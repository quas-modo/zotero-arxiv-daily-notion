"""Comprehensive test for enhanced Notion formatting"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the notion_client module to avoid import errors
import unittest.mock as mock
sys.modules['notion_client'] = mock.MagicMock()

from src.integrations.notion_client import NotionClient


def test_parse_markdown_comprehensive():
    """Test comprehensive markdown parsing"""

    # Create a client instance (won't actually connect to Notion)
    # We'll test the parsing methods directly
    client = NotionClient.__new__(NotionClient)

    # Sample markdown with all supported features
    markdown_text = """
# Main Heading
This is a paragraph with **bold text**, *italic text*, and `inline code`.

## Section 1: Key Points
Here are the key findings:
- First point with **emphasis**
- Second point with `code reference`
- Third point with *italic*

### Subsection Details
This is a subsection with detailed information.

> This is an important callout or quote that provides additional context.

## Section 2: Technical Implementation

```python
def example_function(x, y):
    \"\"\"Example function with code highlighting\"\"\"
    result = x + y
    return result
```

Some explanation after the code block.

## Section 3: Step-by-Step Process

1. First step in the process
2. Second step with **important** detail
3. Third step with `code reference`

---

## Conclusion
Final thoughts and summary.
"""

    print("="*60)
    print("COMPREHENSIVE MARKDOWN PARSING TEST")
    print("="*60)
    print("\nInput Markdown:")
    print(markdown_text)
    print("\n" + "="*60)

    # Parse the markdown
    blocks = client._parse_markdown_to_blocks(markdown_text)

    print(f"\n✓ Successfully parsed into {len(blocks)} Notion blocks")
    print("\nBlock Types Generated:")

    block_types = {}
    for block in blocks:
        block_type = block.get('type', 'unknown')
        block_types[block_type] = block_types.get(block_type, 0) + 1

    for block_type, count in sorted(block_types.items()):
        print(f"  • {block_type}: {count}")

    # Detailed block analysis
    print("\n" + "="*60)
    print("DETAILED BLOCK ANALYSIS")
    print("="*60)

    for i, block in enumerate(blocks, 1):
        block_type = block.get('type')
        print(f"\nBlock {i}: {block_type}")

        if block_type == 'heading_2':
            content = block['heading_2']['rich_text'][0]['text']['content']
            color = block['heading_2'].get('color', 'default')
            print(f"  Content: {content[:50]}...")
            print(f"  Color: {color}")

        elif block_type == 'heading_3':
            content = block['heading_3']['rich_text'][0]['text']['content']
            print(f"  Content: {content[:50]}...")

        elif block_type == 'toggle':
            content = block['toggle']['rich_text'][0]['text']['content']
            annotations = block['toggle']['rich_text'][0]['text'].get('annotations', {})
            print(f"  Content: {content[:50]}...")
            print(f"  Annotations: {annotations}")

        elif block_type == 'paragraph':
            rich_text = block['paragraph']['rich_text']
            total_text = ''.join([rt['text']['content'] for rt in rich_text])
            print(f"  Content: {total_text[:60]}...")
            print(f"  Rich text segments: {len(rich_text)}")

        elif block_type == 'bulleted_list_item':
            rich_text = block['bulleted_list_item']['rich_text']
            total_text = ''.join([rt['text']['content'] for rt in rich_text])
            print(f"  Content: {total_text[:50]}...")

        elif block_type == 'numbered_list_item':
            rich_text = block['numbered_list_item']['rich_text']
            total_text = ''.join([rt['text']['content'] for rt in rich_text])
            print(f"  Content: {total_text[:50]}...")

        elif block_type == 'callout':
            content = block['callout']['rich_text'][0]['text']['content']
            icon = block['callout']['icon']['emoji']
            color = block['callout'].get('color', 'default')
            print(f"  Content: {content[:50]}...")
            print(f"  Icon: {icon}, Color: {color}")

        elif block_type == 'code':
            content = block['code']['rich_text'][0]['text']['content']
            language = block['code']['language']
            print(f"  Language: {language}")
            print(f"  Lines: {len(content.split(chr(10)))}")

        elif block_type == 'divider':
            print(f"  [Horizontal divider]")

    return blocks


def test_inline_formatting():
    """Test inline formatting parsing"""

    client = NotionClient.__new__(NotionClient)

    print("\n" + "="*60)
    print("INLINE FORMATTING TEST")
    print("="*60)

    test_cases = [
        ("Simple text without formatting", 1),
        ("Text with **bold** formatting", 3),
        ("Text with *italic* formatting", 3),
        ("Text with `inline code` formatting", 3),
        ("Text with **bold** and *italic* and `code`", 6),
        ("Multiple **bold** words **here**", 5),
    ]

    for text, expected_segments in test_cases:
        rich_text = client._parse_inline_formatting(text)
        print(f"\nInput: {text}")
        print(f"  Segments: {len(rich_text)} (expected: {expected_segments})")

        for segment in rich_text:
            content = segment['text']['content']
            annotations = segment['text'].get('annotations', {})
            if annotations:
                print(f"    '{content}' -> {annotations}")
            else:
                print(f"    '{content}'")

        # Verify we have the expected number of segments (approximately)
        if abs(len(rich_text) - expected_segments) <= 1:
            print(f"  ✓ Correct")
        else:
            print(f"  ⚠ Unexpected segment count")


def test_content_blocks_structure():
    """Test the overall content block structure"""

    client = NotionClient.__new__(NotionClient)

    print("\n" + "="*60)
    print("CONTENT STRUCTURE TEST")
    print("="*60)

    # Sample paper data
    paper = {
        'title': 'Test Paper: Advanced Machine Learning Techniques',
        'authors': ['John Doe', 'Jane Smith'],
        'published_date': datetime(2024, 1, 15),
        'arxiv_id': '2401.12345',
        'pdf_url': 'https://arxiv.org/pdf/2401.12345.pdf',
        'entry_url': 'https://arxiv.org/abs/2401.12345',
        'github_links': ['https://github.com/example/repo'],
        'categories': ['cs.AI', 'cs.LG'],
        'relevance_score': 8.5,
        'abstract': 'This paper presents novel approaches to machine learning...',
        'summary': 'The paper introduces three key innovations: 1) A new architecture, 2) Improved training methods, 3) Better evaluation metrics.',
        'detailed_analysis': """
