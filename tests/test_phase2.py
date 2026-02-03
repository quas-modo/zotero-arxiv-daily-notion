"""Test script for Phase 2: ArXiv fetching and filtering"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.filters.relevance_filter import RelevanceFilter
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def test_phase2():
    """Test ArXiv fetching and filtering"""

    print("\n" + "="*80)
    print("PHASE 2 TEST: ArXiv Fetching and Filtering")
    print("="*80 + "\n")

    # Initialize fetcher
    print("📥 Step 1: Fetching papers from ArXiv...")
    fetcher = ArxivFetcher(
        categories=['cs.AI', 'cs.CL', 'cs.LG'],
        max_results=30
    )

    papers = fetcher.fetch_daily_papers(days_back=2)
    print(f"   Found {len(papers)} papers from the last 2 days\n")

    # Initialize filter
    print("🔍 Step 2: Filtering papers by relevance...")
    filter_engine = RelevanceFilter(
        primary_keywords=['LLM', 'Large Language Model', 'RAG', 'Multi-Agent', 'Robotics'],
        secondary_keywords=['NLP', 'Transformer', 'RLHF', 'Reinforcement Learning'],
        min_score=0.3,
        boost_github=True
    )

    filtered_papers = filter_engine.filter_papers(papers, max_papers=10)
    print(f"   Selected {len(filtered_papers)} relevant papers\n")

    # Display results
    print("="*80)
    print("TOP PAPERS")
    print("="*80 + "\n")

    for i, paper in enumerate(filtered_papers, 1):
        print(f"#{i} [Score: {paper['relevance_score']:.2f}]")
        print(f"   Title: {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
        print(f"   ArXiv ID: {paper['arxiv_id']}")
        print(f"   Categories: {', '.join(paper['categories'])}")
        print(f"   PDF: {paper['pdf_url']}")

        if paper.get('github_links'):
            print(f"   GitHub: {paper['github_links'][0]}")

        # Show matched keywords
        matched = filter_engine.get_matched_keywords(paper)
        print(f"   Matched Keywords: {', '.join(matched)}")

        print(f"   Abstract: {paper['abstract'][:200]}...")
        print()

    print("="*80)
    print("✅ Phase 2 test completed successfully!")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_phase2()
