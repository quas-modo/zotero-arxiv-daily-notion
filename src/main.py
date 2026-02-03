"""Main orchestration script for the Research Paper Intelligence Assistant"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.filters.relevance_filter import RelevanceFilter
from src.filters.similarity_filter import SimilarityFilter
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.integrations.notion_client import NotionClient
from src.integrations.zotero_client import ZoteroClient
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger
from src.utils.scholar_inbox_reader import ScholarInboxReader
from src.utils.output_saver import save_analyzed_papers

# Load environment variables
load_dotenv()

logger = setup_logger(__name__)


def main(dry_run: bool = False, max_papers: int = None):
    """
    Main workflow: Fetch, filter, analyze, and sync papers.

    Args:
        dry_run: If True, don't create Notion/Zotero entries
        max_papers: Override max papers to process
    """
    print("\n" + "="*80)
    print("🤖 RESEARCH PAPER INTELLIGENCE ASSISTANT")
    print("="*80 + "\n")

    start_time = datetime.now()

    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully")
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return

    # Extract config sections
    arxiv_config = config.get('arxiv', {})
    keywords = config.get('keywords', {})
    filtering_config = config.get('filtering', {})
    similarity_config = config.get('similarity_filter', {})
    llm_config = config.get('llm', {})

    # Override max papers if specified
    if max_papers:
        filtering_config['max_papers_per_day'] = max_papers

    # STEP 1: Fetch papers from ArXiv
    print("📥 STEP 1: Fetching papers from ArXiv")
    print("-" * 80)

    fetcher = ArxivFetcher(
        categories=arxiv_config.get('categories', ['cs.AI']),
        max_results=arxiv_config.get('max_results', 50)
    )

    papers = fetcher.fetch_daily_papers(days_back=7)
    print(f"✓ Found {len(papers)} papers from the last 7 days\n")

    if not papers:
        logger.warning("No papers found. Exiting.")
        return

    # STEP 2: Filter papers by similarity (Primary Filter)
    print("🔍 STEP 2: Filtering papers by similarity to your research")
    print("-" * 80)

    similarity_enabled = similarity_config.get('enabled', False)

    if similarity_enabled:
        try:
            # Initialize similarity filter
            similarity_filter = SimilarityFilter(
                min_similarity=similarity_config.get('min_similarity_score', 0.6),
                top_k=similarity_config.get('top_k_papers', 20),
                model_name=similarity_config.get('embedding_model', 'all-MiniLM-L6-v2'),
                enable_cache=similarity_config.get('cache_embeddings', True)
            )

            # Load reference papers from Zotero
            if similarity_config.get('use_zotero_library', True):
                print("  Loading reference papers from Zotero...")
                zotero_client = ZoteroClient()
                if zotero_client.enabled:
                    zotero_papers = zotero_client.get_papers_for_embedding(
                        limit=similarity_config.get('zotero_paper_limit', 100)
                    )
                    if zotero_papers:
                        similarity_filter.add_reference_papers(zotero_papers, source='zotero')
                        print(f"  ✓ Loaded {len(zotero_papers)} papers from Zotero")
                    else:
                        print("  ⚠️  No papers found in Zotero library")
                else:
                    print("  ⚠️  Zotero not configured")

            # Load reference papers from scholar-inbox
            scholar_inbox_file = similarity_config.get('scholar_inbox_file')
            if scholar_inbox_file:
                print("  Loading reference papers from scholar-inbox...")
                scholar_papers = ScholarInboxReader.read_file(scholar_inbox_file)
                if scholar_papers:
                    similarity_filter.add_reference_papers(scholar_papers, source='scholar-inbox')
                    print(f"  ✓ Loaded {len(scholar_papers)} papers from scholar-inbox")

            # Check if we have reference papers
            stats = similarity_filter.get_stats()
            if stats['num_reference_papers'] == 0:
                print("  ⚠️  No reference papers loaded. Falling back to keyword filtering only.\n")
                filtered_papers = papers
            else:
                print(f"\n  Using {stats['num_reference_papers']} reference papers for similarity matching")
                print(f"  Model: {stats['model_name']} ({stats['embedding_dimension']} dimensions)\n")

                # Filter by similarity
                filtered_papers = similarity_filter.filter_papers(papers)
                print(f"✓ Selected {len(filtered_papers)} similar papers\n")

        except Exception as e:
            logger.error(f"Similarity filtering failed: {str(e)}")
            print(f"⚠️  Similarity filtering failed: {str(e)}")
            print("  Falling back to keyword filtering only.\n")
            filtered_papers = papers
            similarity_enabled = False

    else:
        print("⚠️  Similarity filtering disabled. Using keyword filtering only.\n")
        filtered_papers = papers

    if not filtered_papers:
        logger.warning("No papers passed similarity filter. Exiting.")
        return

    # STEP 3: Boost scores with keyword matching (Secondary Filter)
    print("🏷️  STEP 3: Boosting relevance with keyword matching")
    print("-" * 80)

    filter_engine = RelevanceFilter(
        primary_keywords=keywords.get('primary', []),
        secondary_keywords=keywords.get('secondary', []),
        min_score=0.0,  # Don't filter, just score
        boost_github=filtering_config.get('prioritize_github_links', True)
    )

    # Score all papers with keywords
    keyword_scored_papers = filter_engine.filter_papers(filtered_papers, max_papers=999999)

    # Combine scores if similarity was used
    if similarity_enabled and similarity_config.get('similarity_weight'):
        similarity_weight = similarity_config.get('similarity_weight', 0.7)
        keyword_weight = similarity_config.get('keyword_weight', 0.3)

        print(f"  Combining scores: {similarity_weight:.0%} similarity + {keyword_weight:.0%} keywords\n")

        for paper in keyword_scored_papers:
            similarity_score = paper.get('similarity_score', 0.0)
            keyword_score = paper.get('relevance_score', 0.0)

            # Combined score
            paper['combined_score'] = (similarity_weight * similarity_score) + (keyword_weight * keyword_score)
            paper['similarity_score'] = similarity_score
            paper['keyword_score'] = keyword_score

        # Sort by combined score
        keyword_scored_papers.sort(key=lambda x: x.get('combined_score', 0), reverse=True)

        # Display top papers with scores
        print("Top papers by combined score:")
        for i, paper in enumerate(keyword_scored_papers[:10], 1):
            sim = paper.get('similarity_score', 0)
            kw = paper.get('keyword_score', 0)
            combined = paper.get('combined_score', 0)
            print(f"  {i}. [{combined:.2f}] (sim:{sim:.2f} + kw:{kw:.2f}) {paper['title'][:60]}...")

    else:
        # Use keyword scores only
        for paper in keyword_scored_papers:
            paper['combined_score'] = paper.get('relevance_score', 0.0)

        print("Using keyword scores only:")
        for i, paper in enumerate(keyword_scored_papers[:10], 1):
            score = paper.get('combined_score', 0)
            print(f"  {i}. [{score:.2f}] {paper['title'][:60]}...")

    # Keep top N papers
    max_papers_count = filtering_config.get('max_papers_per_day', 10)
    final_papers = keyword_scored_papers[:max_papers_count]
    print(f"\n✓ Keeping top {len(final_papers)} papers for analysis\n")

    # STEP 4: Analyze papers with LLM
    print("🤖 STEP 4: Analyzing papers with LLM")
    print("-" * 80)

    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OPENAI_API_KEY not set. Skipping LLM analysis.")
        print("⚠️  OpenAI API key not configured. Skipping analysis.\n")
        analyzed_papers = final_papers
    else:
        try:
            analyzer = LLMAnalyzer(
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                summary_prompt_template=llm_config.get('summary_prompt'),
                detailed_prompt_template=llm_config.get('detailed_prompt')
            )

            analyzed_papers = []
            for i, paper in enumerate(final_papers, 1):
                print(f"  [{i}/{len(final_papers)}] {paper['title'][:60]}...")

                try:
                    analysis = analyzer.analyze_paper(paper)
                    paper.update(analysis)
                    analyzed_papers.append(paper)
                    print(f"      ✓ Complete")
                except Exception as e:
                    logger.error(f"Analysis failed for paper {i}: {str(e)}")
                    print(f"      ✗ Error: {str(e)}")
                    analyzed_papers.append(paper)  # Add without analysis

            print(f"\n✓ Analyzed {len(analyzed_papers)} papers\n")

        except Exception as e:
            logger.error(f"LLM analyzer initialization failed: {str(e)}")
            print(f"⚠️  LLM analysis failed: {str(e)}\n")
            analyzed_papers = final_papers

    # Save analyzed papers to files
    print("💾 Saving analysis to files...")
    print("-" * 80)
    output_files = None
    try:
        json_file, md_file = save_analyzed_papers(analyzed_papers)
        output_files = (json_file, md_file)
        print()
    except Exception as e:
        logger.error(f"Failed to save outputs: {str(e)}")
        print(f"⚠️  Failed to save outputs: {str(e)}\n")

    # STEP 5: Sync to Notion
    print("📝 STEP 5: Syncing to Notion")
    print("-" * 80)

    if dry_run:
        print("⚠️  Dry run mode - skipping Notion sync\n")
    elif not os.getenv('NOTION_API_KEY') or not os.getenv('NOTION_DATABASE_ID'):
        print("⚠️  Notion not configured. Skipping sync.\n")
    else:
        try:
            notion_client = NotionClient()

            print(f"Creating {len(analyzed_papers)} entries in Notion...")
            results = notion_client.batch_create_entries(analyzed_papers)

            print(f"✓ Created {len(results)} Notion entries\n")

        except Exception as e:
            logger.error(f"Notion sync failed: {str(e)}")
            print(f"⚠️  Notion sync failed: {str(e)}\n")

    # STEP 6: Sync to Zotero (Optional)
    print("📖 STEP 6: Syncing to Zotero (Optional)")
    print("-" * 80)

    if dry_run:
        print("⚠️  Dry run mode - skipping Zotero sync\n")
    elif not os.getenv('ZOTERO_API_KEY'):
        print("⚠️  Zotero not configured. Skipping.\n")
    else:
        try:
            zotero_client = ZoteroClient()

            if zotero_client.enabled:
                print(f"Adding {len(analyzed_papers)} papers to Zotero...")
                results = zotero_client.batch_add_papers(analyzed_papers)
                print(f"✓ Added {len(results)} papers to Zotero\n")
            else:
                print("⚠️  Zotero client not enabled. Skipping.\n")

        except Exception as e:
            logger.error(f"Zotero sync failed: {str(e)}")
            print(f"⚠️  Zotero sync failed: {str(e)}\n")

    # Summary
    elapsed_time = datetime.now() - start_time
    print("="*80)
    print("✅ WORKFLOW COMPLETED")
    print("="*80)
    print(f"\nSummary:")
    print(f"  • Papers fetched: {len(papers)}")
    print(f"  • Papers after filtering: {len(final_papers)}")
    print(f"  • Papers analyzed: {len(analyzed_papers)}")
    print(f"  • Time elapsed: {elapsed_time.total_seconds():.1f}s")
    print(f"\nOutput Files:")
    print(f"  • Logs: logs/paper_assistant_{datetime.now().strftime('%Y%m%d')}.log")
    if output_files:
        print(f"  • JSON: {output_files[0]}")
        print(f"  • Report: {output_files[1]}")
    print()


def schedule_daily_run():
    """Schedule daily execution"""
    import schedule
    import time

    schedule_config = load_config().get('schedule', {})
    run_time = schedule_config.get('run_time', '09:00')

    logger.info(f"Scheduling daily run at {run_time}")
    print(f"\n⏰ Scheduled to run daily at {run_time}")
    print("Press Ctrl+C to stop\n")

    schedule.every().day.at(run_time).do(main)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Research Paper Intelligence Assistant'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without creating Notion/Zotero entries'
    )
    parser.add_argument(
        '--max-papers',
        type=int,
        help='Maximum number of papers to process'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run on schedule (daily at configured time)'
    )

    args = parser.parse_args()

    try:
        if args.schedule:
            schedule_daily_run()
        else:
            main(dry_run=args.dry_run, max_papers=args.max_papers)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
