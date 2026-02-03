"""Test Phase 3 with a specific paper"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_specific_paper():
    """Test LLM analysis with a specific paper"""

    print("\n" + "="*80)
    print("PHASE 3 TEST: LLM Analysis - Specific Paper")
    print("="*80 + "\n")

    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY not set")
        return

    # Initialize fetcher
    fetcher = ArxivFetcher(categories=['cs.RO'], max_results=10)

    # Search for the specific paper
    print("📥 Searching for 'LingBot-VA' paper...")
    papers = fetcher.search_by_keywords(['LingBot-VA', 'Causal video-action world model'], max_results=5)

    if not papers:
        print("   Paper not found by keyword search. Trying to fetch recent robotics papers...")
        papers = fetcher.fetch_daily_papers(days_back=30)

    if not papers:
        print("❌ No papers found")
        return

    # Find LingBot-VA or use first paper
    target_paper = None
    for paper in papers:
        if 'lingbot' in paper['title'].lower() or 'video-action' in paper['title'].lower():
            target_paper = paper
            break

    if not target_paper:
        print(f"   LingBot-VA not found in search. Using first available paper instead.")
        target_paper = papers[0]

    print(f"✓ Found paper: {target_paper['title']}\n")

    # Initialize analyzer
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    base_url = os.getenv('OPENAI_BASE_URL')

    print(f"🤖 Initializing LLM Analyzer...")
    print(f"   Model: {model}")
    if base_url:
        print(f"   Base URL: {base_url}")
    print()

    try:
        analyzer = LLMAnalyzer(model=model)
        print("✓ Analyzer initialized\n")
    except Exception as e:
        print(f"❌ Error initializing analyzer: {str(e)}")
        return

    # Analyze the paper
    print("="*80)
    print("ANALYZING PAPER")
    print("="*80)
    print(f"\n📄 Title: {target_paper['title']}")
    print(f"👥 Authors: {', '.join(target_paper['authors'][:5])}")
    print(f"🔗 ArXiv: https://arxiv.org/abs/{target_paper['arxiv_id']}")
    print(f"📅 Published: {target_paper['published_date'].strftime('%Y-%m-%d')}")
    print(f"\n📋 Abstract:\n{target_paper['abstract'][:500]}...\n")

    print("="*80)
    print("Generating analysis (this may take 30-60 seconds)...")
    print("="*80 + "\n")

    try:
        # Generate summary
        print("📝 Generating summary...")
        summary = analyzer.generate_summary(target_paper)
        print("✓ Summary complete\n")

        # Generate detailed analysis
        print("📋 Generating detailed analysis...")
        detailed = analyzer.generate_detailed_analysis(target_paper)
        print("✓ Detailed analysis complete\n")

        # Display results
        print("\n" + "="*80)
        print("ANALYSIS RESULTS")
        print("="*80 + "\n")

        print("─"*80)
        print("📝 SUMMARY (TL;DR)")
        print("─"*80)
        print(summary)

        print(f"\n{'─'*80}")
        print("📋 DETAILED ANALYSIS")
        print("─"*80)
        print(detailed)

        print("\n" + "="*80)
        print("✅ Phase 3 test completed successfully!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_specific_paper()
