"""
Test script for HTML extraction feature

Tests the new HTML extraction functionality with sample papers.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.html_extractor import HTMLExtractor
from src.utils.content_extractor import ContentExtractor
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_html_extractor():
    """Test HTMLExtractor with a known paper that has HTML version"""
    print("\n" + "=" * 80)
    print("Testing HTML Extractor")
    print("=" * 80 + "\n")

    # Load config to get proper timeout settings
    config = load_config()
    html_config = config.get("html_extraction", {})
    timeout = html_config.get("timeout", 30)
    max_figures = html_config.get("max_figures", 3)
    retry_config = html_config.get("retry", {})
    pool_config = html_config.get("connection_pool", {})

    extractor = HTMLExtractor(
        timeout=timeout,
        max_figures=max_figures,
        retry_config=retry_config,
        pool_config=pool_config,
    )

    # Test paper: ArXiv's HTML announcement paper (known to have HTML)
    test_papers = [
        {
            "arxiv_id": "2601.21998",
            "title": "Causal World Modeling for Robot Control",
            "html_url": "https://arxiv.org/html/2601.21998",
        },
        {
            "arxiv_id": "2601.16163",
            "title": "Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning",
            "html_url": "https://arxiv.org/html/2601.16163",
        },
    ]

    for paper in test_papers:
        print(f"\n📄 Testing: {paper['title']}")
        print(f"ArXiv ID: {paper['arxiv_id']}")
        print(f"HTML URL: {paper['html_url']}")
        print("-" * 80)

        # Check availability
        available = extractor.check_html_available(paper["html_url"])
        print(f"HTML Available: {available}")

        if available:
            # Extract content
            result = extractor.extract_multimodal_content(paper, download_images=False)

            print(f"\nExtraction Results:")
            print(f"  - Introduction: {len(result['introduction'])} chars")
            print(f"  - Methodology: {len(result['methodology'])} chars")
            print(f"  - Conclusion: {len(result['conclusion'])} chars")
            print(f"  - Figures: {len(result['figures'])}")

            if result["introduction"]:
                print(f"\nIntroduction Preview (first 200 chars):")
                print(result["introduction"][:200] + "...")

            if result["methodology"]:
                print(f"\nMethodology Preview (first 200 chars):")
                print(result["methodology"][:200] + "...")

            if result["figures"]:
                print(f"\nFigures:")
                for fig in result["figures"]:
                    print(f"  - Figure {fig['figure_number']}: {fig['caption'][:100]}")
        else:
            print("  HTML not available - would fall back to PDF")

        print()


def test_extract_sections():
    """Test the new extract_sections functionality that extracts all sections"""
    print("\n" + "=" * 80)
    print("Testing Extract Sections (All Sections)")
    print("=" * 80 + "\n")

    # Load config
    config = load_config()
    html_config = config.get("html_extraction", {})
    timeout = html_config.get("timeout", 30)
    retry_config = html_config.get("retry", {})
    pool_config = html_config.get("connection_pool", {})

    extractor = HTMLExtractor(
        timeout=timeout,
        max_figures=3,
        retry_config=retry_config,
        pool_config=pool_config,
    )

    # Test papers list
    test_papers = [
        {
            "arxiv_id": "2601.16163",
            "title": "Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning",
            "html_url": "https://arxiv.org/html/2601.16163",
        },
        {
            "arxiv_id": "2601.21998",
            "title": "Causal World Modeling for Robot Control",
            "html_url": "https://arxiv.org/html/2601.21998",
        },
        {
            "arxiv_id": "2501.12368",
            "title": "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs",
            "html_url": "https://arxiv.org/html/2501.12368",
        },
        {
            "arxiv_id": "2501.09751",
            "title": "Kimi k1.5: Scaling Reinforcement Learning with LLMs",
            "html_url": "https://arxiv.org/html/2501.09751",
        },
    ]

    for paper_idx, test_paper in enumerate(test_papers, 1):
        print(f"\n{'='*80}")
        print(f"📄 [{paper_idx}/{len(test_papers)}] Testing: {test_paper['title']}")
        print(f"ArXiv ID: {test_paper['arxiv_id']}")
        print("-" * 80)

        # Check availability and download HTML
        available = extractor.check_html_available(test_paper["html_url"])
        if not available:
            print("❌ HTML not available for this paper, skipping...")
            continue

        # Download HTML content directly
        html_content = extractor._download_html(test_paper["html_url"])
        if not html_content:
            print("❌ Failed to download HTML content, skipping...")
            continue

        # Test extract_sections
        print("\n🔍 Testing extract_sections()...")
        sections_result = extractor.extract_sections(html_content)

        # Check returned keys
        print("\n📋 Returned Keys:")
        for key in sections_result.keys():
            print(f"  - {key}")

        # Check special sections (backward compatibility)
        print("\n📌 Special Sections (Backward Compatible):")
        for section_name in ["introduction", "methodology", "conclusion"]:
            content = sections_result.get(section_name, "")
            status = "✅" if content else "⚠️ (empty)"
            print(f"  - {section_name}: {len(content)} chars {status}")

        # Check all_sections
        all_sections = sections_result.get("all_sections", {})
        section_order = sections_result.get("section_order", [])

        print(f"\n📚 All Sections Extracted: {len(all_sections)} sections")
        print(f"📝 Section Order: {len(section_order)} items")

        if section_order:
            print("\n📖 Sections in Document Order:")
            for idx, section_name in enumerate(section_order, 1):
                content = all_sections.get(section_name, "")
                preview = (
                    content[:80].replace("\n", " ") + "..."
                    if len(content) > 80
                    else content.replace("\n", " ")
                )
                print(f"  {idx}. {section_name}: {len(content)} chars")
                print(f"      Preview: {preview}")

        # Verify section_order matches all_sections keys
        all_sections_keys = set(all_sections.keys())
        section_order_set = set(section_order)

        if all_sections_keys == section_order_set:
            print("\n✅ section_order matches all_sections keys")
        else:
            print("\n⚠️ Mismatch between section_order and all_sections keys")
            print(
                f"   In all_sections but not in order: {all_sections_keys - section_order_set}"
            )
            print(
                f"   In order but not in all_sections: {section_order_set - all_sections_keys}"
            )

    print("\n" + "=" * 80)
    print("✅ extract_sections test completed!")
    print("=" * 80)


def test_content_extractor():
    """Test ContentExtractor with HTML-first, PDF-fallback logic"""
    print("\n" + "=" * 80)
    print("Testing Content Extractor (HTML-first with PDF fallback)")
    print("=" * 80 + "\n")

    # Load config
    config = load_config()
    extractor = ContentExtractor(config=config)

    # Test paper with both HTML and PDF
    test_paper = {
        "arxiv_id": "2601.16163",
        "title": "Cosmos Policy: Fine-Tuning Video Models for Visuomotor Control and Planning",
        "html_url": "https://arxiv.org/html/2601.16163",
    }

    print(f"📄 Testing: {test_paper['title']}")
    print(f"ArXiv ID: {test_paper['arxiv_id']}")
    print("-" * 80)

    result = extractor.extract_multimodal_content(test_paper)

    print(f"\nExtraction Method: {result['extraction_method'].upper()}")
    print(f"HTML Available: {result['html_available']}")
    print(f"\nSpecial Sections:")
    print(f"  - Introduction: {len(result['introduction'])} chars")
    print(f"  - Methodology: {len(result['methodology'])} chars")
    print(f"  - Conclusion: {len(result['conclusion'])} chars")
    print(f"  - Figures: {len(result['figures'])}")

    # Check all_sections if available
    all_sections = result.get("all_sections", {})
    section_order = result.get("section_order", [])
    if all_sections:
        print(f"\nAll Sections: {len(all_sections)} sections extracted")
        for section_name in section_order[:5]:  # Show first 5 sections
            print(f"  - {section_name}: {len(all_sections[section_name])} chars")
        if len(section_order) > 5:
            print(f"  ... and {len(section_order) - 5} more sections")

    if result["extraction_method"] == "html":
        print("\n✅ SUCCESS: HTML extraction worked!")
    else:
        print(
            f"\n⚠️  Fell back to PDF extraction (reason: HTML not available or extraction failed)"
        )


def test_url_generation():
    """Test HTML URL generation"""
    print("\n" + "=" * 80)
    print("Testing HTML URL Generation")
    print("=" * 80 + "\n")

    test_ids = ["2402.08954", "2401.12345v1", "2301.00001v2"]

    for arxiv_id in test_ids:
        html_url = HTMLExtractor.generate_html_url(arxiv_id)
        print(f"ArXiv ID: {arxiv_id:20s} -> HTML URL: {html_url}")


if __name__ == "__main__":
    print("\n🧪 HTML Extraction Feature Test Suite")
    print("=" * 80)

    try:
        # Test 1: URL generation
        test_url_generation()

        # Test 2: HTML extractor (basic)
        test_html_extractor()

        # Test 3: Extract sections (new functionality)
        test_extract_sections()

        # Test 4: Content extractor orchestrator
        test_content_extractor()

        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
