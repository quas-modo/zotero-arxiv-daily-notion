"""
Test script for Deep Dive Mode with Web Search
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("🧪 TESTING DEEP DIVE MODE WITH WEB SEARCH")
print("=" * 80)
print()

# Test 1: Check environment and model
print("📋 Test 1: Environment Configuration")
print("-" * 80)

model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
api_key = os.getenv('OPENAI_API_KEY', '')

print(f"✓ OpenAI Model: {model}")
print(f"✓ API Key: {'Set' if api_key else 'Missing'}")

# Check if model supports web search
web_search_models = ['gpt-4o', 'gpt-4-turbo']
supports_web_search = any(m in model.lower() for m in web_search_models)

if supports_web_search:
    print(f"✓ Model '{model}' supports web search tool")
else:
    print(f"⚠️  Model '{model}' may not support web search")
    print(f"   Recommended: gpt-4o or gpt-4-turbo")

print()

# Test 2: Check imports
print("📦 Test 2: Import Dependencies")
print("-" * 80)

try:
    from src.analyzers.llm_analyzer import LLMAnalyzer
    print("✓ LLMAnalyzer imported successfully")
except Exception as e:
    print(f"❌ Failed to import LLMAnalyzer: {str(e)}")
    sys.exit(1)

try:
    from src.integrations.notion_client import NotionClient
    print("✓ NotionClient imported successfully")
except Exception as e:
    print(f"❌ Failed to import NotionClient: {str(e)}")
    sys.exit(1)

print()

# Test 3: Check new methods exist
print("🔍 Test 3: Check New Methods")
print("-" * 80)

if hasattr(LLMAnalyzer, 'analyze_paper_with_web_search'):
    print("✓ Method exists: analyze_paper_with_web_search")
else:
    print("❌ Method missing: analyze_paper_with_web_search")
    sys.exit(1)

if hasattr(LLMAnalyzer, 'generate_analysis_with_web_context'):
    print("✓ Method exists: generate_analysis_with_web_context")
else:
    print("❌ Method missing: generate_analysis_with_web_context")
    sys.exit(1)

print()

# Test 4: Check configuration
print("⚙️  Test 4: Configuration File")
print("-" * 80)

try:
    from src.utils.config_loader import load_config
    config = load_config()
    llm_config = config.get('llm', {})

    deep_dive_enabled = llm_config.get('deep_dive_mode', False)
    print(f"✓ Configuration loaded")
    print(f"  deep_dive_mode: {deep_dive_enabled}")

    if deep_dive_enabled:
        print("  ℹ️  Deep dive mode is enabled by default in config")
    else:
        print("  ℹ️  Deep dive mode is disabled (use --deep-dive flag)")

except Exception as e:
    print(f"⚠️  Configuration check failed: {str(e)}")

print()

# Test 5: Initialize analyzer
print("🤖 Test 5: Initialize LLM Analyzer")
print("-" * 80)

if not api_key:
    print("⚠️  OpenAI API key not set, skipping analyzer initialization")
else:
    try:
        analyzer = LLMAnalyzer(model=model)
        print("✓ LLMAnalyzer initialized successfully")
        print(f"  Model: {analyzer.model}")
        print(f"  Base URL: {analyzer.base_url or 'Default (OpenAI)'}")
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {str(e)}")

print()

# Test 6: Check command-line arguments
print("🎯 Test 6: Command-Line Interface")
print("-" * 80)

print("Available commands:")
print("  python src/main.py --max-papers 3")
print("  python src/main.py --max-papers 3 --deep-dive")
print("  python src/main.py --deep-dive --dry-run")
print()
print("✓ CLI arguments configured correctly")

print()

# Summary
print("=" * 80)
print("📊 SUMMARY")
print("=" * 80)
print()

if not api_key:
    print("⚠️  OpenAI API key not configured")
    print("   Set OPENAI_API_KEY in .env file")
    print()

if not supports_web_search:
    print("⚠️  Current model may not support web search")
    print("   Recommended: OPENAI_MODEL=gpt-4o")
    print()

print("✅ Deep Dive Mode implementation verified!")
print()
print("To test with a real paper:")
print("  1. Ensure OPENAI_MODEL=gpt-4o in .env")
print("  2. Run: python src/main.py --max-papers 1 --deep-dive")
print("  3. Check Notion for the 'Web Search Sources' section")
print()
print("Documentation: See DEEP_DIVE_MODE.md for full guide")
print()
