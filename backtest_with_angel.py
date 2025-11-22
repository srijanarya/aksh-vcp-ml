#!/usr/bin/env python3
"""
Quick Backtest Using Angel One API
NO Yahoo Finance rate limits!

Tests our Multi-Timeframe Breakout Strategy with:
- Beta > 1.0
- ADX > 20
- RS > 1.0 (optional confluence)
- Simplified confluences (2 of 7)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import os

# Angel One imports
from src.data.angel_one_client import AngelOneClient
from agents.data.angel_rate_limiter_agent import AngelOneRateLimiterAgent
from agents.filtering.bse_filtering_agent import BSEFilteringAgent

# Strategy import
from strategies.multi_timeframe_breakout import MultiTimeframeBreakoutStrategy


# NIFTY 50 symbols for focused testing
NIFTY_50 = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'HINDUNILVR', 'ITC',
    'SBIN', 'BHARTIARTL', 'KOTAKBANK', 'LT', 'HCLTECH', 'AXISBANK', 'ASIANPAINT',
    'MARUTI', 'SUNPHARMA', 'TITAN', 'BAJFINANCE', 'ULTRACEMCO', 'NESTLEIND',
    'WIPRO', 'ADANIENT', 'ADANIPORTS', 'NTPC', 'TATAMOTORS', 'ONGC', 'POWERGRID',
    'COALINDIA', 'TATASTEEL', 'M&M', 'JSWSTEEL', 'HINDALCO', 'INDUSINDBK',
    'TECHM', 'BAJAJFINSV', 'CIPLA', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'BRITANNIA',
    'APOLLOHOSP', 'HEROMOTOCO', 'DIVISLAB', 'BPCL', 'TATACONSUM', 'SBILIFE',
    'HDFCLIFE', 'BAJAJ-AUTO', 'SHREECEM', 'UPL'
]


class AngelBacktester:
    """Simple backtester using Angel One data with BSE pre-filtering"""

    def __init__(self, enable_bse_filtering: bool = False, lookforward_days: int = 7):
        print("🚀 Initializing Angel One Backtester...")
        print("=" * 70)

        # Initialize Angel One client
        self.client = self._init_angel_client()
        # Use Rate Limiter Agent for 90% API call reduction
        self.rate_limiter_agent = AngelOneRateLimiterAgent(
            client=self.client,
            cache_ttl_hours=24  # 24 hour cache
        )

        # Initialize BSE filtering (optional, for 70% universe reduction)
        self.enable_bse_filtering = enable_bse_filtering
        self.bse_filter_agent = None
        if enable_bse_filtering:
            self.bse_filter_agent = BSEFilteringAgent(
                default_lookforward_days=lookforward_days
            )
            print(f"   BSE filtering enabled (lookforward: {lookforward_days} days)")

        # Initialize strategy
        self.strategy = MultiTimeframeBreakoutStrategy()

        print(f"✅ Initialized!")
        print(f"   Beta threshold: {self.strategy.high_beta_threshold}")
        print(f"   ADX threshold: {self.strategy.min_adx}")
        print(f"   S/R quality: {self.strategy.min_sr_quality}")
        print(f"   Min confluences: {self.strategy.min_confluences} of 7")
        if enable_bse_filtering:
            print(f"   BSE filtering: ENABLED (70% universe reduction target)")
        print("=" * 70)
        print()

    def _init_angel_client(self) -> AngelOneClient:
        """Initialize Angel One client with authentication"""
        # Check for .env.angel file
        env_path = Path("/Users/srijan/Desktop/aksh/.env.angel")

        if not env_path.exists():
            print(f"❌ Angel One credentials not found at {env_path}")
            print("   Please create .env.angel with:")
            print("   ANGELONE_API_KEY=your_key")
            print("   ANGELONE_CLIENT_ID=your_id")
            print("   ANGELONE_PASSWORD=your_password")
            print("   ANGELONE_TOTP_SECRET=your_totp")
            sys.exit(1)

        # Load and authenticate
        client = AngelOneClient.from_env_file(str(env_path))

        print("   Authenticating with Angel One...")
        if not client.authenticate():
            print("   ❌ Authentication failed!")
            sys.exit(1)

        print("   ✅ Authenticated successfully!")
        return client

    def fetch_angel_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Fetch multi-timeframe data from Angel One"""

        try:
            # Fetch daily data with caching (90% API call reduction)
            daily = self.rate_limiter_agent.fetch_with_cache(
                symbol=symbol,
                exchange="NSE",
                interval="ONE_DAY",
                from_date=start_date,
                to_date=end_date
            )

            if daily.empty:
                return {}

            # Resample to weekly
            weekly = daily.resample('W', on='timestamp').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()

            # Rename columns to match strategy expectations
            daily_renamed = daily.rename(columns={
                'timestamp': 'date'
            }).set_index('date')

            weekly_renamed = weekly.copy()
            weekly_renamed.index.name = 'date'

            return {
                'daily': daily_renamed,
                'weekly': weekly_renamed,
                '4h': pd.DataFrame()  # Not needed, strategy handles empty
            }

        except Exception as e:
            print(f"   ❌ Error fetching data for {symbol}: {e}")
            return {}

    def run_backtest(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ):
        """
        Run backtest on list of symbols

        Args:
            symbols: List of NSE symbols (without .NS suffix)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Apply BSE filtering if enabled
        original_size = len(symbols)
        if self.enable_bse_filtering and self.bse_filter_agent:
            print(f"\n🔍 PRE-FILTERING WITH BSE EARNINGS CALENDAR...")
            print(f"   Original universe: {len(symbols)} stocks")

            filter_result = self.bse_filter_agent.filter_universe_by_earnings(
                original_universe=symbols,
                lookforward_days=None,  # Use agent default
                force_refresh=False
            )

            symbols = filter_result['filtered_universe']

            print(f"   Filtered universe: {len(symbols)} stocks")
            print(f"   Reduction: {filter_result['reduction_pct']:.1f}%")
            print(f"   BSE announcements: {filter_result['bse_announcements']}")
            print("=" * 70)

        print(f"\n🔍 BACKTESTING {len(symbols)} STOCKS")
        if self.enable_bse_filtering:
            print(f"   (Filtered from {original_size} stocks via BSE earnings)")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Duration: {(end_dt - start_dt).days} days")
        print("=" * 70)
        print()

        signals = []
        errors = []

        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] Analyzing {symbol}...")

            try:
                # Fetch Angel One data
                mtf_data = self.fetch_angel_data(symbol, start_dt, end_dt)

                if not mtf_data or 'daily' not in mtf_data:
                    print(f"   ⚠️  No data available\n")
                    errors.append(f"{symbol}: No data")
                    continue

                # Override strategy's data fetching method temporarily
                # by directly calling generate_signal with our data
                original_fetch = self.strategy.fetch_multi_timeframe_data

                def mock_fetch(sym, lookback=365):
                    return mtf_data

                self.strategy.fetch_multi_timeframe_data = mock_fetch

                # Generate signal
                signal = self.strategy.generate_signal(symbol)

                # Restore original method
                self.strategy.fetch_multi_timeframe_data = original_fetch

                if signal:
                    signals.append(signal)
                    print(f"   ✅ SIGNAL GENERATED!\n")
                else:
                    print(f"   ❌ No signal (filtered out)\n")

            except Exception as e:
                print(f"   ❌ Error: {e}\n")
                errors.append(f"{symbol}: {str(e)}")
                continue

        # Print summary with cache statistics
        print("=" * 70)
        print("📊 BACKTEST RESULTS")
        print("=" * 70)

        # Show rate limiter performance
        stats = self.rate_limiter_agent.get_stats()
        print(f"\n⚡ API PERFORMANCE:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Cache hits: {stats['cache_hits']} ({stats['cache_hit_rate']:.1f}%)")
        print(f"   API calls: {stats['api_calls']}")
        if stats['total_requests'] > 0:
            savings = (1 - stats['api_calls'] / stats['total_requests']) * 100
            print(f"   API savings: {savings:.1f}%")

        print(f"\n📈 BACKTEST METRICS:")
        print(f"   Total Analyzed: {len(symbols)}")
        print(f"   Signals Found: {len(signals)}")
        print(f"   Errors: {len(errors)}")
        print()

        if signals:
            print(f"\n🎯 {len(signals)} TRADING SIGNALS FOUND:\n")
            for i, sig in enumerate(signals, 1):
                print(f"{i}. {sig.symbol}")
                print(f"   Entry: ₹{sig.entry_price:.2f}")
                print(f"   Stop: ₹{sig.stop_loss:.2f}")
                print(f"   Target: ₹{sig.target:.2f}")
                print(f"   R:R: 1:{sig.risk_reward_ratio:.2f}")
                print(f"   Strength: {sig.strength_score:.1f}/100")
                print(f"   Beta: {sig.beta:.2f}")
                if sig.adx_metrics:
                    print(f"   ADX: {sig.adx_metrics['adx']:.1f}")
                if sig.rs_metrics:
                    print(f"   RS 30d: {sig.rs_metrics['rs_30d']:.2f}x")
                print(f"   Confluences ({len(sig.confluences)}): {', '.join(sig.confluences)}")
                print()
        else:
            print("\n❌ NO SIGNALS FOUND")
            print("\nPossible reasons:")
            print("  - Strategy criteria too strict")
            print("  - Market in downtrend/consolidation")
            print("  - No breakouts during test period")
            print("\nConsider:")
            print("  - Relaxing one filter (beta, ADX, or S/R quality)")
            print("  - Testing longer time period")
            print("  - Testing different market phase (bull market)")

        if errors:
            print(f"\n⚠️  {len(errors)} ERRORS:")
            for error in errors[:10]:  # Show first 10
                print(f"   - {error}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more")

        print()
        print("=" * 70)

        return signals


def main():
    """Run backtest"""

    print("\n" + "=" * 70)
    print("  MULTI-TIMEFRAME BREAKOUT BACKTEST - ANGEL ONE DATA")
    print("=" * 70)
    print()

    # Initialize backtester with optional BSE filtering
    # Set enable_bse_filtering=True to enable 70% universe reduction
    bt = AngelBacktester(
        enable_bse_filtering=False,  # Set to True to enable BSE pre-filtering
        lookforward_days=7  # Only matters if BSE filtering is enabled
    )

    # Run on NIFTY 50
    signals = bt.run_backtest(
        symbols=NIFTY_50,
        start_date="2022-01-01",
        end_date="2024-11-01"
    )

    print("\n✅ Backtest complete!")
    print()


if __name__ == '__main__':
    main()
