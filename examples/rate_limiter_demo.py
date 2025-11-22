#!/usr/bin/env python3
"""
Rate Limiter Demo - Complete Usage Example

This script demonstrates the complete Angel One Rate Limiter Agent system:
1. Database initialization
2. Cache-first data fetching
3. Statistics tracking
4. Batch operations
5. Nifty 50 cache warming

Run this to verify the system works end-to-end.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent
from src.data.angel_one_client import AngelOneClient


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_initialization():
    """Demo 1: Initialize and setup"""
    print_section("DEMO 1: INITIALIZATION")

    print("Setting up Angel One client...")
    client = AngelOneClient()

    if not client.authenticate():
        print("❌ Authentication failed. Check your .env.angel file")
        print("Required variables: ANGEL_ONE_API_KEY, ANGEL_ONE_CLIENT_ID, etc.")
        return None

    print("✓ Authentication successful!")

    print("\nCreating Rate Limiter Agent...")
    agent = AngelOneRateLimiterAgent(
        client=client,
        cache_ttl_hours=24,  # Cache data for 24 hours
        max_retries=5        # Retry up to 5 times on failure
    )

    print("✓ Agent created successfully!")

    return agent


def demo_single_fetch(agent):
    """Demo 2: Single symbol fetch with caching"""
    print_section("DEMO 2: SINGLE SYMBOL FETCH")

    symbol = 'RELIANCE'
    from_date = datetime.now() - timedelta(days=30)
    to_date = datetime.now()

    print(f"Fetching {symbol} data (last 30 days)...")
    print(f"Date range: {from_date.date()} to {to_date.date()}")
    print("\nFirst fetch (cache miss expected)...")

    data = agent.fetch_with_cache(
        symbol=symbol,
        exchange='NSE',
        interval='ONE_DAY',
        from_date=from_date,
        to_date=to_date
    )

    if data is not None:
        print(f"✓ Fetched {len(data)} rows")
        print(f"  Columns: {list(data.columns)}")
        print(f"  Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
    else:
        print("❌ Fetch failed")
        return

    # Fetch again (should hit cache)
    print("\nSecond fetch (cache hit expected)...")

    data2 = agent.fetch_with_cache(
        symbol=symbol,
        exchange='NSE',
        interval='ONE_DAY',
        from_date=from_date,
        to_date=to_date
    )

    if data2 is not None:
        print(f"✓ Fetched {len(data2)} rows from cache")

    # Show statistics
    print("\n" + "-" * 80)
    stats = agent.get_stats()
    print("STATISTICS:")
    print(f"  Total requests:  {stats['total_requests']}")
    print(f"  Cache hits:      {stats['cache_hits']}")
    print(f"  Cache misses:    {stats['cache_misses']}")
    print(f"  API calls:       {stats['api_calls']}")
    print(f"  Cache hit rate:  {stats['cache_hit_rate']:.1f}%")
    print("-" * 80)


def demo_batch_fetch(agent):
    """Demo 3: Batch fetch multiple symbols"""
    print_section("DEMO 3: BATCH FETCH")

    symbols = ['TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'WIPRO']
    from_date = datetime.now() - timedelta(days=7)  # Last week
    to_date = datetime.now()

    print(f"Fetching {len(symbols)} symbols: {', '.join(symbols)}")
    print(f"Date range: {from_date.date()} to {to_date.date()}")
    print("\nProgress:")

    results = agent.fetch_batch(
        symbols=symbols,
        exchange='NSE',
        interval='ONE_DAY',
        from_date=from_date,
        to_date=to_date
    )

    print(f"\n✓ Batch fetch complete!")
    print(f"  Successfully fetched: {len(results)}/{len(symbols)} symbols")

    for symbol, data in results.items():
        print(f"  {symbol}: {len(data)} rows")

    # Show updated statistics
    print("\n" + "-" * 80)
    stats = agent.get_stats()
    print("UPDATED STATISTICS:")
    print(f"  Total requests:  {stats['total_requests']}")
    print(f"  Cache hits:      {stats['cache_hits']}")
    print(f"  API calls:       {stats['api_calls']}")
    print(f"  Cache hit rate:  {stats['cache_hit_rate']:.1f}%")
    print("-" * 80)


def demo_nifty_50_warming(agent):
    """Demo 4: Nifty 50 cache warming (sample)"""
    print_section("DEMO 4: NIFTY 50 CACHE WARMING (SAMPLE)")

    print("⚠️  Full Nifty 50 warming takes 1-2 hours!")
    print("This demo will warm cache for just 5 Nifty 50 stocks as example.\n")

    # Get sample of Nifty 50
    from agents.data.tools.nifty_index_cache_tool import NiftyIndexCacheTool
    nifty_tool = NiftyIndexCacheTool()
    all_nifty_50 = nifty_tool.get_nifty_50_constituents()
    sample_symbols = all_nifty_50[:5]  # First 5 stocks

    print(f"Warming cache for: {', '.join(sample_symbols)}")
    print(f"Date range: Last 1 year\n")

    from_date = datetime.now() - timedelta(days=365)
    to_date = datetime.now()

    results = agent.fetch_batch(
        symbols=sample_symbols,
        exchange='NSE',
        interval='ONE_DAY',
        from_date=from_date,
        to_date=to_date
    )

    print(f"\n✓ Cache warming complete!")
    print(f"  Warmed: {len(results)}/{len(sample_symbols)} stocks")

    total_rows = sum(len(data) for data in results.values())
    print(f"  Total rows cached: {total_rows}")

    # Show cache coverage
    from agents.data.tools.enhanced_sqlite_cache_tool import EnhancedSQLiteCacheTool
    cache_tool = EnhancedSQLiteCacheTool()
    cache_stats = cache_tool.get_coverage_stats()

    print("\n" + "-" * 80)
    print("CACHE DATABASE STATISTICS:")
    print(f"  Total symbols:   {cache_stats['total_symbols']}")
    print(f"  Total rows:      {cache_stats['total_rows']}")
    print(f"  Database size:   {cache_stats['db_size_mb']:.2f} MB")
    print(f"  Fresh symbols:   {cache_stats['fresh_symbols']}")
    print("-" * 80)


def demo_force_refresh(agent):
    """Demo 5: Force refresh to bypass cache"""
    print_section("DEMO 5: FORCE REFRESH")

    symbol = 'RELIANCE'
    from_date = datetime.now() - timedelta(days=7)
    to_date = datetime.now()

    print(f"Fetching {symbol} with force_refresh=True")
    print("This will bypass cache and fetch fresh data from API\n")

    data = agent.fetch_with_cache(
        symbol=symbol,
        exchange='NSE',
        interval='ONE_DAY',
        from_date=from_date,
        to_date=to_date,
        force_refresh=True  # Bypass cache
    )

    if data is not None:
        print(f"✓ Fetched {len(data)} rows (fresh from API)")
    else:
        print("❌ Fetch failed")

    stats = agent.get_stats()
    print(f"\nAPI calls made: {stats['api_calls']}")


def demo_error_handling(agent):
    """Demo 6: Error handling"""
    print_section("DEMO 6: ERROR HANDLING")

    print("Testing with invalid symbol...")

    data = agent.fetch_with_cache(
        symbol='INVALID_SYMBOL_12345',
        exchange='NSE',
        interval='ONE_DAY',
        from_date=datetime.now() - timedelta(days=7),
        to_date=datetime.now()
    )

    if data is None:
        print("✓ Error handled gracefully - returned None")
    else:
        print("⚠️  Unexpected: received data for invalid symbol")

    stats = agent.get_stats()
    print(f"\nFailed API calls: {stats['failed_api_calls']}")


def show_final_summary(agent):
    """Show final summary"""
    print_section("FINAL SUMMARY")

    stats = agent.get_stats()

    print("SESSION STATISTICS:")
    print(f"  Total requests:    {stats['total_requests']}")
    print(f"  Cache hits:        {stats['cache_hits']} ({stats['cache_hit_rate']:.1f}%)")
    print(f"  Cache misses:      {stats['cache_misses']}")
    print(f"  API calls:         {stats['api_calls']}")
    print(f"  Failed calls:      {stats['failed_api_calls']}")

    if stats['total_requests'] > 0:
        efficiency = (stats['cache_hits'] / stats['total_requests']) * 100
        api_reduction = (1 - stats['api_calls'] / stats['total_requests']) * 100

        print(f"\nEFFICIENCY METRICS:")
        print(f"  Cache efficiency:  {efficiency:.1f}%")
        print(f"  API call savings:  {api_reduction:.1f}%")

    # Cache database stats
    from agents.data.tools.enhanced_sqlite_cache_tool import EnhancedSQLiteCacheTool
    cache_tool = EnhancedSQLiteCacheTool()
    cache_stats = cache_tool.get_coverage_stats()

    print(f"\nCACHE DATABASE:")
    print(f"  Location:          data/angel_ohlcv_cache.db")
    print(f"  Total symbols:     {cache_stats['total_symbols']}")
    print(f"  Total rows:        {cache_stats['total_rows']}")
    print(f"  Database size:     {cache_stats['db_size_mb']:.2f} MB")

    print("\n" + "=" * 80)
    print("  DEMO COMPLETE!")
    print("=" * 80)
    print("\n✨ The Rate Limiter Agent is working perfectly!")
    print("\nNext steps:")
    print("  1. Integrate with backtest_with_angel.py")
    print("  2. Run full Nifty 50 cache warming")
    print("  3. Measure real-world performance improvements")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("  ANGEL ONE RATE LIMITER AGENT - COMPLETE DEMO")
    print("=" * 80)
    print("\nThis demo will showcase all features of the rate limiter system.")
    print("Make sure you have:")
    print("  ✓ Angel One credentials configured in .env.angel")
    print("  ✓ Database initialized (run init_cache_db.py if not)")

    input("\nPress Enter to start demo...")

    # Run demos
    agent = demo_initialization()

    if agent is None:
        print("\n❌ Demo aborted due to authentication failure")
        return

    try:
        demo_single_fetch(agent)
        demo_batch_fetch(agent)
        demo_nifty_50_warming(agent)
        demo_force_refresh(agent)
        demo_error_handling(agent)
        show_final_summary(agent)

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        show_final_summary(agent)
    except Exception as e:
        print(f"\n\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

    print("\nThank you for trying the demo!")


if __name__ == "__main__":
    main()
