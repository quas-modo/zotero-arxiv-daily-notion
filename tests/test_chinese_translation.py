#!/usr/bin/env python3
"""Test Chinese translation functionality"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.llm_analyzer import LLMAnalyzer
from src.utils.output_saver import save_analyzed_papers
import os
from dotenv import load_dotenv

load_dotenv()

# Sample paper for testing
sample_paper = {
    'title': 'Test Paper: Attention Is All You Need',
    'authors': ['Vaswani', 'Shazeer'],
    'arxiv_id': '1706.03762',
    'published_date': '2017-06-12',
    'abstract': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms.',
    'pdf_url': 'https://arxiv.org/pdf/1706.03762.pdf',
    'entry_url': 'https://arxiv.org/abs/1706.03762',
    'categories': ['cs.CL', 'cs.LG'],
    'relevance_score': 0.95
}

print("\n" + "="*80)
print("TESTING CHINESE TRANSLATION")
print("="*80 + "\n")

# Initialize analyzer
print("1. Initializing LLM analyzer...")
analyzer = LLMAnalyzer(
    model=os.getenv('OPENAI_MODEL', 'gpt-4o')
)
print("   ✓ Analyzer initialized\n")

# Analyze paper (will include Chinese translations)
print("2. Analyzing paper (English + Chinese)...")
print(f"   Paper: {sample_paper['title']}\n")

analysis = analyzer.analyze_paper(sample_paper)
sample_paper.update(analysis)

print("   ✓ Analysis complete\n")

# Check results
print("3. Checking results...")
print(f"   - English summary: {len(analysis.get('summary', ''))} chars")
print(f"   - Chinese summary: {len(analysis.get('summary_zh', ''))} chars")
print(f"   - English analysis: {len(analysis.get('detailed_analysis', ''))} chars")
print(f"   - Chinese analysis: {len(analysis.get('detailed_analysis_zh', ''))} chars")
print(f"   - Chinese abstract: {len(analysis.get('abstract_zh', ''))} chars")
print()

# Preview Chinese summary
if analysis.get('summary_zh'):
    print("4. Preview Chinese summary:")
    print("-" * 80)
    preview = analysis['summary_zh'][:300]
    print(preview + "..." if len(analysis['summary_zh']) > 300 else preview)
    print("-" * 80)
    print()

# Save to files
print("5. Saving to output files...")
json_file, md_file = save_analyzed_papers([sample_paper], output_dir="data/outputs")
print()

print("="*80)
print("✅ TEST COMPLETE")
print("="*80)
print(f"\nCheck the files:")
print(f"  • {md_file}")
print(f"  • {json_file}\n")
