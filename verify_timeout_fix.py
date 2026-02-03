#!/usr/bin/env python3
"""
Verification script for HTML extraction timeout fix.

Tests the problematic paper (2602.02393) that was previously timing out.
"""

import yaml
import time
from src.utils.content_extractor import ContentExtractor

def main():
    print("\n" + "=" * 70)
    print("HTML Extraction Timeout Fix - Verification")
    print("=" * 70 + "\n")

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    html_config = config.get('html_extraction', {})
    
    print("Configuration:")
    print(f"  - Timeout: {html_config.get('timeout')}s (was 15s)")
    print(f"  - Retry enabled: {html_config.get('retry', {}).get('enabled')}")
    print(f"  - Max retries: {html_config.get('retry', {}).get('max_retries')}")
    print(f"  - Connection pool size: {html_config.get('connection_pool', {}).get('pool_maxsize')}")
    print()

    # Test with the previously failing paper
    test_paper = {
        'arxiv_id': '2602.02393',
        'title': 'Infinite-World (Previously timing out)',
        'html_url': 'https://arxiv.org/html/2602.02393',
        'pdf_url': 'https://arxiv.org/pdf/2602.02393.pdf'
    }

    print(f"Testing paper: {test_paper['title']}")
    print(f"ArXiv ID: {test_paper['arxiv_id']}")
    print("-" * 70)

    # Initialize extractor
    extractor = ContentExtractor(config=config)

    # Time the extraction
    start_time = time.time()
    result = extractor.extract_multimodal_content(test_paper)
    elapsed = time.time() - start_time

    print(f"\n✅ Extraction completed in {elapsed:.2f}s")
    print(f"\nResults:")
    print(f"  - Extraction method: {result['extraction_method'].upper()}")
    print(f"  - HTML available: {result['html_available']}")
    print(f"  - Introduction: {len(result['introduction'])} chars")
    print(f"  - Methodology: {len(result['methodology'])} chars")
    print(f"  - Conclusion: {len(result['conclusion'])} chars")
    print(f"  - Figures extracted: {len(result['figures'])}")
    print(f"  - Full text: {len(result['full_text'])} chars")

    if result['extraction_method'] == 'html' and result['html_available']:
        print("\n" + "=" * 70)
        print("✅ SUCCESS: HTML extraction working!")
        print("=" * 70)
        print("\nBefore fix: Would timeout after 15s")
        print(f"After fix:  Completed in {elapsed:.2f}s with retry support")
        print("\nKey improvements:")
        print("  ✓ Increased timeout to 30s")
        print("  ✓ Added retry mechanism (3 attempts with exponential backoff)")
        print("  ✓ Connection pooling for better performance")
        print("  ✓ Enhanced error handling and logging")
        return True
    else:
        print("\n⚠️  Fell back to PDF extraction")
        print(f"Reason: HTML {'not available' if not result['html_available'] else 'extraction failed'}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
