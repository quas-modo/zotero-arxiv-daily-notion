"""Test figure extraction and embedding in outputs"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.html_extractor import HTMLExtractor
from src.utils.pdf_extractor import PDFTextExtractor
from src.integrations.notion_client import NotionClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_html_figure_extraction():
    """Test HTML figure extraction with a sample ArXiv paper"""
    print("\n" + "="*80)
    print("TEST: HTML Figure Extraction")
    print("="*80 + "\n")

    # Use a real ArXiv paper with HTML version
    # Example: "2402.08954" - a recent robotics paper
    arxiv_id = "2601.16163"

    extractor = HTMLExtractor(max_figures=3)
    html_url = extractor.generate_html_url(arxiv_id)

    print(f"Testing with ArXiv ID: {arxiv_id}")
    print(f"HTML URL: {html_url}\n")

    # Check if HTML is available
    html_available = extractor.check_html_available(html_url)
    print(f"HTML Available: {html_available}\n")

    if not html_available:
        print("⚠️  HTML not available for this paper, skipping test")
        return

    # Extract multimodal content
    paper = {
        'arxiv_id': arxiv_id,
        'html_url': html_url
    }

    result = extractor.extract_multimodal_content(paper, download_images=False)  # Use URLs only

    print(f"Extraction Method: {result['extraction_method']}")
    print(f"HTML Available: {result['html_available']}")
    print(f"Introduction Length: {len(result['introduction'])} chars")
    print(f"Methodology Length: {len(result['methodology'])} chars")
    print(f"Conclusion Length: {len(result['conclusion'])} chars")
    print(f"Number of Figures: {result['num_figures']}\n")

    # Print figure details
    if result['figures']:
        print("Extracted Figures:")
        print("-" * 80)
        for fig in result['figures']:
            print(f"\n  Figure {fig.get('figure_number', '?')}:")
            print(f"    Caption: {fig.get('caption', 'No caption')[:100]}...")
            print(f"    Image URL: {fig.get('image_url', 'N/A')}")
            print(f"    Has Image Data: {bool(fig.get('image_data'))}")
    else:
        print("⚠️  No figures extracted")

    print("\n✓ HTML figure extraction test complete\n")
    return result


def test_pdf_figure_extraction():
    """Test PDF figure extraction with a sample ArXiv paper"""
    print("\n" + "="*80)
    print("TEST: PDF Figure Extraction")
    print("="*80 + "\n")

    # Use a real ArXiv paper
    arxiv_id = "2601.16163"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    print(f"Testing with ArXiv ID: {arxiv_id}")
    print(f"PDF URL: {pdf_url}\n")

    # Extract multimodal content
    paper = {
        'arxiv_id': arxiv_id,
        'pdf_url': pdf_url
    }

    result = PDFTextExtractor.extract_multimodal_content(
        paper,
        extract_figures=True,
        max_figures=3
    )

    print(f"Introduction Length: {len(result.get('introduction', '')) if result.get('introduction') else 0} chars")
    print(f"Full Text Length: {len(result.get('full_text', '')) if result.get('full_text') else 0} chars")
    print(f"Number of Figures: {result['num_figures']}\n")

    # Print figure details
    if result['figures']:
        print("Extracted Figures:")
        print("-" * 80)
        for fig in result['figures']:
            print(f"\n  Figure {fig.get('figure_number', '?')}:")
            print(f"    Caption: {fig.get('caption', 'No caption')[:100]}...")
            print(f"    Page: {fig.get('page_num', '?')}")
            print(f"    Format: {fig.get('image_format', 'unknown')}")
            print(f"    Size: {fig.get('size_bytes', 0)} bytes")
            if fig.get('image_data'):
                print(f"    Image Data Length: {len(fig['image_data'])} chars")
    else:
        print("⚠️  No figures extracted")

    print("\n✓ PDF figure extraction test complete\n")
    return result


def test_figure_data_structure():
    """Test that figure data structure is consistent"""
    print("\n" + "="*80)
    print("TEST: Figure Data Structure Validation")
    print("="*80 + "\n")

    # Required fields for figures
    required_fields = ['figure_number', 'caption']
    optional_fields = ['image_data', 'image_url', 'image_format', 'page_num', 'sequential_index']

    print(f"Required Fields: {required_fields}")
    print(f"Optional Fields: {optional_fields}\n")

    # Test with HTML extraction
    html_result = test_html_figure_extraction()
    if html_result and html_result.get('figures'):
        print("\nValidating HTML figure structure:")
        for i, fig in enumerate(html_result['figures'], 1):
            missing_required = [f for f in required_fields if f not in fig]
            if missing_required:
                print(f"  ✗ Figure {i} missing required fields: {missing_required}")
            else:
                print(f"  ✓ Figure {i} has all required fields")

    # Test with PDF extraction
    pdf_result = test_pdf_figure_extraction()
    if pdf_result and pdf_result.get('figures'):
        print("\nValidating PDF figure structure:")
        for i, fig in enumerate(pdf_result['figures'], 1):
            missing_required = [f for f in required_fields if f not in fig]
            if missing_required:
                print(f"  ✗ Figure {i} missing required fields: {missing_required}")
            else:
                print(f"  ✓ Figure {i} has all required fields")

    print("\n✓ Figure data structure validation complete\n")


def test_notion_figure_insertion():
    """Test that figures are correctly inserted into Notion pages"""
    print("\n" + "="*80)
    print("TEST: Notion Figure Insertion")
    print("="*80 + "\n")

    # Step 1: Extract figures from a real paper
    arxiv_id = "2601.16163"
    extractor = HTMLExtractor(max_figures=10)
    html_url = extractor.generate_html_url(arxiv_id)

    print(f"Step 1: Extracting figures from ArXiv ID: {arxiv_id}")
    print(f"HTML URL: {html_url}\n")

    # Check if HTML is available
    html_available = extractor.check_html_available(html_url)
    if not html_available:
        print("⚠️  HTML not available for this paper, trying PDF extraction...")
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        paper_for_extraction = {'arxiv_id': arxiv_id, 'pdf_url': pdf_url}
        result = PDFTextExtractor.extract_multimodal_content(
            paper_for_extraction, extract_figures=True, max_figures=3
        )
    else:
        paper_for_extraction = {'arxiv_id': arxiv_id, 'html_url': html_url}
        result = extractor.extract_multimodal_content(paper_for_extraction, download_images=False)

    figures = result.get('figures', [])
    print(f"Extracted {len(figures)} figures\n")

    if not figures:
        print("⚠️  No figures extracted, cannot test Notion insertion")
        return None

    # Step 2: Build a test paper object with figures
    print("Step 2: Building test paper object...")
    test_paper = {
        'title': f'[TEST] Figure Insertion Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        'authors': ['Test Author 1', 'Test Author 2'],
        'abstract': 'This is a test paper to verify that figures are correctly inserted into Notion pages.',
        'arxiv_id': arxiv_id,
        'pdf_url': f'https://arxiv.org/pdf/{arxiv_id}.pdf',
        'entry_url': f'https://arxiv.org/abs/{arxiv_id}',
        'html_url': html_url,
        'categories': ['cs.AI', 'cs.RO'],
        'published_date': datetime.now().strftime('%Y-%m-%d'),
        
        # Analysis fields
        'summary': 'This is a test summary for figure insertion verification.',
        'summary_zh': '这是一个测试摘要，用于验证图片插入功能。',
        'abstract_zh': '这是一个测试论文，用于验证图片是否正确插入到 Notion 页面中。',
        'detailed_analysis': '',
        'detailed_analysis_zh': '',
        
        # Figures from extraction
        'figures': figures,
        'num_figures_analyzed': len(figures),
        'extraction_method': result.get('extraction_method', 'html'),
        'html_available': html_available
    }

    # Print figure details
    print(f"\nFigures to be inserted:")
    for i, fig in enumerate(figures, 1):
        print(f"  Figure {i}:")
        print(f"    Number: {fig.get('figure_number', '?')}")
        print(f"    Caption: {fig.get('caption', 'No caption')[:80]}...")
        print(f"    Image URL: {fig.get('image_url', 'N/A')}")

    # Step 3: Create Notion entry
    print("\n" + "-"*40)
    print("Step 3: Creating Notion entry with figures...")

    try:
        notion_client = NotionClient()
        response = notion_client.create_paper_entry(test_paper)

        page_id = response.get('id', 'unknown')
        page_url = response.get('url', 'unknown')

        print(f"\n✓ Notion page created successfully!")
        print(f"  Page ID: {page_id}")
        print(f"  Page URL: {page_url}")
        print(f"\n📌 Please verify the figures manually at the URL above.")

        return {
            'success': True,
            'page_id': page_id,
            'page_url': page_url,
            'num_figures': len(figures)
        }

    except ValueError as e:
        print(f"\n⚠️  Notion not configured: {str(e)}")
        print("   Set NOTION_API_KEY and NOTION_DATABASE_ID environment variables to test.")
        return {'success': False, 'error': str(e)}

    except Exception as e:
        print(f"\n✗ Failed to create Notion entry: {str(e)}")
        logger.error(f"Notion insertion failed: {str(e)}")
        return {'success': False, 'error': str(e)}


def test_notion_figure_with_custom_paper():
    """Test Notion figure insertion with custom/mock figures"""
    print("\n" + "="*80)
    print("TEST: Notion Figure Insertion with Custom Data")
    print("="*80 + "\n")

    # Create a test paper with mock figures (using valid external URLs)
    test_paper = {
        'title': f'[TEST] Custom Figure Test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        'authors': ['Test Author'],
        'abstract': 'Testing figure insertion with custom mock data.',
        'arxiv_id': 'test.00000',
        'pdf_url': 'https://arxiv.org/pdf/2401.00001.pdf',
        'entry_url': 'https://arxiv.org/abs/2401.00001',
        'categories': ['cs.AI'],
        'published_date': datetime.now().strftime('%Y-%m-%d'),
        
        # Analysis fields
        'summary': 'Test summary for custom figure test.',
        'summary_zh': '自定义图片测试的摘要。',
        'abstract_zh': '使用自定义模拟数据测试图片插入。',
        
        # Custom mock figures with valid external image URLs
        'figures': [
            {
                'figure_number': '1',
                'caption': 'Test Figure 1: This is a sample architecture diagram showing the model overview.',
                'image_url': 'https://ar5iv.labs.arxiv.org/html/2401.00001/assets/figures/overview.png'
            },
            {
                'figure_number': '2', 
                'caption': 'Test Figure 2: Results comparison across different benchmarks.',
                'image_url': 'https://ar5iv.labs.arxiv.org/html/2401.00001/assets/figures/results.png'
            }
        ],
        'num_figures_analyzed': 2,
        'extraction_method': 'mock',
        'html_available': False
    }

    print(f"Test paper: {test_paper['title']}")
    print(f"Number of mock figures: {len(test_paper['figures'])}\n")

    try:
        notion_client = NotionClient()
        response = notion_client.create_paper_entry(test_paper)

        page_id = response.get('id', 'unknown')
        page_url = response.get('url', 'unknown')

        print(f"✓ Notion page created!")
        print(f"  Page URL: {page_url}")
        print(f"\n📌 Note: Mock figure URLs may not display actual images.")
        print(f"   This test verifies the block structure is correct.")

        return {'success': True, 'page_id': page_id, 'page_url': page_url}

    except ValueError as e:
        print(f"⚠️  Notion not configured: {str(e)}")
        return {'success': False, 'error': str(e)}

    except Exception as e:
        print(f"✗ Failed: {str(e)}")
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Test figure extraction and Notion insertion')
    parser.add_argument('--html', action='store_true', help='Test HTML extraction only')
    parser.add_argument('--pdf', action='store_true', help='Test PDF extraction only')
    parser.add_argument('--notion', action='store_true', help='Test Notion figure insertion (requires NOTION_API_KEY)')
    parser.add_argument('--notion-mock', action='store_true', help='Test Notion insertion with mock figures')
    parser.add_argument('--all', action='store_true', help='Run all extraction tests (default, excludes Notion)')

    args = parser.parse_args()

    try:
        if args.html:
            test_html_figure_extraction()
        elif args.pdf:
            test_pdf_figure_extraction()
        elif args.notion:
            test_notion_figure_insertion()
        elif args.notion_mock:
            test_notion_figure_with_custom_paper()
        else:
            # Run extraction tests by default (not Notion)
            test_figure_data_structure()

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n✗ Test failed: {str(e)}")
