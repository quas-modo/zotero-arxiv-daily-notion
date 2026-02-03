"""
Demo script showing the complete workflow (Phases 1-3)

This demonstrates:
1. Fetching papers from ArXiv
2. Filtering by relevance
3. Analyzing with LLM (summary + detailed analysis)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.filters.relevance_filter import RelevanceFilter
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Run the complete paper analysis workflow"""

    print("\n" + "="*80)
    print("🤖 Research Paper Intelligence Assistant - Demo")
    print("="*80 + "\n")

    # Load configuration
    try:
        config = load_config()
        print("✓ Configuration loaded\n")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return

    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ ERROR: OPENAI_API_KEY not set")
        print("   Please create a .env file and add your OpenAI API key:")
        print("   OPENAI_API_KEY=sk-your-key-here\n")
        return

    # Extract config sections
    arxiv_config = config.get('arxiv', {})
    keywords = config.get('keywords', {})
    filtering_config = config.get('filtering', {})
    llm_config = config.get('llm', {})

    # Step 1: Fetch papers from ArXiv
    print("📥 Step 1: Fetching papers from ArXiv...")
    fetcher = ArxivFetcher(
        categories=arxiv_config.get('categories', ['cs.AI']),
        max_results=arxiv_config.get('max_results', 30)
    )

    papers = fetcher.fetch_daily_papers(days_back=2)
    print(f"   Found {len(papers)} papers from the last 2 days\n")

    if not papers:
        print("❌ No papers found. Try adjusting the date range or categories.")
        return

    # Step 2: Filter papers by relevance
    print("🔍 Step 2: Filtering papers by relevance...")
    filter_engine = RelevanceFilter(
        primary_keywords=keywords.get('primary', []),
        secondary_keywords=keywords.get('secondary', []),
        min_score=filtering_config.get('min_relevance_score', 0.3),
        boost_github=filtering_config.get('prioritize_github_links', True)
    )

    max_papers = filtering_config.get('max_papers_per_day', 10)
    # For demo, limit to 2 papers to save API costs
    demo_limit = min(2, max_papers)

    filtered_papers = filter_engine.filter_papers(papers, max_papers=demo_limit)
    print(f"   Selected top {len(filtered_papers)} papers (demo mode)\n")

    if not filtered_papers:
        print("❌ No papers passed the relevance filter.")
        print("   Try adjusting keywords in config/config.yaml or lowering min_relevance_score")
        return

    # Step 3: Analyze papers with LLM
    print("🤖 Step 3: Analyzing papers with OpenAI...")
    print(f"   Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}\n")

    analyzer = LLMAnalyzer(
        model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        summary_prompt_template=llm_config.get('summary_prompt'),
        detailed_prompt_template=llm_config.get('detailed_prompt')
    )

    analyzed_papers = []
    for i, paper in enumerate(filtered_papers, 1):
        print(f"   [{i}/{len(filtered_papers)}] {paper['title'][:60]}...")

        try:
            analysis = analyzer.analyze_paper(paper)
            paper.update(analysis)
            analyzed_papers.append(paper)
            print(f"       ✓ Complete\n")
        except Exception as e:
            print(f"       ✗ Error: {str(e)}\n")
            continue

    # Display results
    print("\n" + "="*80)
    print("📊 ANALYSIS RESULTS")
    print("="*80 + "\n")

    for i, paper in enumerate(analyzed_papers, 1):
        print(f"\n{'█'*80}")
        print(f"  PAPER #{i}: {paper['title']}")
        print('█'*80)

        print(f"\n📌 Metadata:")
        print(f"   • Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
        print(f"   • ArXiv ID: {paper['arxiv_id']}")
        print(f"   • Published: {paper['published_date'].strftime('%Y-%m-%d')}")
        print(f"   • Categories: {', '.join(paper['categories'])}")
        print(f"   • Relevance Score: {paper['relevance_score']:.2f}")
        print(f"   • PDF: {paper['pdf_url']}")

        if paper.get('github_links'):
            print(f"   • GitHub: {paper['github_links'][0]}")

        matched = filter_engine.get_matched_keywords(paper)
        print(f"   • Matched Keywords: {', '.join(matched)}")

        print(f"\n{'─'*80}")
        print("📝 SUMMARY")
        print('─'*80)
        print(paper.get('summary', 'N/A'))

        print(f"\n{'─'*80}")
        print("📋 DETAILED ANALYSIS")
        print('─'*80)
        print(paper.get('detailed_analysis', 'N/A'))

        print("\n")

    print("="*80)
    print(f"✅ Demo completed! Analyzed {len(analyzed_papers)} papers")
    print("="*80)

    print("\n💡 Next Steps:")
    print("   1. Set up Notion integration (get API key and database ID)")
    print("   2. Run the full workflow with Phase 4 to sync to Notion")
    print("   3. Set up daily automation with cron or systemd\n")


if __name__ == '__main__':
    main()
