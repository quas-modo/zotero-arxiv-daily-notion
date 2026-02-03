"""Quick test of Phase 2 with longer date range"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.filters.relevance_filter import RelevanceFilter
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def quick_test():
    print("\n" + "="*80)
    print("QUICK TEST: ArXiv Fetching and Filtering")
    print("="*80 + "\n")

    # Fetch papers from last 7 days
    print("📥 Fetching papers from ArXiv (last 7 days)...")
    fetcher = ArxivFetcher(
        categories=['cs.AI'],
        max_results=20
    )
    papers = fetcher.fetch_daily_papers(days_back=7)
    print(f"   Found {len(papers)} papers\n")

    if not papers:
        print("❌ No papers found. ArXiv might be down or there's a connectivity issue.")
        return

    # Filter papers
    print("🔍 Filtering papers by relevance...")
    filter_engine = RelevanceFilter(
        primary_keywords=['LLM', 'Large Language Model', 'Agent', 'GPT'],
        secondary_keywords=['NLP', 'Transformer'],
        min_score=0.3,
        boost_github=True
    )
    filtered = filter_engine.filter_papers(papers, max_papers=5)
    print(f"   Selected {len(filtered)} papers\n")

    # Display results
    print("="*80)
    print("TOP PAPERS")
    print("="*80 + "\n")

    for i, paper in enumerate(filtered, 1):
        print(f"#{i} [Score: {paper['relevance_score']:.2f}]")
        print(f"   Title: {paper['title']}")
        print(f"   ArXiv ID: {paper['arxiv_id']}")
        print(f"   Date: {paper['published_date'].strftime('%Y-%m-%d')}")
        print(f"   Categories: {', '.join(paper['categories'])}")

        matched = filter_engine.get_matched_keywords(paper)
        print(f"   Matched: {', '.join(matched)}")
        print()

    print("="*80)
    print(f"✅ Test completed! Found {len(papers)} papers, filtered to {len(filtered)}")
    print("="*80 + "\n")


if __name__ == '__main__':
    quick_test()
