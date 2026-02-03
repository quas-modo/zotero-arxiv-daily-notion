"""Test script for Phase 3: LLM Analysis"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.filters.relevance_filter import RelevanceFilter
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_phase3():
    """Test LLM analysis functionality"""

    print("\n" + "="*80)
    print("PHASE 3 TEST: LLM Analysis")
    print("="*80 + "\n")

    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY not set in environment")
        print("   Please set your OpenAI API key in .env file")
        return

    # Step 1: Fetch papers
    print("📥 Step 1: Fetching recent papers from ArXiv...")
    fetcher = ArxivFetcher(
        categories=['cs.AI', 'cs.CL', 'cs.LG'],
        max_results=20
    )
    papers = fetcher.fetch_daily_papers(days_back=2)
    print(f"   Found {len(papers)} papers\n")

    # Step 2: Filter papers
    print("🔍 Step 2: Filtering by relevance...")
    filter_engine = RelevanceFilter(
        primary_keywords=['LLM', 'Large Language Model', 'RAG', 'Multi-Agent', 'Robotics'],
        secondary_keywords=['NLP', 'Transformer', 'RLHF'],
        min_score=0.4,  # Higher threshold for testing
        boost_github=True
    )
    filtered_papers = filter_engine.filter_papers(papers, max_papers=3)  # Only top 3 for testing
    print(f"   Selected {len(filtered_papers)} papers\n")

    if not filtered_papers:
        print("❌ No papers passed the relevance filter. Try lowering min_score or adjusting keywords.")
        return

    # Step 3: Analyze papers with LLM
    print("🤖 Step 3: Analyzing papers with OpenAI...")
    analyzer = LLMAnalyzer(model='gpt-4o-mini')  # Use cheaper model for testing

    analyzed_papers = []
    for i, paper in enumerate(filtered_papers, 1):
        print(f"\n   Analyzing paper {i}/{len(filtered_papers)}: {paper['title'][:60]}...")

        analysis = analyzer.analyze_paper(paper)
        paper.update(analysis)
        analyzed_papers.append(paper)

        print(f"   ✓ Analysis complete")

    # Display results
    print("\n" + "="*80)
    print("ANALYSIS RESULTS")
    print("="*80 + "\n")

    for i, paper in enumerate(analyzed_papers, 1):
        print(f"\n{'='*80}")
        print(f"PAPER #{i}")
        print('='*80)
        print(f"\n📄 Title: {paper['title']}")
        print(f"👥 Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
        print(f"🔗 ArXiv: https://arxiv.org/abs/{paper['arxiv_id']}")
        print(f"📊 Relevance Score: {paper['relevance_score']:.2f}")

        if paper.get('github_links'):
            print(f"💻 GitHub: {paper['github_links'][0]}")

        print(f"\n{'─'*80}")
        print("📝 SUMMARY (TL;DR)")
        print('─'*80)
        print(paper['summary'])

        print(f"\n{'─'*80}")
        print("📋 DETAILED ANALYSIS")
        print('─'*80)
        print(paper['detailed_analysis'])

        print("\n")

    print("="*80)
    print("✅ Phase 3 test completed successfully!")
    print(f"   Analyzed {len(analyzed_papers)} papers")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_phase3()
