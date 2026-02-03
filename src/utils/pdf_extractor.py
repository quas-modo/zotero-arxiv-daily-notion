"""PDF text extraction and multimodal content extraction utilities"""

import re
import io
import base64
import requests
from typing import Optional, Dict, List, Tuple
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFTextExtractor:
    """Extract text sections and visual elements from PDF papers"""

    @staticmethod
    def download_pdf(pdf_url: str, timeout: int = 30) -> Optional[bytes]:
        """Download PDF content from URL"""
        try:
            response = requests.get(pdf_url, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Downloaded PDF from {pdf_url[:50]}...")
            return response.content
        except Exception as e:
            logger.error(f"Failed to download PDF: {str(e)}")
            return None

    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> Optional[str]:
        """Extract full text from PDF bytes"""
        try:
            # Try using PyPDF2
            import PyPDF2
            from io import BytesIO

            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            full_text = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)

            result = "\n".join(full_text)
            logger.info(f"Extracted {len(result)} characters from PDF")
            return result

        except ImportError:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            return None
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None

    @staticmethod
    def extract_full_text_with_pymupdf(pdf_content: bytes) -> Optional[str]:
        """
        Extract full text using PyMuPDF (fitz) for better layout preservation.
        Falls back to PyPDF2 if PyMuPDF not available.
        """
        try:
            import fitz  # PyMuPDF
            from io import BytesIO

            pdf_file = BytesIO(pdf_content)
            doc = fitz.open(stream=pdf_file, filetype="pdf")

            full_text = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text:
                    full_text.append(text)

            doc.close()
            result = "\n".join(full_text)
            logger.info(f"Extracted {len(result)} characters from PDF using PyMuPDF")
            return result

        except ImportError:
            logger.warning("PyMuPDF not installed. Falling back to PyPDF2")
            return PDFTextExtractor.extract_text_from_pdf(pdf_content)
        except Exception as e:
            logger.error(f"Error extracting text with PyMuPDF: {str(e)}")
            return PDFTextExtractor.extract_text_from_pdf(pdf_content)

    @staticmethod
    def extract_figures_from_pdf(pdf_content: bytes, max_figures: int = 5) -> List[Dict]:
        """
        Extract figures/images from PDF with captions.

        Args:
            pdf_content: PDF file bytes
            max_figures: Maximum number of figures to extract

        Returns:
            List of dicts with: {image_data, caption, page_num, figure_num}
        """
        try:
            import fitz  # PyMuPDF
            from io import BytesIO

            pdf_file = BytesIO(pdf_content)
            doc = fitz.open(stream=pdf_file, filetype="pdf")

            figures = []
            figure_count = 0

            # Extract images from each page
            for page_num in range(min(10, len(doc))):  # Check first 10 pages
                page = doc[page_num]
                text = page.get_text()

                # Get images from page
                image_list = page.get_images(full=True)

                for img_index, img_info in enumerate(image_list):
                    if figure_count >= max_figures:
                        break

                    try:
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # Only keep reasonably sized images (likely figures, not icons)
                        if len(image_bytes) < 10000:  # Skip small images
                            continue

                        # Convert to base64 for storage
                        image_b64 = base64.b64encode(image_bytes).decode('utf-8')

                        # Try to find caption near this image
                        caption = PDFTextExtractor._find_figure_caption(text, figure_count + 1)

                        figures.append({
                            'image_data': image_b64,
                            'image_format': image_ext,
                            'caption': caption,
                            'page_num': page_num + 1,
                            'figure_num': figure_count + 1,
                            'size_bytes': len(image_bytes)
                        })

                        figure_count += 1

                    except Exception as e:
                        logger.debug(f"Error extracting image {img_index} from page {page_num}: {str(e)}")
                        continue

                if figure_count >= max_figures:
                    break

            doc.close()
            logger.info(f"Extracted {len(figures)} figures from PDF")
            return figures

        except ImportError:
            logger.warning("PyMuPDF not installed. Cannot extract figures. Install with: pip install pymupdf")
            return []
        except Exception as e:
            logger.error(f"Error extracting figures: {str(e)}")
            return []

    @staticmethod
    def _find_figure_caption(page_text: str, figure_num: int) -> str:
        """
        Find figure caption from page text.

        Args:
            page_text: Full text of the page
            figure_num: Figure number to look for

        Returns:
            Caption text or empty string
        """
        try:
            # Common patterns: "Figure 1:", "Fig. 1:", "Figure 1."
            patterns = [
                rf'(?:Figure|Fig\.?)\s*{figure_num}[:\.]?\s*([^\n]+(?:\n(?!Figure|Fig)[^\n]+)*)',
                rf'(?:Figure|FIG\.?)\s*{figure_num}[:\.]?\s*([^\n]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    caption = match.group(1).strip()
                    # Limit caption length
                    caption = caption[:300]
                    return caption

            return f"Figure {figure_num}"

        except Exception as e:
            logger.debug(f"Error finding caption: {str(e)}")
            return f"Figure {figure_num}"

    @staticmethod
    def extract_introduction(full_text: str) -> Optional[str]:
        """
        Extract Introduction section from full paper text.

        Common patterns:
        - "1 Introduction" or "1. Introduction" or "I. INTRODUCTION"
        - Ends when next section starts (usually "2" or "II")
        """
        if not full_text:
            return None

        try:
            # Common introduction patterns
            intro_patterns = [
                r'(?:^|\n)\s*(?:1\.?|I\.?)\s+Introduction\s*\n(.*?)(?=\n\s*(?:2\.?|II\.?)\s+)',
                r'(?:^|\n)\s*(?:1\.?|I\.?)\s+INTRODUCTION\s*\n(.*?)(?=\n\s*(?:2\.?|II\.?)\s+)',
                r'(?:^|\n)Introduction\s*\n(.*?)(?=\n(?:2|II|Methodology|Method|Approach|Background)\s)',
            ]

            for pattern in intro_patterns:
                match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                if match:
                    intro_text = match.group(1).strip()
                    # Limit to reasonable length (first 3000 characters)
                    intro_text = intro_text[:3000]
                    logger.info(f"Found Introduction section ({len(intro_text)} chars)")
                    return intro_text

            logger.warning("Could not find Introduction section in PDF")
            return None

        except Exception as e:
            logger.error(f"Error parsing Introduction section: {str(e)}")
            return None

    @classmethod
    def get_introduction_from_paper(cls, paper: Dict) -> Optional[str]:
        """
        Download PDF and extract Introduction section.

        Args:
            paper: Paper dictionary with pdf_url

        Returns:
            Introduction text or None
        """
        pdf_url = paper.get('pdf_url')
        if not pdf_url:
            logger.warning("No PDF URL available")
            return None

        # Download PDF
        pdf_content = cls.download_pdf(pdf_url)
        if not pdf_content:
            return None

        # Extract full text
        full_text = cls.extract_text_from_pdf(pdf_content)
        if not full_text:
            return None

        # Extract introduction section
        introduction = cls.extract_introduction(full_text)
        return introduction

    @classmethod
    def extract_multimodal_content(cls, paper: Dict, extract_figures: bool = True, max_figures: int = 3) -> Dict:
        """
        Extract full text and figures from a paper PDF.

        Args:
            paper: Paper dictionary with pdf_url
            extract_figures: Whether to extract figures
            max_figures: Maximum number of figures to extract

        Returns:
            Dict with: {full_text, introduction, figures: [{image_data, caption, page_num}]}
        """
        pdf_url = paper.get('pdf_url')
        if not pdf_url:
            logger.warning("No PDF URL available")
            return {'full_text': None, 'introduction': None, 'figures': []}

        # Download PDF
        pdf_content = cls.download_pdf(pdf_url)
        if not pdf_content:
            return {'full_text': None, 'introduction': None, 'figures': []}

        # Extract full text (using PyMuPDF if available)
        full_text = cls.extract_full_text_with_pymupdf(pdf_content)

        # Extract introduction
        introduction = cls.extract_introduction(full_text) if full_text else None

        # Extract figures
        figures = []
        if extract_figures:
            figures = cls.extract_figures_from_pdf(pdf_content, max_figures=max_figures)

        return {
            'full_text': full_text,
            'introduction': introduction,
            'figures': figures,
            'num_figures': len(figures)
        }
