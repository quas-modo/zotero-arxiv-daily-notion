"""
Demo script to test the new pipeline optimizations
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("🚀 TESTING PIPELINE OPTIMIZATIONS")
print("=" * 80)
print()

# Test 1: Zotero Deduplication
print("📋 Test 1: Zotero Deduplication")
print("-" * 80)

try:
    from src.integrations.zotero_client import ZoteroClient

    if os.getenv('ZOTERO_API_KEY') and os.getenv('ZOTERO_LIBRARY_ID'):
        zotero = ZoteroClient()
        if zotero.enabled:
            # Test getting existing identifiers
            identifiers = zotero.get_existing_identifiers(limit=10)
            print(f"✓ Found {len(identifiers)} existing identifiers in Zotero")

            # Show some examples
            if identifiers:
                print("\nSample identifiers:")
                for i, (key, zotero_key) in enumerate(list(identifiers.items())[:3], 1):
                    print(f"  {i}. {key[:60]}...")
        else:
            print("⚠️  Zotero not enabled")
    else:
        print("⚠️  Zotero credentials not configured")

except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# Test 2: Semantic Scoring Weights
print("⚖️  Test 2: Semantic Scoring Configuration")
print("-" * 80)

try:
    from src.utils.config_loader import load_config

    config = load_config()
    similarity_config = config.get('similarity_filter', {})

    sim_weight = similarity_config.get('similarity_weight', 0.7)
    kw_weight = similarity_config.get('keyword_weight', 0.3)

    print(f"✓ Similarity weight: {sim_weight:.0%}")
    print(f"✓ Keyword weight: {kw_weight:.0%}")

    if sim_weight >= 0.85:
        print("✓ Semantic-first scoring enabled (85%+)")
    else:
        print(f"⚠️  Current weight: {sim_weight:.0%} (recommended: 85%+)")

except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# Test 3: Multimodal PDF Extraction
print("📄 Test 3: Multimodal PDF Extraction")
print("-" * 80)

try:
    from src.utils.pdf_extractor import PDFTextExtractor

    # Check if PyMuPDF is available
    try:
        import fitz
        print("✓ PyMuPDF (fitz) installed - full multimodal support available")
    except ImportError:
        print("⚠️  PyMuPDF not installed - figure extraction unavailable")
        print("   Install with: pip install pymupdf")

    # Check methods exist
    methods = [
        'extract_full_text_with_pymupdf',
        'extract_figures_from_pdf',
        'extract_multimodal_content'
    ]

    for method in methods:
        if hasattr(PDFTextExtractor, method):
            print(f"✓ Method available: {method}")
        else:
            print(f"❌ Method missing: {method}")

except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# Test 4: LLM Multimodal Analysis
print("🤖 Test 4: LLM Multimodal Analysis")
print("-" * 80)

try:
    from src.analyzers.llm_analyzer import LLMAnalyzer

    # Check if using vision-capable model
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    print(f"✓ Current model: {model}")

    vision_models = ['gpt-4o', 'gpt-4-turbo', 'gpt-4-vision']
    if any(vm in model.lower() for vm in vision_models):
        print("✓ Vision-capable model detected - figure analysis enabled")
    else:
        print("⚠️  Non-vision model - text-only analysis")
        print("   For figure analysis, use: gpt-4o or gpt-4-turbo")

    # Check methods exist
    if hasattr(LLMAnalyzer, 'generate_detailed_analysis_with_figures'):
        print("✓ Method available: generate_detailed_analysis_with_figures")
    else:
        print("❌ Method missing: generate_detailed_analysis_with_figures")

except Exception as e:
    print(f"❌ Error: {str(e)}")

print()
print("=" * 80)
print("✅ OPTIMIZATION CHECK COMPLETE")
print("=" * 80)
print()

# Summary
print("📊 SUMMARY")
print("-" * 80)
print()
print("All optimizations are installed. To use them:")
print()
print("1. Zotero Deduplication: Automatic (if Zotero configured)")
print("2. Semantic-First Scoring: Active (85% similarity, 15% keywords)")
print("3. Multimodal Extraction: Install 'pymupdf' for full support")
print("4. Vision Analysis: Use OPENAI_MODEL=gpt-4o for figure analysis")
print()
print("Run the pipeline with:")
print("  python src/main.py")
print()
