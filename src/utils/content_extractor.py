"""
Content Extractor Orchestrator

Unified interface for extracting content from papers using HTML-first with PDF fallback.
"""

import logging
from typing import Dict
from .html_extractor import HTMLExtractor
from .pdf_extractor import PDFTextExtractor

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Orchestrates content extraction with HTML-first, PDF-fallback strategy.
    """

    def __init__(self, config: Dict = None):
        """
        Initialize content extractor.

        Args:
            config: Configuration dict with html_extraction settings
        """
        self.config = config or {}

        # Get HTML extraction settings
        html_config = self.config.get('html_extraction', {})
        self.html_enabled = html_config.get('enabled', True)
        self.prefer_html = html_config.get('prefer_html', True)
        self.download_images = html_config.get('download_images', True)
        self.timeout = html_config.get('timeout', 15)
        self.max_figures = html_config.get('max_figures', 3)

        # Initialize extractors
        self.html_extractor = HTMLExtractor(
            timeout=self.timeout,
            max_figures=self.max_figures
        )

    def extract_multimodal_content(self, paper: Dict) -> Dict:
        """
        Extract content from paper using HTML-first, PDF-fallback strategy.

        Args:
            paper: Paper dict with arxiv_id, html_url, pdf_url

        Returns:
            Unified content dict with keys:
                - extraction_method: 'html' or 'pdf'
                - html_available: bool
                - introduction: str
                - methodology: str (empty for PDF)
                - conclusion: str (empty for PDF)
                - figures: List[Dict]
                - num_figures: int
                - full_text: str
        """
        arxiv_id = paper.get('arxiv_id', 'unknown')

        # Try HTML extraction first if enabled and preferred
        if self.html_enabled and self.prefer_html:
            logger.info(f"Attempting HTML extraction for {arxiv_id}")

            try:
                html_result = self.html_extractor.extract_multimodal_content(
                    paper,
                    download_images=self.download_images
                )

                # Check if HTML extraction was successful
                if html_result.get('html_available', False):
                    # Verify we got at least introduction
                    if html_result.get('introduction'):
                        logger.info(f"HTML extraction successful for {arxiv_id}")
                        return html_result
                    else:
                        logger.warning(f"HTML available but no introduction extracted for {arxiv_id}, falling back to PDF")
                else:
                    logger.info(f"HTML not available for {arxiv_id}, falling back to PDF")

            except Exception as e:
                logger.error(f"HTML extraction failed for {arxiv_id}: {e}, falling back to PDF")

        # Fall back to PDF extraction
        logger.info(f"Using PDF extraction for {arxiv_id}")
        return self._extract_from_pdf(paper)

    def _extract_from_pdf(self, paper: Dict) -> Dict:
        """
        Extract content from PDF with unified output structure.

        Args:
            paper: Paper dict with pdf_url

        Returns:
            Content dict matching HTML output structure
        """
        try:
            pdf_result = PDFTextExtractor.extract_multimodal_content(
                paper,
                extract_figures=True,
                max_figures=self.max_figures
            )

            # Transform PDF result to match unified structure
            result = {
                'extraction_method': 'pdf',
                'html_available': False,
                'introduction': pdf_result.get('introduction') or "",
                'methodology': "",  # PDF doesn't extract methodology separately
                'conclusion': "",   # PDF doesn't extract conclusion separately
                'figures': pdf_result.get('figures', []),
                'num_figures': pdf_result.get('num_figures', 0),
                'full_text': pdf_result.get('full_text') or ""
            }

            logger.info(f"PDF extraction complete: "
                       f"{len(result['introduction'])} chars intro, "
                       f"{len(result['figures'])} figures")

            return result

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            # Return empty result on failure
            return {
                'extraction_method': 'pdf',
                'html_available': False,
                'introduction': "",
                'methodology': "",
                'conclusion': "",
                'figures': [],
                'num_figures': 0,
                'full_text': ""
            }

    @staticmethod
    def generate_html_url(arxiv_id: str) -> str:
        """
        Generate ArXiv HTML URL from paper ID.

        Args:
            arxiv_id: ArXiv paper ID

        Returns:
            HTML URL string
        """
        return HTMLExtractor.generate_html_url(arxiv_id)
