"""
Test script for HTML extraction feature

Tests the new HTML extraction functionality with sample papers.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.html_extractor import HTMLExtractor
from src.utils.content_extractor import ContentExtractor
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_html_extractor():
    """Test HTMLExtractor with a known paper that has HTML version"""
    print("\n" + "="*80)
    print("Testing HTML Extractor")
    print("="*80 + "\n")

    extractor = HTMLExtractor(timeout=15, max_figures=3)

    # Test paper: ArXiv's HTML announcement paper (known to have HTML)
    test_papers = [
        {
            'arxiv_id': '2402.08954',
            'title': 'Test Paper 1 (Recent paper with HTML)',
            'html_url': 'https://arxiv.org/html/2402.08954'
        },
        {
            'arxiv_id': '2401.12345',  # May or may not exist
            'title': 'Test Paper 2 (Testing fallback)',
            'html_url': 'https://arxiv.org/html/2401.12345'
        }
    ]

    for paper in test_papers:
        print(f"\n📄 Testing: {paper['title']}")
        print(f"ArXiv ID: {paper['arxiv_id']}")
        print(f"HTML URL: {paper['html_url']}")
        print("-" * 80)

        # Check availability
        available = extractor.check_html_available(paper['html_url'])
        print(f"HTML Available: {available}")

        if available:
            # Extract content
            result = extractor.extract_multimodal_content(paper, download_images=False)

            print(f"\nExtraction Results:")
            print(f"  - Introduction: {len(result['introduction'])} chars")
            print(f"  - Methodology: {len(result['methodology'])} chars")
            print(f"  - Conclusion: {len(result['conclusion'])} chars")
            print(f"  - Figures: {len(result['figures'])}")

            if result['introduction']:
                print(f"\nIntroduction Preview (first 200 chars):")
                print(result['introduction'][:200] + "...")

            if result['methodology']:
                print(f"\nMethodology Preview (first 200 chars):")
                print(result['methodology'][:200] + "...")

            if result['figures']:
                print(f"\nFigures:")
                for fig in result['figures']:
                    print(f"  - Figure {fig['figure_number']}: {fig['caption'][:100]}")
        else:
            print("  HTML not available - would fall back to PDF")

        print()


def test_content_extractor():
    """Test ContentExtractor with HTML-first, PDF-fallback logic"""
    print("\n" + "="*80)
    print("Testing Content Extractor (HTML-first with PDF fallback)")
    print("="*80 + "\n")

    # Load config
    config = load_config()
    extractor = ContentExtractor(config=config)

    # Test paper with both HTML and PDF
    test_paper = {
        'arxiv_id': '2402.08954',
        'title': 'Test Paper with HTML',
        'html_url': 'https://arxiv.org/html/2402.08954',
        'pdf_url': 'https://arxiv.org/pdf/2402.08954.pdf'
    }

    print(f"📄 Testing: {test_paper['title']}")
    print(f"ArXiv ID: {test_paper['arxiv_id']}")
    print("-" * 80)

    result = extractor.extract_multimodal_content(test_paper)

    print(f"\nExtraction Method: {result['extraction_method'].upper()}")
    print(f"HTML Available: {result['html_available']}")
    print(f"\nContent:")
    print(f"  - Introduction: {len(result['introduction'])} chars")
    print(f"  - Methodology: {len(result['methodology'])} chars")
    print(f"  - Conclusion: {len(result['conclusion'])} chars")
    print(f"  - Figures: {len(result['figures'])}")
    print(f"  - Full Text: {len(result['full_text'])} chars")

    if result['extraction_method'] == 'html':
        print("\n✅ SUCCESS: HTML extraction worked!")
    else:
        print(f"\n⚠️  Fell back to PDF extraction (reason: HTML not available or extraction failed)")


def test_url_generation():
    """Test HTML URL generation"""
    print("\n" + "="*80)
    print("Testing HTML URL Generation")
    print("="*80 + "\n")

    test_ids = [
        '2402.08954',
        '2401.12345v1',
        '2301.00001v2'
    ]

    for arxiv_id in test_ids:
        html_url = HTMLExtractor.generate_html_url(arxiv_id)
        print(f"ArXiv ID: {arxiv_id:20s} -> HTML URL: {html_url}")


if __name__ == "__main__":
    print("\n🧪 HTML Extraction Feature Test Suite")
    print("=" * 80)

    try:
        # Test 1: URL generation
        test_url_generation()

        # Test 2: HTML extractor
        test_html_extractor()

        # Test 3: Content extractor orchestrator
        test_content_extractor()

        print("\n" + "="*80)
        print("✅ All tests completed!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
