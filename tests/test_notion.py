"""Test script for Phase 4: Notion Integration"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.notion_client import NotionClient
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_notion_connection():
    """Test Notion API connection and database access"""

    print("\n" + "="*80)
    print("NOTION CONNECTION TEST")
    print("="*80 + "\n")

    # Check environment variables
    api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')

    if not api_key:
        print("❌ NOTION_API_KEY not set in .env file\n")
        print("Please follow these steps:")
        print("  1. Go to https://www.notion.so/my-integrations")
        print("  2. Create a new integration")
        print("  3. Copy the 'Internal Integration Token'")
        print("  4. Add to .env: NOTION_API_KEY=secret_your_token_here\n")
        return False

    if not database_id:
        print("❌ NOTION_DATABASE_ID not set in .env file\n")
        print("Please follow these steps:")
        print("  1. Create a new database in Notion")
        print("  2. Share it with your integration")
        print("  3. Copy the database ID from the URL")
        print("  4. Add to .env: NOTION_DATABASE_ID=your_database_id\n")
        return False

    print(f"✓ API Key: {api_key[:20]}...{api_key[-4:]}")
    print(f"✓ Database ID: {database_id}\n")

    # Try to connect
    try:
        print("Connecting to Notion...")
        client = NotionClient()
        print("✓ Client initialized\n")

        print("Checking database access...")
        if client.check_database_exists():
            print("✓ Database is accessible\n")

            print("Retrieving database properties...")
            props = client.get_database_properties()
            print(f"✓ Database has {len(props)} properties:\n")

            for prop_name, prop_info in props.items():
                print(f"  - {prop_name}: {prop_info.get('type', 'unknown')}")

            return True
        else:
            print("❌ Cannot access database")
            print("\nTroubleshooting:")
            print("  1. Make sure you've shared the database with your integration")
            print("  2. Verify the database ID is correct")
            print("  3. Check that your integration has read/write permissions\n")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False


def test_create_entry():
    """Test creating a Notion entry with sample data"""

    print("\n" + "="*80)
    print("NOTION ENTRY CREATION TEST")
    print("="*80 + "\n")

    # Check if connection test passed
    if not os.getenv('NOTION_API_KEY') or not os.getenv('NOTION_DATABASE_ID'):
        print("⚠️  Skipping entry creation test - credentials not configured")
        return

    try:
        client = NotionClient()

        # Sample paper data
        sample_paper = {
            'title': 'Test Paper: Attention Is All You Need',
            'authors': ['Vaswani', 'Shazeer', 'Parmar', 'Uszkoreit'],
            'published_date': __import__('datetime').datetime(2017, 6, 12),
            'arxiv_id': '1706.03762',
            'abstract': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
            'pdf_url': 'https://arxiv.org/pdf/1706.03762.pdf',
            'entry_url': 'https://arxiv.org/abs/1706.03762',
            'categories': ['CL', 'LG', 'AI'],
            'github_links': ['https://github.com/tensorflow/tensor2tensor'],
            'relevance_score': 0.95,
            'match_details': {
                'primary_matches': ['Transformer', 'Attention'],
                'secondary_matches': ['NLP']
            },
            'summary': '**Core Contribution**: The Transformer is a novel neural network architecture that relies entirely on self-attention mechanisms, eliminating the need for recurrence and convolutions.\n\n**Key Innovation**: Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions.\n\n**Practical Impact**: The Transformer achieves state-of-the-art results on machine translation tasks while being more parallelizable and requiring significantly less time to train than previous architectures.',
            'detailed_analysis': '''## Background & Motivation

Sequence transduction models have traditionally relied on RNNs or CNNs, which process sequences sequentially or with limited receptive fields. This creates bottlenecks in training parallelization and makes it difficult to learn dependencies between distant positions.

## Methodology

The Transformer uses:
- **Self-attention mechanisms** that relate different positions of a single sequence
- **Multi-head attention** for attending to different representation subspaces
- **Position-wise feed-forward networks** applied identically to each position
- **Positional encodings** to inject sequence order information

## Key Findings

- Achieves 28.4 BLEU on WMT 2014 English-to-German translation
- Establishes new state-of-the-art of 41.8 BLEU on English-to-French translation
- Trains in a fraction of the time compared to previous models
- Shows excellent results on English constituency parsing

## Strengths & Limitations

**Strengths:**
- Highly parallelizable architecture
- More effective at capturing long-range dependencies
- Reduced training time

**Limitations:**
- Requires careful tuning of hyperparameters
- May struggle with very long sequences due to quadratic memory complexity

## Practical Applications

- Machine translation
- Text summarization
- Question answering
- Language modeling
- Many other NLP tasks

## Related Work

Builds on attention mechanisms from previous work while eliminating recurrence entirely. Has inspired numerous follow-up works including BERT, GPT, and other transformer-based models.'''
        }

        print("Creating test entry in Notion...")
        print(f"Paper: {sample_paper['title']}\n")

        result = client.create_paper_entry(sample_paper)

        print("\n✅ SUCCESS! Entry created in Notion")
        print(f"Page ID: {result['id']}")
        print(f"URL: {result['url']}\n")

        print("="*80)
        print("Test Complete!")
        print("="*80)
        print("\nCheck your Notion database to see the new entry!")
        print("If everything looks good, you're ready to use the full workflow.\n")

    except Exception as e:
        print(f"\n❌ Error creating entry: {str(e)}\n")
        import traceback
        traceback.print_exc()


def main():
    """Run all Notion tests"""

    print("\n" + "█"*80)
    print(" "*20 + "PHASE 4: NOTION INTEGRATION TEST")
    print("█"*80)

    # Test 1: Connection
    connection_ok = test_notion_connection()

    if connection_ok:
        # Test 2: Create entry
        test_create_entry()
    else:
        print("\n⚠️  Fix connection issues before testing entry creation\n")


if __name__ == '__main__':
    main()