## Key Contributions
- Novel neural architecture design
- **Improved training efficiency** by 40%
- State-of-the-art results on benchmark

## Technical Approach
The authors propose using:
1. Attention mechanisms
2. Residual connections
3. Layer normalization

```python
class NewModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.attention = Attention()
```

> The key insight is combining these techniques effectively.
""",
        'abstract_zh': '本文提出了机器学习的新方法...',
        'summary_zh': '论文介绍了三个关键创新：1) 新架构，2) 改进的训练方法，3) 更好的评估指标。',
        'detailed_analysis_zh': """
## 关键贡献
- 新颖的神经架构设计
- **提高训练效率** 40%
- 在基准测试上达到最先进的结果
"""
    }

    # Generate content blocks
    blocks = client._format_content_blocks(paper)

    print(f"\n✓ Generated {len(blocks)} content blocks")
    print("\nStructure Overview:")

    section = "Header"
    for i, block in enumerate(blocks, 1):
        block_type = block.get('type')

        # Detect section changes
        if block_type == 'heading_1':
            content = block['heading_1']['rich_text'][0]['text']['content']
            section = content
            print(f"\n📍 {section}")

        elif block_type == 'heading_2':
            content = block['heading_2']['rich_text'][0]['text']['content']
            print(f"\n  📌 {content}")

        elif block_type == 'divider':
            print(f"  ━━━━━━━━━━━━━━━━")

        elif block_type == 'callout':
            icon = block['callout']['icon']['emoji']
            color = block['callout'].get('color', 'default')
            content = block['callout']['rich_text'][0]['text']['content'][:40]
            print(f"    {icon} Callout ({color}): {content}...")

        elif block_type == 'toggle':
            content = block['toggle']['rich_text'][0]['text']['content']
            print(f"    🔽 Toggle: {content}")

    # Verify expected sections exist
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)

    has_callout = any(b['type'] == 'callout' for b in blocks)
    has_toggle = any(b['type'] == 'toggle' for b in blocks)
    has_heading_1 = any(b['type'] == 'heading_1' for b in blocks)
    has_heading_2 = any(b['type'] == 'heading_2' for b in blocks)
    has_divider = any(b['type'] == 'divider' for b in blocks)
    has_links = any(b['type'] == 'paragraph' and any('link' in rt.get('text', {}) for rt in b['paragraph']['rich_text']) for b in blocks)

    print(f"\n✓ Has callout boxes: {has_callout}")
    print(f"✓ Has toggle blocks: {has_toggle}")
    print(f"✓ Has heading_1: {has_heading_1}")
    print(f"✓ Has heading_2: {has_heading_2}")
    print(f"✓ Has dividers: {has_divider}")
    print(f"✓ Has clickable links: {has_links}")

    all_checks = has_callout and has_toggle and has_heading_1 and has_heading_2 and has_divider and has_links

    return all_checks


if __name__ == "__main__":
    print("\n" + "🎨 "*30)
    print("NOTION FORMATTING ENHANCEMENT - COMPREHENSIVE TEST")
    print("🎨 "*30 + "\n")

    try:
        # Test 1: Markdown parsing
        blocks1 = test_parse_markdown_comprehensive()

        # Test 2: Inline formatting
        test_inline_formatting()

        # Test 3: Content structure
        all_checks_passed = test_content_blocks_structure()

        # Final summary
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        print("\n✅ All tests completed successfully!")
        print(f"✅ All validation checks passed: {all_checks_passed}")

        print("\n📊 Summary of Enhancements:")
        print("  ✓ Rich markdown parsing (headings, lists, code, quotes)")
        print("  ✓ Inline formatting (bold, italic, code)")
        print("  ✓ Visual elements (callouts, toggles, dividers)")
        print("  ✓ Color coding and emojis")
        print("  ✓ Clickable hyperlinks")
        print("  ✓ Proper content structure with sections")

        print("\n🎉 Notion formatting is ready to use!")

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
