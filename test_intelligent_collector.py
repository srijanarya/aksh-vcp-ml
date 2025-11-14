#!/usr/bin/env python3
"""
Simple Test Script for Intelligent Earnings Collector
No curl needed - just run this Python script!

Usage:
    python test_intelligent_collector.py
"""

import asyncio
import sys
from pathlib import Path

# Add VCP to path
sys.path.insert(0, '/Users/srijan/vcp_clean_test/vcp')

from agents.intelligent_earnings_collector import IntelligentEarningsCollector


async def test_gap_identification():
    """Test 1: See how many companies are missing earnings data"""
    print("\n" + "="*80)
    print("TEST 1: Identify Data Gaps")
    print("="*80)

    collector = IntelligentEarningsCollector()
    gaps = collector.identify_data_gaps()

    print(f"\n✓ Found {len(gaps)} companies without earnings data")
    print(f"  High priority: {sum(1 for g in gaps if g.priority == 'high')}")
    print(f"  Normal priority: {sum(1 for g in gaps if g.priority == 'normal')}")

    # Show first 5 examples
    print("\n📋 First 5 companies missing data:")
    for i, gap in enumerate(gaps[:5], 1):
        print(f"  {i}. {gap.company_name} ({gap.code}) - {gap.exchange}")

    return gaps


async def test_scraper_only():
    """Test 2: Try scrapers only (no AI, fast test)"""
    print("\n" + "="*80)
    print("TEST 2: Scraper-Only Collection (First 5 Companies)")
    print("="*80)

    collector = IntelligentEarningsCollector(
        enable_web_search=False,  # Disable for faster test
        enable_ai_inference=False  # Disable for faster test
    )

    stats = await collector.collect_missing_data(
        max_companies=5,
        priority_filter="high"
    )

    print("\n📊 Results:")
    print(f"  Total processed: 5")
    print(f"  Data found: {stats['data_found']}")
    print(f"  Scraper success: {stats['scraper_success']}")
    print(f"  Database updates: {stats['database_updates']}")
    print(f"  Processing time: {stats['processing_time']:.1f}s")

    return stats


async def test_with_web_search():
    """Test 3: Try with web search enabled (requires PERPLEXITY_API_KEY)"""
    print("\n" + "="*80)
    print("TEST 3: Web Search Collection (First 3 Companies)")
    print("="*80)

    import os
    if not os.getenv('PERPLEXITY_API_KEY'):
        print("\n⚠️  SKIPPED: PERPLEXITY_API_KEY not set")
        print("   Set it with: export PERPLEXITY_API_KEY='your-key'")
        return None

    collector = IntelligentEarningsCollector(
        enable_web_search=True,   # Enable web search
        enable_ai_inference=False  # Disable AI for faster test
    )

    stats = await collector.collect_missing_data(
        max_companies=3,
        priority_filter="high"
    )

    print("\n📊 Results:")
    print(f"  Total processed: 3")
    print(f"  Data found: {stats['data_found']}")
    print(f"  Scraper success: {stats['scraper_success']}")
    print(f"  Web search success: {stats['web_search_success']}")
    print(f"  Database updates: {stats['database_updates']}")
    print(f"  Processing time: {stats['processing_time']:.1f}s")

    return stats


async def test_full_ai():
    """Test 4: Full AI collection (requires API keys)"""
    print("\n" + "="*80)
    print("TEST 4: Full AI Collection (Scraper + Web + AI)")
    print("="*80)

    import os
    has_perplexity = bool(os.getenv('PERPLEXITY_API_KEY'))
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))

    if not (has_perplexity and (has_openai or has_anthropic)):
        print("\n⚠️  SKIPPED: Missing API keys")
        print("   Needs: PERPLEXITY_API_KEY + (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        return None

    collector = IntelligentEarningsCollector(
        enable_web_search=True,
        enable_ai_inference=True
    )

    stats = await collector.collect_missing_data(
        max_companies=2,  # Only 2 for testing (AI is slow)
        priority_filter="high"
    )

    print("\n📊 Results:")
    print(f"  Total processed: 2")
    print(f"  Data found: {stats['data_found']}")
    print(f"  Scraper success: {stats['scraper_success']}")
    print(f"  Web search success: {stats['web_search_success']}")
    print(f"  AI inference success: {stats['ai_inference_success']}")
    print(f"  Database updates: {stats['database_updates']}")
    print(f"  Processing time: {stats['processing_time']:.1f}s")

    return stats


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 INTELLIGENT EARNINGS COLLECTOR - TEST SUITE")
    print("="*80)

    # Test 1: Gap identification (always works)
    gaps = await test_gap_identification()

    # Test 2: Scraper only (always works, no API keys needed)
    await test_scraper_only()

    # Test 3: Web search (requires PERPLEXITY_API_KEY)
    await test_with_web_search()

    # Test 4: Full AI (requires all API keys)
    await test_full_ai()

    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE")
    print("="*80)
    print(f"\nTotal companies needing data: {len(gaps)}")
    print("\n💡 Next steps:")
    print("   1. Set API keys if not already set")
    print("   2. Run: python scripts/daily_earnings_gap_filler.py --max-companies 50")
    print("   3. Check results in calendar API")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
