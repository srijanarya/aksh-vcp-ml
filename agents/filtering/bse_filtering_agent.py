#!/usr/bin/env python3
"""
BSE Filtering Agent

Main agent for Priority 2: Pre-filters stock universe using BSE earnings calendar
to reduce API calls by 70% before expensive OHLCV fetching.

Architecture:
- Uses BSEEarningsCalendarTool to fetch upcoming earnings
- Uses StockFilterByEarningsTool to map BSE → NSE and filter universe
- Provides filtered whitelist to backtesting engine
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from agents.filtering.tools.bse_earnings_calendar_tool import BSEEarningsCalendarTool
from agents.filtering.tools.stock_filter_by_earnings_tool import StockFilterByEarningsTool

logger = logging.getLogger(__name__)


class BSEFilteringAgent:
    """
    Main filtering agent for stock universe reduction

    Features:
    - Fetches upcoming earnings from BSE (7 or 14 day window)
    - Maps BSE codes to NSE symbols
    - Filters original universe to stocks with earnings
    - Tracks filtering performance metrics
    - 70% universe reduction target
    """

    def __init__(
        self,
        earnings_db_path: str = "data/earnings_calendar.db",
        mapping_db_path: str = "data/bse_nse_mapping.db",
        default_lookforward_days: int = 7
    ):
        """
        Initialize BSE filtering agent

        Args:
            earnings_db_path: Path to earnings calendar database
            mapping_db_path: Path to BSE-NSE mapping database
            default_lookforward_days: Default days to look forward for earnings
        """
        self.earnings_tool = BSEEarningsCalendarTool(db_path=earnings_db_path)
        self.filter_tool = StockFilterByEarningsTool(mapping_db_path=mapping_db_path)

        self.default_lookforward_days = default_lookforward_days

        # Performance statistics
        self.stats = {
            'total_runs': 0,
            'total_bse_announcements': 0,
            'total_filtered_stocks': 0,
            'average_reduction': 0.0,
            'cache_hit_rate': 0.0
        }

        logger.info(f"BSE Filtering Agent initialized (lookforward: {default_lookforward_days} days)")

    def filter_universe_by_earnings(
        self,
        original_universe: List[str],
        lookforward_days: Optional[int] = None,
        force_refresh: bool = False
    ) -> Dict:
        """
        Filter stock universe to only stocks with upcoming earnings

        Args:
            original_universe: Original list of NSE symbols
            lookforward_days: Days to look forward (default: use agent's default)
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            Dictionary with:
                - filtered_universe: List of NSE symbols with earnings
                - original_size: Original universe size
                - filtered_size: Filtered universe size
                - reduction_pct: Percentage reduction
                - bse_announcements: Count of BSE announcements found
                - unmapped_codes: Count of BSE codes that couldn't be mapped
        """
        days = lookforward_days or self.default_lookforward_days

        logger.info(f"Filtering universe of {len(original_universe)} stocks (earnings in next {days} days)")

        # Step 1: Get BSE codes with upcoming earnings
        bse_codes_with_earnings = self.earnings_tool.get_stocks_with_upcoming_earnings(
            days_ahead=days,
            force_refresh=force_refresh
        )

        # Step 2: Filter universe using BSE-NSE mapping
        filtered_universe = self.filter_tool.filter_universe(
            original_universe=original_universe,
            bse_codes_with_earnings=bse_codes_with_earnings
        )

        # Calculate metrics
        original_size = len(original_universe)
        filtered_size = len(filtered_universe)
        reduction_pct = ((original_size - filtered_size) / original_size * 100) if original_size > 0 else 0

        # Get mapping statistics
        filter_stats = self.filter_tool.get_stats()

        # Update agent statistics
        self.stats['total_runs'] += 1
        self.stats['total_bse_announcements'] += len(bse_codes_with_earnings)
        self.stats['total_filtered_stocks'] += filtered_size

        # Calculate running average reduction
        self.stats['average_reduction'] = (
            (self.stats['average_reduction'] * (self.stats['total_runs'] - 1) + reduction_pct)
            / self.stats['total_runs']
        )

        result = {
            'filtered_universe': filtered_universe,
            'original_size': original_size,
            'filtered_size': filtered_size,
            'reduction_pct': reduction_pct,
            'bse_announcements': len(bse_codes_with_earnings),
            'unmapped_codes': filter_stats['unmapped_codes'],
            'lookforward_days': days
        }

        logger.info(
            f"Filtering complete: {original_size} → {filtered_size} stocks "
            f"({reduction_pct:.1f}% reduction)"
        )

        return result

    def get_earnings_whitelist(
        self,
        lookforward_days: Optional[int] = None,
        force_refresh: bool = False
    ) -> List[str]:
        """
        Get whitelist of NSE symbols with upcoming earnings

        Args:
            lookforward_days: Days to look forward
            force_refresh: If True, bypass cache

        Returns:
            List of NSE symbols with earnings
        """
        days = lookforward_days or self.default_lookforward_days

        # Get BSE codes with earnings
        bse_codes_with_earnings = self.earnings_tool.get_stocks_with_upcoming_earnings(
            days_ahead=days,
            force_refresh=force_refresh
        )

        # Get NSE whitelist
        whitelist = self.filter_tool.get_whitelist(bse_codes_with_earnings)

        logger.info(f"Generated whitelist: {len(whitelist)} NSE symbols with earnings")

        return list(whitelist)

    def should_analyze_stock(
        self,
        nse_symbol: str,
        lookforward_days: Optional[int] = None,
        force_refresh: bool = False
    ) -> bool:
        """
        Check if a stock should be analyzed (has upcoming earnings)

        Args:
            nse_symbol: NSE symbol to check
            lookforward_days: Days to look forward
            force_refresh: If True, bypass cache

        Returns:
            True if stock has upcoming earnings, False otherwise
        """
        whitelist = self.get_earnings_whitelist(lookforward_days, force_refresh)
        return nse_symbol in whitelist

    def get_stats(self) -> Dict:
        """
        Get agent performance statistics

        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()

    def initialize_mappings(self):
        """
        Initialize BSE-NSE mappings database

        This should be called once to bootstrap the mapping database
        with known Nifty 50 mappings
        """
        logger.info("Initializing BSE-NSE mappings...")
        self.filter_tool.load_nifty_mappings()

        coverage = self.filter_tool.get_mapping_coverage()
        logger.info(
            f"Mapping coverage: {coverage['total_mappings']} total, "
            f"{coverage['unique_nse_symbols']} NSE symbols"
        )

    def warm_earnings_cache(
        self,
        days_ahead: int = 14
    ):
        """
        Warm the earnings calendar cache

        Args:
            days_ahead: Number of days to pre-fetch
        """
        logger.info(f"Warming earnings cache ({days_ahead} days ahead)")

        from_date = datetime.now()
        to_date = from_date + timedelta(days=days_ahead)

        announcements = self.earnings_tool.fetch_bse_announcements(
            from_date=from_date,
            to_date=to_date,
            force_refresh=True
        )

        logger.info(f"Cache warmed: {len(announcements)} announcements fetched")

    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old cached data

        Args:
            days_to_keep: Keep data from last N days
        """
        logger.info(f"Cleaning up data older than {days_to_keep} days")
        self.earnings_tool.cleanup_old_data(days_to_keep=days_to_keep)


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)

    # Initialize agent
    agent = BSEFilteringAgent(default_lookforward_days=7)

    # Initialize mappings (one-time setup)
    agent.initialize_mappings()

    # Demo: Filter Nifty 50 universe
    nifty_50 = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC',
        'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'HCLTECH', 'AXISBANK', 'ASIANPAINT',
        'MARUTI', 'SUNPHARMA', 'TITAN', 'BAJFINANCE', 'ULTRACEMCO', 'NESTLEIND'
    ]

    print(f"\n{'='*70}")
    print("BSE FILTERING AGENT - DEMO")
    print(f"{'='*70}\n")

    print(f"Original universe: {len(nifty_50)} stocks")
    print(f"Lookforward window: 7 days\n")

    # Filter universe
    result = agent.filter_universe_by_earnings(
        original_universe=nifty_50,
        lookforward_days=7,
        force_refresh=False  # Use cache if available
    )

    print(f"\nFILTERING RESULTS:")
    print(f"{'='*70}")
    print(f"Original size:     {result['original_size']} stocks")
    print(f"Filtered size:     {result['filtered_size']} stocks")
    print(f"Reduction:         {result['reduction_pct']:.1f}%")
    print(f"BSE announcements: {result['bse_announcements']}")
    print(f"Unmapped codes:    {result['unmapped_codes']}")

    if result['filtered_universe']:
        print(f"\nFiltered stocks with earnings:")
        for symbol in result['filtered_universe'][:10]:
            print(f"  - {symbol}")
        if len(result['filtered_universe']) > 10:
            print(f"  ... and {len(result['filtered_universe']) - 10} more")
    else:
        print("\n⚠️  No stocks with earnings in next 7 days")
        print("   Try increasing lookforward_days or checking BSE data availability")

    # Show agent statistics
    print(f"\n{'='*70}")
    print("AGENT STATISTICS:")
    print(f"{'='*70}")
    stats = agent.get_stats()
    print(f"Total runs:        {stats['total_runs']}")
    print(f"Average reduction: {stats['average_reduction']:.1f}%")
    print(f"\n✅ Demo complete!")
