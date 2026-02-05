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
        pool_config: Dict = None,
        download_images: bool = False,
        use_full_text: bool = True,
    ):
        """
        Initialize HTML extractor with enhanced timeout and retry support.

        Args:
            timeout: Timeout configuration (int for simple, dict for granular)
            max_figures: Maximum number of figures to extract
            retry_config: Retry configuration dict
            pool_config: Connection pool configuration dict
            download_images: Whether to download images (default: False, use URLs only)
        """
        self.max_figures = max_figures
        self.download_images = download_images
        self.use_full_text = use_full_text

        # Parse timeout configuration (backward compatible)
        self.timeouts = self._parse_timeout_config(timeout)

        # Set up retry strategy
        retry_config = retry_config or {
            "enabled": True,
            "max_retries": 3,
            "backoff_factor": 1.0,
            "retry_on_status": [500, 502, 503, 504, 429],
            "retry_on_timeout": True,
        }
        self.retry_strategy = self._create_retry_strategy(retry_config)

        # Create session with optimized connection pooling
        pool_config = pool_config or {
            "pool_connections": 10,
            "pool_maxsize": 20,
            "pool_block": False,
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
                "head": timeout_config,
                "get_html": timeout_config,
                "get_image": timeout_config,
                "connect": timeout_config // 2,
            }
        else:
            # New format: granular timeouts
            return {
                "head": timeout_config.get("head_request", 20),
                "get_html": timeout_config.get("get_html", 30),
                "get_image": timeout_config.get("get_image", 25),
                "connect": timeout_config.get("connect", 10),
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

        if not retry_config or not retry_config.get("enabled", True):
            return None

        return Retry(
            total=retry_config.get("max_retries", 3),
            backoff_factor=retry_config.get("backoff_factor", 1.0),
            status_forcelist=retry_config.get("retry_on_status", [500, 502, 503, 504]),
            allowed_methods=["HEAD", "GET"],
            raise_on_status=False,
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
            pool_connections=pool_config.get("pool_connections", 10),
            pool_maxsize=pool_config.get("pool_maxsize", 20),
            pool_block=pool_config.get("pool_block", False),
        )

        # Mount for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set user agent
        session.headers.update(
            {"User-Agent": "Mozilla/5.0 (compatible; ResearchAssistant/1.0)"}
        )

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
        clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
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
            timeout = (self.timeouts["connect"], self.timeouts["head"])

            response = self.session.head(
                html_url, timeout=timeout, allow_redirects=True
            )

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
            timeout = (self.timeouts["connect"], self.timeouts["get_html"])

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
                f"Failed to download HTML from {html_url} " f"after {elapsed:.2f}s: {e}"
            )
            return None

    def _find_section_by_header(
        self, soup: BeautifulSoup, patterns: List[str]
    ) -> Optional[str]:
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
            for header in soup.find_all(["h2", "h3", "h4"]):
                header_text = header.get_text(strip=True)
                if regex.match(header_text):
                    logger.debug(f"Found section header: {header_text}")

                    # Get parent section or article
                    section = header.find_parent(["section", "article", "div"])
                    if not section:
                        continue

                    # Extract all paragraphs in this section
                    paragraphs = []
                    for p in section.find_all("p", recursive=True):
                        # Skip if paragraph is in a nested section with different header
                        parent_section = p.find_parent("section")
                        if parent_section and parent_section != section:
                            # Check if nested section has its own header
                            nested_header = parent_section.find(["h2", "h3", "h4"])
                            if nested_header and nested_header != header:
                                continue

                        text = p.get_text(strip=True)
                        if text:
                            paragraphs.append(text)

                    if paragraphs:
                        content = "\n\n".join(paragraphs)
                        logger.info(
                            f"Extracted section content: {len(content)} chars, {len(paragraphs)} paragraphs"
                        )
                        return content

        return None

    def _normalize_section_name(self, header_text: str) -> str:
        """
        Normalize section header to a clean field name.

        Args:
            header_text: Raw header text (e.g., "2.1 Related Work")

        Returns:
            Normalized name (e.g., "related_work")
        """
        # Remove leading numbers and dots (e.g., "2.1 ", "3. ", "2.1", "1Introduction")
        # The \s* at the end handles both "2.1 Intro" and "2.1Intro" cases
        cleaned = re.sub(r"^\s*[\d\.]+\s*", "", header_text)

        # Remove leading roman numerals ONLY if followed by a dot or colon and space
        # This prevents "Introduction" from becoming "ntroduction"
        # Matches: "I. ", "II. ", "III. ", "IV. ", "I: ", etc.
        cleaned = re.sub(r"^\s*[IVXivx]+[\.:\s]\s*", "", cleaned)

        # Convert to lowercase and replace spaces/special chars with underscores
        normalized = cleaned.lower().strip()
        normalized = re.sub(r"[^\w\s]", "", normalized)  # Remove special characters
        normalized = re.sub(r"\s+", "_", normalized)  # Replace spaces with underscores

        return normalized

    def _is_special_section(self, normalized_name: str) -> Optional[str]:
        """
        Check if a normalized section name maps to a special section.
        Uses partial matching to handle cases like "1introduction" -> "introduction".

        Args:
            normalized_name: Normalized section name

        Returns:
            Special section key ('introduction', 'methodology', 'conclusion') or None
        """
        # Map various section names to our three special sections
        # Using keywords for partial matching
        introduction_keywords = ["introduction", "intro"]
        methodology_keywords = [
            "methodology",
            "method",
            "approach",
            "proposed_method",
            "technical_approach",
            "our_method",
            "our_approach",
            "framework",
        ]
        conclusion_keywords = [
            "conclusion",
            "discussion",
            "concluding_remarks",
            "summary",
        ]

        # Check introduction (partial match)
        for keyword in introduction_keywords:
            if keyword in normalized_name:
                return "introduction"

        # Check methodology (partial match)
        for keyword in methodology_keywords:
            if keyword in normalized_name:
                return "methodology"

        # Check conclusion (partial match)
        for keyword in conclusion_keywords:
            if keyword in normalized_name:
                return "conclusion"

        return None

    def _extract_section_content(self, section_element, header_element) -> str:
        """
        Extract text content from a section element.

        Args:
            section_element: BeautifulSoup section element
            header_element: The header element of this section

        Returns:
            Extracted text content
        """
        paragraphs = []

        for p in section_element.find_all("p", recursive=True):
            # Skip if paragraph is in a nested section with different header
            parent_section = p.find_parent("section")
            if parent_section and parent_section != section_element:
                # Check if nested section has its own header
                nested_header = parent_section.find(["h2", "h3", "h4"])
                if nested_header and nested_header != header_element:
                    continue

            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs) if paragraphs else ""

    def extract_all_sections(self, html_content: str) -> Dict[str, any]:
        """
        Extract all sections from HTML with their content.

        Args:
            html_content: Raw HTML string

        Returns:
            Dict with keys:
                - all_sections: Dict mapping section names to content
                - section_order: List of section names in document order
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            all_sections = {}
            section_order = []

            # Find all section headers (h2, h3, h4)
            for header in soup.find_all(["h2", "h3", "h4"]):
                header_text = header.get_text(strip=True)
                if not header_text:
                    continue

                # Skip headers that are likely not main sections
                # (e.g., figure captions, table headers)
                if header.find_parent("figure") or header.find_parent("table"):
                    continue

                # Get parent section
                section = header.find_parent(["section", "article", "div"])
                if not section:
                    continue

                # Normalize the section name
                normalized_name = self._normalize_section_name(header_text)
                if not normalized_name:
                    continue

                # Extract content
                content = self._extract_section_content(section, header)

                if content:
                    # Handle duplicate section names by appending suffix
                    original_name = normalized_name
                    counter = 1
                    while normalized_name in all_sections:
                        counter += 1
                        normalized_name = f"{original_name}_{counter}"

                    all_sections[normalized_name] = content
                    section_order.append(normalized_name)

                    logger.debug(
                        f"Extracted section '{normalized_name}' "
                        f"(original: '{header_text}'): {len(content)} chars"
                    )

            logger.info(f"Extracted {len(all_sections)} sections from HTML")
            return {"all_sections": all_sections, "section_order": section_order}

        except Exception as e:
            logger.error(f"Failed to extract all sections from HTML: {e}")
            return {"all_sections": {}, "section_order": []}

    def extract_sections(self, html_content: str) -> Dict[str, any]:
        """
        Extract all sections from HTML, with special handling for
        introduction, methodology, and conclusion (backward compatible).

        Args:
            html_content: Raw HTML string

        Returns:
            Dict with keys:
                - introduction, methodology, conclusion (for backward compatibility)
                - all_sections: Dict with all section names as keys
                - section_order: List of section names in document order
        """
        try:
            # First, extract all sections
            all_sections_result = self.extract_all_sections(html_content)
            all_sections = all_sections_result["all_sections"]
            section_order = all_sections_result["section_order"]

            # Initialize special sections
            special_sections = {"introduction": "", "methodology": "", "conclusion": ""}

            # Map extracted sections to special sections
            for section_name, content in all_sections.items():
                special_key = self._is_special_section(section_name)
                if special_key and not special_sections[special_key]:
                    # Only use the first matching section for each special key
                    special_sections[special_key] = content
                    logger.info(f"Mapped section '{section_name}' to '{special_key}'")

            # If methodology not found, try to find it with broader patterns
            if not special_sections["methodology"]:
                soup = BeautifulSoup(html_content, "html.parser")
                methodology_patterns = [
                    r"^\s*\d*\.?\s*Methodology\s*$",
                    r"^\s*\d*\.?\s*Method(s)?\s*$",
                    r"^\s*\d*\.?\s*Approach\s*$",
                    r"^\s*\d*\.?\s*Proposed\s+Method\s*$",
                    r"^\s*\d*\.?\s*Technical\s+Approach\s*$",
                    r"^\s*\d*\.?\s*Our\s+Method\s*$",
                    r"^\s*\d*\.?\s*Framework\s*$",
                    r"^\s*\d*\.?\s*Model\s*$",
                ]
                content = self._find_section_by_header(soup, methodology_patterns)
                if content:
                    special_sections["methodology"] = content
                    logger.info("Found methodology section via pattern matching")

            # Log extraction results
            for section_name in ["introduction", "methodology", "conclusion"]:
                if special_sections[section_name]:
                    logger.info(f"Successfully extracted {section_name} section")
                else:
                    logger.warning(f"Could not find {section_name} section")

            # Combine results
            result = {
                **special_sections,
                "all_sections": all_sections,
                "section_order": section_order,
            }

            return result

        except Exception as e:
            logger.error(f"Failed to extract sections from HTML: {e}")
            return {
                "introduction": "",
                "methodology": "",
                "conclusion": "",
                "all_sections": {},
                "section_order": [],
            }

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
            timeout = (self.timeouts["connect"], self.timeouts["get_image"])

            response = self.session.get(img_url, timeout=timeout)
            response.raise_for_status()

            elapsed = time.time() - start_time

            # Convert to base64
            img_base64 = base64.b64encode(response.content).decode("utf-8")

            # Detect image type from content-type header
            content_type = response.headers.get("content-type", "image/png")
            media_type = content_type.split("/")[-1]

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
                f"Failed to download image from {img_url} " f"after {elapsed:.2f}s: {e}"
            )
            return None

    def extract_figures(
        self, html_content: str, arxiv_id: str = None, download_images: bool = None
    ) -> List[Dict]:
        """
        Extract figures with captions from HTML.

        Args:
            html_content: Raw HTML string
            arxiv_id: ArXiv paper ID (e.g., "2402.08954") for constructing image URLs
            download_images: Whether to download images as base64 (default: use instance setting)

        Returns:
            List of figure dicts with keys: image_url, caption, figure_number
        """
        # Use instance setting if not specified
        if download_images is None:
            download_images = self.download_images
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            figures = []

            # Find all figure elements
            figure_elements = soup.find_all("figure", class_="ltx_figure")
            logger.info(f"Found {len(figure_elements)} figure elements in HTML")

            # Clean arxiv_id (remove version suffix if present)
            if arxiv_id:
                clean_id = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
            else:
                clean_id = None

            for idx, figure in enumerate(figure_elements[: self.max_figures], 1):
                try:
                    # Extract image
                    img_tag = figure.find("img")
                    if not img_tag or not img_tag.get("src"):
                        logger.warning(f"Figure {idx} missing image tag or src")
                        continue

                    img_src = img_tag.get("src")

                    # Make absolute URL using ArXiv HTML format: https://arxiv.org/html/{arxiv_id}/{image_filename}
                    if img_src.startswith("http"):
                        # Already absolute URL
                        img_url = img_src
                    elif clean_id:
                        # Extract filename from path (handle both /path/to/file.png and path/to/file.png)
                        img_filename = img_src.lstrip("/")
                        img_url = f"https://arxiv.org/html/{clean_id}/{img_filename}"
                    elif img_src.startswith("/"):
                        # Fallback: use old format if no arxiv_id provided
                        img_url = f"https://arxiv.org{img_src}"
                    else:
                        # Fallback: use old format if no arxiv_id provided
                        img_url = f"https://arxiv.org/{img_src}"

                    # Extract caption
                    caption_tag = figure.find("figcaption", class_="ltx_caption")
                    caption = ""
                    original_figure_number = None

                    if caption_tag:
                        caption_text = caption_tag.get_text(strip=True)

                        # Try to extract original figure number (e.g., "Figure 2.1:", "Figure 3:")
                        fig_num_match = re.match(
                            r"^Figure\s+([\d\.]+)[:.]\s*",
                            caption_text,
                            flags=re.IGNORECASE,
                        )
                        if fig_num_match:
                            original_figure_number = fig_num_match.group(1)

                        # Remove "Figure X:" prefix from caption
                        caption = re.sub(
                            r"^Figure\s+[\d\.]+[:.]\s*",
                            "",
                            caption_text,
                            flags=re.IGNORECASE,
                        )

                    # Optionally download image if requested (not recommended)
                    image_data = None
                    if download_images:
                        image_data = self._download_image(img_url)
                        if not image_data:
                            logger.warning(
                                f"Failed to download image for figure {idx}, using URL only"
                            )

                    # Use original figure number if found, otherwise use sequential index
                    figure_number = (
                        original_figure_number if original_figure_number else str(idx)
                    )

                    figures.append(
                        {
                            "image_url": img_url,
                            "image_data": image_data,  # None unless download_images=True
                            "caption": caption,
                            "figure_number": figure_number,
                            "sequential_index": idx,  # Keep track of extraction order
                        }
                    )

                    logger.info(f"Extracted figure {idx}: {len(caption)} chars caption")

                except Exception as e:
                    logger.warning(f"Failed to process figure {idx}: {e}")
                    continue

            logger.info(f"Successfully extracted {len(figures)} figures from HTML")
            return figures

        except Exception as e:
            logger.error(f"Failed to extract figures from HTML: {e}")
            return []

    def extract_multimodal_content(
        self, paper: Dict, download_images: bool = None, use_full_text: bool = None
    ) -> Dict:
        """
        Main entry point: Extract all content from ArXiv HTML paper.

        Args:
            paper: Paper dict containing 'arxiv_id' and 'html_url'
            download_images: Whether to download images as base64 (default: use instance setting)

        Returns:
            Dict with keys: extraction_method, html_available, introduction,
                          methodology, conclusion, figures, num_figures,
                          all_sections, section_order
        """
        # Use instance setting if not specified
        if download_images is None:
            download_images = self.download_images
        if use_full_text is None:
            use_full_text = self.use_full_text
        arxiv_id = paper.get("arxiv_id", "")
        html_url = paper.get("html_url", "")

        if not html_url:
            html_url = self.generate_html_url(arxiv_id)

        logger.info(f"Starting HTML extraction for {arxiv_id}")

        # Check if HTML available
        if not self.check_html_available(html_url):
            logger.info(f"HTML not available for {arxiv_id}")
            return {
                "extraction_method": "html",
                "html_available": False,
                "introduction": "",
                "methodology": "",
                "conclusion": "",
                "figures": [],
                "num_figures": 0,
                "all_sections": {},
                "section_order": [],
            }

        # Download HTML
        html_content = self._download_html(html_url)
        if not html_content:
            logger.error(f"Failed to download HTML for {arxiv_id}")
            return {
                "extraction_method": "html",
                "html_available": False,
                "introduction": "",
                "methodology": "",
                "conclusion": "",
                "figures": [],
                "num_figures": 0,
                "all_sections": {},
                "section_order": [],
            }

        # Extract sections (includes all_sections and special sections)
        sections = self.extract_sections(html_content)

        # Extract figures
        figures = self.extract_figures(
            html_content, arxiv_id=arxiv_id, download_images=download_images
        )

        # Get all sections data
        all_sections = sections.get("all_sections", {})
        section_order = sections.get("section_order", [])

        result = {
            "extraction_method": "html",
            "html_available": True,
            "introduction": sections["introduction"],
            "methodology": sections["methodology"],
            "conclusion": sections["conclusion"],
            "figures": figures,
            "num_figures": len(figures),
            "all_sections": all_sections,
            "section_order": section_order,
        }

        logger.info(
            f"HTML extraction complete for {arxiv_id}: "
            f"{len(sections['introduction'])} chars intro, "
            f"{len(sections['methodology'])} chars method, "
            f"{len(sections['conclusion'])} chars conclusion, "
            f"{len(all_sections)} total sections, "
            f"{len(figures)} figures"
        )

        return result
