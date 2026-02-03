"""Test script to verify OpenAI API configuration with custom base URL"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.llm_analyzer import LLMAnalyzer


def test_openai_config():
    """Test OpenAI API configuration"""

    print("\n" + "="*80)
    print("OpenAI Configuration Test")
    print("="*80 + "\n")

    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set in .env file")
        print("\nPlease create a .env file:")
        print("  cp .env.example .env")
        print("\nThen add your OpenAI API key:")
        print("  OPENAI_API_KEY=sk-your-key-here")
        return

    print(f"✓ API Key: {api_key[:10]}...{api_key[-4:]}")

    # Check base URL
    base_url = os.getenv('OPENAI_BASE_URL')
    if base_url:
        print(f"✓ Custom Base URL: {base_url}")
    else:
        print("✓ Using default OpenAI API endpoint")

    # Check model
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    print(f"✓ Model: {model}\n")

    # Try to initialize the analyzer
    try:
        print("Initializing LLM Analyzer...")
        analyzer = LLMAnalyzer(model=model)
        print("✓ LLM Analyzer initialized successfully!\n")

        # Test with a simple paper
        print("Testing with a sample paper...")
        test_paper = {
            'title': 'Attention Is All You Need',
            'authors': ['Vaswani', 'Shazeer', 'Parmar'],
            'abstract': 'We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
        }

        print("Generating summary (this will make an API call)...\n")
        summary = analyzer.generate_summary(test_paper)

        print("="*80)
        print("SUCCESS! Summary generated:")
        print("="*80)
        print(summary)
        print("="*80 + "\n")

        print("✅ OpenAI API is working correctly!")
        print(f"   Base URL: {analyzer.base_url or 'https://api.openai.com/v1 (default)'}")
        print(f"   Model: {analyzer.model}\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        print("Troubleshooting:")
        print("  1. Check your API key is correct")
        print("  2. If using custom base URL, verify it's accessible")
        print("  3. Check your internet connection")
        print("  4. Verify the model name is correct\n")
        return

    print("="*80)
    print("Configuration Test Complete!")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_openai_config()
