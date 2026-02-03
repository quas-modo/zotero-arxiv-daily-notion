"""
ArXiv HTML Extractor Module

Extracts structured content (sections, figures) from ArXiv HTML papers.
ArXiv uses LaTeXML format with specific HTML structure.
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Union
import base64
from io import BytesIO
import time

logger = logging.getLogger(__name__)


class HTMLExtractor:
    """Extract structured content from ArXiv HTML papers."""

    def __init__(
        self,
        timeout: Union[int, Dict] = 30,
        max_figures: int = 3,
        retry_config: Dict = None,
        pool_config: Dict = None
    ):
        """
        Initialize HTML extractor with enhanced timeout and retry support.

        Args:
            timeout: Timeout configuration (int for simple, dict for granular)
            max_figures: Maximum number of figures to extract
            retry_config: Retry configuration dict
            pool_config: Connection pool configuration dict
        """
        self.max_figures = max_figures

        # Parse timeout configuration (backward compatible)
        self.timeouts = self._parse_timeout_config(timeout)

        # Set up retry strategy
        retry_config = retry_config or {
            'enabled': True,
            'max_retries': 3,
            'backoff_factor': 1.0,
            'retry_on_status': [500, 502, 503, 504, 429],
            'retry_on_timeout': True
        }
        self.retry_strategy = self._create_retry_strategy(retry_config)

        # Create session with optimized connection pooling
        pool_config = pool_config or {
            'pool_connections': 10,
            'pool_maxsize': 20,
            'pool_block': False
        }
        self.session = self._create_optimized_session(self.retry_strategy, pool_config)

    def _parse_timeout_config(self, timeout_config: Union[int, Dict]) -> Dict[str, int]:
        """
        Parse timeout configuration (backward compatible).
        Supports both old format (int) and new format (dict).

        Args:
            timeout_config: Integer timeout or dict with granular timeouts

        Returns:
            Dict with timeout values for different operations
        """
        if isinstance(timeout_config, int):
            # Old format: single timeout value
            return {
                'head': timeout_config,
                'get_html': timeout_config,
                'get_image': timeout_config,
                'connect': timeout_config // 2
            }
        else:
            # New format: granular timeouts
            return {
                'head': timeout_config.get('head_request', 20),
                'get_html': timeout_config.get('get_html', 30),
                'get_image': timeout_config.get('get_image', 25),
                'connect': timeout_config.get('connect', 10)
            }

    def _create_retry_strategy(self, retry_config: Dict):
        """
        Create urllib3 Retry strategy for automatic retries.

        Args:
            retry_config: Configuration dict with retry settings

        Returns:
            Retry object or None if disabled
        """
        from urllib3.util.retry import Retry

        if not retry_config or not retry_config.get('enabled', True):
            return None

        return Retry(
            total=retry_config.get('max_retries', 3),
            backoff_factor=retry_config.get('backoff_factor', 1.0),
            status_forcelist=retry_config.get('retry_on_status', [500, 502, 503, 504]),
            allowed_methods=['HEAD', 'GET'],
            raise_on_status=False
        )

    def _create_optimized_session(self, retry_strategy, pool_config: Dict):
        """
        Create requests session with connection pooling and retry logic.

        Args:
            retry_strategy: Retry strategy object
            pool_config: Pool configuration dict

        Returns:
            Configured requests Session
        """
        from requests.adapters import HTTPAdapter

        session = requests.Session()

        # Configure adapter with retry and pool settings
        adapter = HTTPAdapter(
            max_retries=retry_strategy if retry_strategy else 0,
            pool_connections=pool_config.get('pool_connections', 10),
            pool_maxsize=pool_config.get('pool_maxsize', 20),
            pool_block=pool_config.get('pool_block', False)
        )

        # Mount for both HTTP and HTTPS
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # Set user agent
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ResearchAssistant/1.0)'
        })

        return session

    @staticmethod
    def generate_html_url(arxiv_id: str) -> str:
        """
        Generate ArXiv HTML URL from paper ID.

        Args:
            arxiv_id: ArXiv paper ID (e.g., "2401.12345" or "2401.12345v1")

        Returns:
            HTML URL string
        """
        # Remove version suffix if present
        clean_id = arxiv_id.split('v')[0] if 'v' in arxiv_id else arxiv_id
        return f"https://arxiv.org/html/{clean_id}"

    def check_html_available(self, html_url: str) -> bool:
        """
        Check if HTML version is available for the paper (with retry logic).

        Args:
            html_url: ArXiv HTML URL to check

        Returns:
            True if HTML available, False otherwise
        """
        start_time = time.time()

        try:
            # Use granular timeout: (connect_timeout, read_timeout)
            timeout = (self.timeouts['connect'], self.timeouts['head'])

            response = self.session.head(html_url, timeout=timeout, allow_redirects=True)

            elapsed = time.time() - start_time
            available = response.status_code == 200

            logger.info(
                f"HTML availability check for {html_url}: {available} "
                f"(status: {response.status_code}, elapsed: {elapsed:.2f}s)"
            )

            return available

        except requests.Timeout as e:
            elapsed = time.time() - start_time
            logger.warning(
                f"HTML availability check timed out for {html_url} "
                f"after {elapsed:.2f}s: {e}"
            )
            return False

        except requests.RequestException as e:
            elapsed = time.time() - start_time
            logger.warning(
                f"Failed to check HTML availability for {html_url} "
                f"after {elapsed:.2f}s: {e}"
            )
            return False

    def _download_html(self, html_url: str) -> Optional[str]:
        """
        Download HTML content with retry and proper timeout.

        Args:
            html_url: ArXiv HTML URL

        Returns:
            HTML content string or None if failed
        """
        start_time = time.time()

        try:
            timeout = (self.timeouts['connect'], self.timeouts['get_html'])

            response = self.session.get(html_url, timeout=timeout)
            response.raise_for_status()

            elapsed = time.time() - start_time
            logger.info(
                f"Successfully downloaded HTML from {html_url} "
                f"({len(response.text)} chars, {elapsed:.2f}s)"
            )

            return response.text

        except requests.Timeout as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Timeout downloading HTML from {html_url} "
                f"after {elapsed:.2f}s: {e}"
            )
            return None

        except requests.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Failed to download HTML from {html_url} "
                f"after {elapsed:.2f}s: {e}"
            )
            return None

    def _find_section_by_header(self, soup: BeautifulSoup, patterns: List[str]) -> Optional[str]:
        """
        Find section content by matching header patterns.

        Args:
            soup: BeautifulSoup parsed HTML
            patterns: List of regex patterns to match section headers

        Returns:
            Section content as string or None if not found
        """
        # Try to find section with matching header
        for pattern in patterns:
            regex = re.compile(pattern, re.IGNORECASE)

            # Search in h2 headers (main sections)
            for header in soup.find_all(['h2', 'h3', 'h4']):
                header_text = header.get_text(strip=True)
                if regex.match(header_text):
                    logger.debug(f"Found section header: {header_text}")

                    # Get parent section or article
                    section = header.find_parent(['section', 'article', 'div'])
                    if not section:
                        continue

                    # Extract all paragraphs in this section
                    paragraphs = []
                    for p in section.find_all('p', recursive=True):
                        # Skip if paragraph is in a nested section with different header
                        parent_section = p.find_parent('section')
                        if parent_section and parent_section != section:
                            # Check if nested section has its own header
                            nested_header = parent_section.find(['h2', 'h3', 'h4'])
                            if nested_header and nested_header != header:
                                continue

                        text = p.get_text(strip=True)
                        if text:
                            paragraphs.append(text)

                    if paragraphs:
                        content = '\n\n'.join(paragraphs)
                        logger.info(f"Extracted section content: {len(content)} chars, {len(paragraphs)} paragraphs")
                        return content

        return None

    def extract_sections(self, html_content: str) -> Dict[str, str]:
        """
        Extract Introduction, Methodology, and Conclusion sections from HTML.

        Args:
            html_content: Raw HTML string

        Returns:
            Dict with keys: introduction, methodology, conclusion
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Define section patterns (multiple alternatives per section)
            section_patterns = {
                'introduction': [
                    r'^\s*\d*\.?\s*Introduction\s*$',
                    r'^\s*\d+\.\s*Introduction\s*$',
                    r'^\s*I+\.?\s*Introduction\s*$',  # Roman numerals
                ],
                'methodology': [
                    r'^\s*\d*\.?\s*Methodology\s*$',
                    r'^\s*\d*\.?\s*Method(s)?\s*$',
                    r'^\s*\d*\.?\s*Approach\s*$',
                    r'^\s*\d*\.?\s*Proposed\s+Method\s*$',
                    r'^\s*\d*\.?\s*Technical\s+Approach\s*$',
                ],
                'conclusion': [
                    r'^\s*\d*\.?\s*Conclusion(s)?\s*$',
                    r'^\s*\d*\.?\s*Discussion\s*$',
                    r'^\s*\d*\.?\s*Conclusion\s+and\s+Discussion\s*$',
                    r'^\s*\d*\.?\s*Discussion\s+and\s+Conclusion\s*$',
                ]
            }

            sections = {}
            for section_name, patterns in section_patterns.items():
                content = self._find_section_by_header(soup, patterns)
                sections[section_name] = content if content else ""

                if content:
                    logger.info(f"Successfully extracted {section_name} section")
                else:
                    logger.warning(f"Could not find {section_name} section")

            return sections

        except Exception as e:
            logger.error(f"Failed to extract sections from HTML: {e}")
            return {'introduction': "", 'methodology': "", 'conclusion': ""}

    def _download_image(self, img_url: str) -> Optional[str]:
        """
        Download image with retry and proper timeout.

        Args:
            img_url: Image URL

        Returns:
            Base64 encoded image string or None if failed
        """
        start_time = time.time()

        try:
            timeout = (self.timeouts['connect'], self.timeouts['get_image'])

            response = self.session.get(img_url, timeout=timeout)
            response.raise_for_status()

            elapsed = time.time() - start_time

            # Convert to base64
            img_base64 = base64.b64encode(response.content).decode('utf-8')

            # Detect image type from content-type header
            content_type = response.headers.get('content-type', 'image/png')
            media_type = content_type.split('/')[-1]

            logger.debug(
                f"Downloaded image: {len(response.content)} bytes, "
                f"type: {media_type}, elapsed: {elapsed:.2f}s"
            )

            return f"data:image/{media_type};base64,{img_base64}"

        except requests.Timeout as e:
            elapsed = time.time() - start_time
            logger.warning(
                f"Timeout downloading image from {img_url} "
                f"after {elapsed:.2f}s: {e}"
            )
            return None

        except requests.RequestException as e:
            elapsed = time.time() - start_time
            logger.warning(
                f"Failed to download image from {img_url} "
                f"after {elapsed:.2f}s: {e}"
            )
            return None

    def extract_figures(self, html_content: str, download_images: bool = True) -> List[Dict]:
        """
        Extract figures with captions from HTML.

        Args:
            html_content: Raw HTML string
            download_images: Whether to download images as base64

        Returns:
            List of figure dicts with keys: image_data, caption, figure_number
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            figures = []

            # Find all figure elements
            figure_elements = soup.find_all('figure', class_='ltx_figure')
            logger.info(f"Found {len(figure_elements)} figure elements in HTML")

            for idx, figure in enumerate(figure_elements[:self.max_figures], 1):
                try:
                    # Extract image
                    img_tag = figure.find('img')
                    if not img_tag or not img_tag.get('src'):
                        logger.warning(f"Figure {idx} missing image tag or src")
                        continue

                    img_src = img_tag.get('src')

                    # Make absolute URL if relative
                    if img_src.startswith('/'):
                        img_url = f"https://arxiv.org{img_src}"
                    elif not img_src.startswith('http'):
                        img_url = f"https://arxiv.org/{img_src}"
                    else:
                        img_url = img_src

                    # Extract caption
                    caption_tag = figure.find('figcaption', class_='ltx_caption')
                    caption = ""
                    if caption_tag:
                        # Remove "Figure X:" prefix if present
                        caption_text = caption_tag.get_text(strip=True)
                        caption = re.sub(r'^Figure\s+\d+[:.]\s*', '', caption_text, flags=re.IGNORECASE)

                    # Download image if requested
                    image_data = None
                    if download_images:
                        image_data = self._download_image(img_url)
                        if not image_data:
                            logger.warning(f"Failed to download image for figure {idx}, skipping")
                            continue

                    figures.append({
                        'image_data': image_data,
                        'image_url': img_url,
                        'caption': caption,
                        'figure_number': idx
                    })

                    logger.info(f"Extracted figure {idx}: {len(caption)} chars caption")

                except Exception as e:
                    logger.warning(f"Failed to process figure {idx}: {e}")
                    continue

            logger.info(f"Successfully extracted {len(figures)} figures from HTML")
            return figures

        except Exception as e:
            logger.error(f"Failed to extract figures from HTML: {e}")
            return []

    def extract_multimodal_content(self, paper: Dict, download_images: bool = True) -> Dict:
        """
        Main entry point: Extract all content from ArXiv HTML paper.

        Args:
            paper: Paper dict containing 'arxiv_id' and 'html_url'
            download_images: Whether to download images as base64

        Returns:
            Dict with keys: extraction_method, html_available, introduction,
                          methodology, conclusion, figures, num_figures, full_text
        """
        arxiv_id = paper.get('arxiv_id', '')
        html_url = paper.get('html_url', '')

        if not html_url:
            html_url = self.generate_html_url(arxiv_id)

        logger.info(f"Starting HTML extraction for {arxiv_id}")

        # Check if HTML available
        if not self.check_html_available(html_url):
            logger.info(f"HTML not available for {arxiv_id}")
            return {
                'extraction_method': 'html',
                'html_available': False,
                'introduction': "",
                'methodology': "",
                'conclusion': "",
                'figures': [],
                'num_figures': 0,
                'full_text': ""
            }

        # Download HTML
        html_content = self._download_html(html_url)
        if not html_content:
            logger.error(f"Failed to download HTML for {arxiv_id}")
            return {
                'extraction_method': 'html',
                'html_available': False,
                'introduction': "",
                'methodology': "",
                'conclusion': "",
                'figures': [],
                'num_figures': 0,
                'full_text': ""
            }

        # Extract sections
        sections = self.extract_sections(html_content)

        # Extract figures
        figures = self.extract_figures(html_content, download_images=download_images)

        # Create full_text for backward compatibility
        full_text_parts = []
        if sections['introduction']:
            full_text_parts.append(f"Introduction:\n{sections['introduction']}")
        if sections['methodology']:
            full_text_parts.append(f"Methodology:\n{sections['methodology']}")
        if sections['conclusion']:
            full_text_parts.append(f"Conclusion:\n{sections['conclusion']}")

        full_text = "\n\n".join(full_text_parts)

        result = {
            'extraction_method': 'html',
            'html_available': True,
            'introduction': sections['introduction'],
            'methodology': sections['methodology'],
            'conclusion': sections['conclusion'],
            'figures': figures,
            'num_figures': len(figures),
            'full_text': full_text
        }

        logger.info(f"HTML extraction complete for {arxiv_id}: "
                   f"{len(sections['introduction'])} chars intro, "
                   f"{len(sections['methodology'])} chars method, "
                   f"{len(sections['conclusion'])} chars conclusion, "
                   f"{len(figures)} figures")

        return result
