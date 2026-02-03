"""
Simple offline test for HTML extraction parsing logic

Tests the HTML parsing functionality without requiring network access.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.html_extractor import HTMLExtractor

# Sample ArXiv HTML structure (simplified)
SAMPLE_HTML = """
<html>
<head><title>Test Paper</title></head>
<body>
    <article>
        <section class="ltx_section">
            <h2 class="ltx_title">1 Introduction</h2>
            <p>This is the introduction paragraph one. It discusses the motivation and background of the research.</p>
            <p>This is the second paragraph of the introduction. It outlines the main contributions.</p>
        </section>

        <section class="ltx_section">
            <h2 class="ltx_title">2 Methodology</h2>
            <p>This section describes our proposed approach. We use a novel neural architecture.</p>
            <p>The methodology involves three main steps as illustrated in Figure 1.</p>
        </section>

        <section class="ltx_section">
            <h2 class="ltx_title">3 Experiments</h2>
            <p>We conducted experiments on three benchmark datasets.</p>
        </section>

        <section class="ltx_section">
            <h2 class="ltx_title">4 Conclusion</h2>
            <p>In conclusion, our method achieves state-of-the-art results on all benchmarks.</p>
            <p>Future work will explore extensions to multi-modal settings.</p>
        </section>

        <figure class="ltx_figure">
            <img src="/html/2401.12345v1/extracted/fig1.png" alt="Figure 1"/>
            <figcaption class="ltx_caption">
                <span class="ltx_tag">Figure 1:</span> System architecture showing the three main components.
            </figcaption>
        </figure>

        <figure class="ltx_figure">
            <img src="/html/2401.12345v1/extracted/fig2.png" alt="Figure 2"/>
            <figcaption class="ltx_caption">
                <span class="ltx_tag">Figure 2:</span> Experimental results on benchmark datasets.
            </figcaption>
        </figure>
    </article>
</body>
</html>
"""


def test_section_extraction():
    """Test extracting sections from HTML"""
    print("\n" + "="*80)
    print("Testing Section Extraction (Offline)")
    print("="*80 + "\n")

    extractor = HTMLExtractor()

    sections = extractor.extract_sections(SAMPLE_HTML)

    print("Extracted Sections:")
    print("-" * 80)

    for section_name, content in sections.items():
        print(f"\n{section_name.upper()}:")
        print(f"  Length: {len(content)} chars")
        if content:
            print(f"  Preview: {content[:150]}...")
        else:
            print("  ❌ Not found")

    # Verify results
    assert sections['introduction'], "Introduction should be extracted"
    assert sections['methodology'], "Methodology should be extracted"
    assert sections['conclusion'], "Conclusion should be extracted"

    print("\n✅ Section extraction test PASSED")


def test_figure_extraction():
    """Test extracting figures from HTML"""
    print("\n" + "="*80)
    print("Testing Figure Extraction (Offline)")
    print("="*80 + "\n")

    extractor = HTMLExtractor()

    # Extract without downloading images
    figures = extractor.extract_figures(SAMPLE_HTML, download_images=False)

    print(f"Extracted {len(figures)} figures:")
    print("-" * 80)

    for fig in figures:
        print(f"\nFigure {fig['figure_number']}:")
        print(f"  Image URL: {fig['image_url']}")
        print(f"  Caption: {fig['caption']}")

    # Verify results
    assert len(figures) == 2, f"Should extract 2 figures, got {len(figures)}"
    assert figures[0]['caption'], "First figure should have a caption"

    print("\n✅ Figure extraction test PASSED")


def test_url_generation():
    """Test HTML URL generation"""
    print("\n" + "="*80)
    print("Testing URL Generation")
    print("="*80 + "\n")

    test_cases = [
        ('2402.08954', 'https://arxiv.org/html/2402.08954'),
        ('2401.12345v1', 'https://arxiv.org/html/2401.12345'),
        ('2301.00001v2', 'https://arxiv.org/html/2301.00001'),
    ]

    for arxiv_id, expected_url in test_cases:
        result = HTMLExtractor.generate_html_url(arxiv_id)
        print(f"ArXiv ID: {arxiv_id:20s} -> {result}")
        assert result == expected_url, f"URL mismatch for {arxiv_id}"

    print("\n✅ URL generation test PASSED")


if __name__ == "__main__":
    print("\n🧪 HTML Extraction Offline Test Suite")
    print("=" * 80)
    print("Testing HTML parsing logic without network access")
    print("=" * 80)

    try:
        test_url_generation()
        test_section_extraction()
        test_figure_extraction()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED!")
        print("="*80 + "\n")

        print("Next steps:")
        print("  1. Test with real ArXiv papers (requires network access)")
        print("  2. Run end-to-end test with main.py")
        print("  3. Verify Notion integration displays HTML links")

    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
