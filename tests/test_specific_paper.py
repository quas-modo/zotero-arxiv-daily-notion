"""Test main workflow (analyze, save, sync) with a specific paper - skipping retrieve and filter"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.integrations.notion_client import NotionClient
from src.integrations.zotero_client import ZoteroClient
from src.utils.config_loader import load_config
from src.utils.output_saver import save_analyzed_papers
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def fetch_paper_by_arxiv_id(arxiv_id: str) -> dict:
    """Fetch a specific paper by ArXiv ID"""
    print(f"📥 Fetching paper: {arxiv_id}")
    
    fetcher = ArxivFetcher(categories=['cs.AI'], max_results=1)
    paper = fetcher.fetch_paper_by_id(arxiv_id)
    
    return paper


def test_specific_paper(
    arxiv_id: str = "2601.16163",
    skip_analysis: bool = False,
    skip_notion: bool = False,
    skip_zotero: bool = False,
    skip_save: bool = False,
    deep_dive: bool = False
):
    """
    Test main workflow with a specific paper.
    
    This tests:
    - STEP 4: LLM Analysis (analyze_paper / analyze_paper_with_web_search)
    - Save to files (save_analyzed_papers)
    - STEP 5: Notion sync (create_paper_entry)
    - STEP 6: Zotero sync (add_paper)
    
    Args:
        arxiv_id: ArXiv paper ID to test with
        skip_analysis: Skip LLM analysis step
        skip_notion: Skip Notion sync
        skip_zotero: Skip Zotero sync
        skip_save: Skip saving to files
        deep_dive: Enable deep dive mode with web search
    """
    print("\n" + "="*80)
    print("🧪 TEST: Main Workflow (Analysis + Save + Sync)")
    print("="*80)
    print(f"\nTarget Paper: {arxiv_id}")
    print(f"Skip Analysis: {skip_analysis}")
    print(f"Skip Notion: {skip_notion}")
    print(f"Skip Zotero: {skip_zotero}")
    print(f"Skip Save: {skip_save}")
    print(f"Deep Dive: {deep_dive}")
    print()

    start_time = datetime.now()

    # Load configuration
    try:
        config = load_config()
        llm_config = config.get('llm', {})
        logger.info("Configuration loaded")
    except Exception as e:
        logger.warning(f"Config load failed: {e}, using defaults")
        config = {}
        llm_config = {}

    # ========================================
    # STEP 0: Fetch the specific paper
    # ========================================
    print("="*80)
    print("📥 STEP 0: Fetching specific paper")
    print("-"*80)

    paper = fetch_paper_by_arxiv_id(arxiv_id)
    
    if not paper:
        print(f"❌ Paper not found: {arxiv_id}")
        return

    print(f"✓ Found paper: {paper['title'][:70]}...")
    print(f"  Authors: {', '.join(paper['authors'][:3])}...")
    print(f"  Published: {paper['published_date'].strftime('%Y-%m-%d')}")
    print(f"  Categories: {', '.join(paper['categories'])}")
    print(f"  PDF: {paper['pdf_url']}")
    print()

    # ========================================
    # STEP 4: LLM Analysis
    # ========================================
    print("="*80)
    print("🤖 STEP 4: Analyzing paper with LLM")
    print("-"*80)

    if skip_analysis:
        print("⏭️  Skipping LLM analysis (--skip-analysis)\n")
        # Add minimal fields for downstream steps
        paper['summary'] = '[Analysis skipped]'
        paper['summary_zh'] = '[分析已跳过]'
        paper['detailed_analysis'] = ''
        paper['detailed_analysis_zh'] = ''
        paper['abstract_zh'] = ''
        paper['figures'] = []
        paper['num_figures_analyzed'] = 0
        analyzed_paper = paper
    elif not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set. Skipping analysis.\n")
        paper['summary'] = '[No API key]'
        paper['summary_zh'] = '[无API密钥]'
        analyzed_paper = paper
    else:
        try:
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            print(f"  Model: {model}")
            print(f"  Deep Dive: {deep_dive}")
            
            analyzer = LLMAnalyzer(
                model=model,
                summary_prompt_template=llm_config.get('summary_prompt'),
                detailed_prompt_template=llm_config.get('detailed_prompt'),
                config=config
            )

            print(f"\n  Analyzing: {paper['title'][:60]}...")
            
            if deep_dive:
                print("  🌐 Using deep dive mode with web search...")
                analysis = analyzer.analyze_paper_with_web_search(paper)
                sources_count = len(analysis.get('web_sources', []))
                print(f"  ✓ Analysis complete ({sources_count} web sources)")
            else:
                print("  📄 Using standard analysis mode...")
                analysis = analyzer.analyze_paper(paper)
                print(f"  ✓ Analysis complete ({analysis.get('num_figures_analyzed', 0)} figures)")

            paper.update(analysis)
            analyzed_paper = paper

            # Display results preview
            print(f"\n  Summary Preview:")
            print(f"    {analysis.get('summary', 'N/A')[:200]}...")
            print(f"\n  Chinese Summary Preview:")
            print(f"    {analysis.get('summary_zh', 'N/A')[:200]}...")
            
            if analysis.get('figures'):
                print(f"\n  Figures Extracted: {len(analysis['figures'])}")
                for fig in analysis['figures'][:3]:
                    print(f"    - Figure {fig.get('figure_number', '?')}: {fig.get('caption', 'No caption')[:50]}...")

        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            print(f"❌ Analysis failed: {str(e)}")
            import traceback
            traceback.print_exc()
            analyzed_paper = paper

    print()

    # ========================================
    # Save to files
    # ========================================
    print("="*80)
    print("💾 Saving analysis to files")
    print("-"*80)

    output_files = None
    if skip_save:
        print("⏭️  Skipping save (--skip-save)\n")
    else:
        try:
            json_file, md_file = save_analyzed_papers([analyzed_paper])
            output_files = (json_file, md_file)
            print(f"  ✓ JSON: {json_file}")
            print(f"  ✓ Report: {md_file}")
        except Exception as e:
            logger.error(f"Save failed: {str(e)}")
            print(f"❌ Save failed: {str(e)}")

    print()

    # ========================================
    # STEP 5: Notion sync
    # ========================================
    print("="*80)
    print("📝 STEP 5: Syncing to Notion")
    print("-"*80)

    if skip_notion:
        print("⏭️  Skipping Notion sync (--skip-notion)\n")
    elif not os.getenv('NOTION_API_KEY') or not os.getenv('NOTION_DATABASE_ID'):
        print("⚠️  Notion not configured (missing NOTION_API_KEY or NOTION_DATABASE_ID)\n")
    else:
        try:
            notion_client = NotionClient()
            print(f"  Creating entry for: {analyzed_paper['title'][:60]}...")
            
            response = notion_client.create_paper_entry(analyzed_paper)
            
            page_id = response.get('id', 'unknown')
            page_url = response.get('url', 'unknown')
            
            print(f"  ✓ Notion entry created!")
            print(f"    Page ID: {page_id}")
            print(f"    Page URL: {page_url}")

        except Exception as e:
            logger.error(f"Notion sync failed: {str(e)}")
            print(f"❌ Notion sync failed: {str(e)}")

    print()

    # ========================================
    # STEP 6: Zotero sync
    # ========================================
    print("="*80)
    print("📖 STEP 6: Syncing to Zotero")
    print("-"*80)

    if skip_zotero:
        print("⏭️  Skipping Zotero sync (--skip-zotero)\n")
    elif not os.getenv('ZOTERO_API_KEY') or not os.getenv('ZOTERO_LIBRARY_ID'):
        print("⚠️  Zotero not configured (missing ZOTERO_API_KEY or ZOTERO_LIBRARY_ID)\n")
    else:
        try:
            zotero_client = ZoteroClient()
            
            if zotero_client.enabled:
                print(f"  Adding paper to Zotero: {analyzed_paper['title'][:60]}...")
                
                results = zotero_client.batch_add_papers([analyzed_paper])
                
                if results:
                    print(f"  ✓ Added to Zotero: {results[0].get('key', 'unknown')}")
                else:
                    print("  ⚠️  Paper may already exist in Zotero")
            else:
                print("⚠️  Zotero client not enabled")

        except Exception as e:
            logger.error(f"Zotero sync failed: {str(e)}")
            print(f"❌ Zotero sync failed: {str(e)}")

    print()

    # ========================================
    # Summary
    # ========================================
    elapsed_time = datetime.now() - start_time
    
    print("="*80)
    print("✅ TEST COMPLETED")
    print("="*80)
    print(f"\nSummary:")
    print(f"  • Paper: {analyzed_paper['title'][:60]}...")
    print(f"  • ArXiv ID: {arxiv_id}")
    print(f"  • Analysis: {'Done' if not skip_analysis and 'summary' in analyzed_paper else 'Skipped'}")
    print(f"  • Figures: {analyzed_paper.get('num_figures_analyzed', 0)}")
    print(f"  • Files saved: {'Yes' if output_files else 'No'}")
    print(f"  • Notion sync: {'Skipped' if skip_notion else 'Attempted'}")
    print(f"  • Zotero sync: {'Skipped' if skip_zotero else 'Attempted'}")
    print(f"  • Time elapsed: {elapsed_time.total_seconds():.1f}s")
    
    if output_files:
        print(f"\nOutput Files:")
        print(f"  • JSON: {output_files[0]}")
        print(f"  • Report: {output_files[1]}")
    
    print()
    return analyzed_paper


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test main workflow with a specific paper (skipping retrieve and filter)'
    )
    parser.add_argument(
        '--arxiv-id',
        type=str,
        default='2601.16163',
        help='ArXiv paper ID to test with (default: 2601.16163)'
    )
    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='Skip LLM analysis step'
    )
    parser.add_argument(
        '--skip-notion',
        action='store_true',
        help='Skip Notion sync'
    )
    parser.add_argument(
        '--skip-zotero',
        action='store_true',
        help='Skip Zotero sync'
    )
    parser.add_argument(
        '--skip-save',
        action='store_true',
        help='Skip saving to files'
    )
    parser.add_argument(
        '--deep-dive',
        action='store_true',
        help='Enable deep dive mode with web search'
    )
    parser.add_argument(
        '--notion-only',
        action='store_true',
        help='Only test Notion sync (skip analysis, save, and zotero)'
    )
    parser.add_argument(
        '--analysis-only',
        action='store_true',
        help='Only test LLM analysis (skip notion, zotero, save)'
    )

    args = parser.parse_args()

    # Handle convenience flags
    if args.notion_only:
        args.skip_analysis = True
        args.skip_zotero = True
        args.skip_save = True
    elif args.analysis_only:
        args.skip_notion = True
        args.skip_zotero = True
        args.skip_save = True

    try:
        test_specific_paper(
            arxiv_id=args.arxiv_id,
            skip_analysis=args.skip_analysis,
            skip_notion=args.skip_notion,
            skip_zotero=args.skip_zotero,
            skip_save=args.skip_save,
            deep_dive=args.deep_dive
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
