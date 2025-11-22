#!/usr/bin/env python3
"""
Batched Backtest Using Angel One API with Checkpointing

Features:
- Uses pre-cached symbol tokens (run preload_angel_symbols.py first)
- Aggressive rate limiting (2 seconds between requests)
- Batch processing (50 stocks at a time)
- Checkpoint saving (can resume from failures)
- Progress tracking

Usage:
    # First, pre-load symbol tokens:
    python3 tools/preload_angel_symbols.py

    # Then run backtest:
    python3 backtest_angel_batched.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

# Angel One imports
from src.data.angel_one_client import AngelOneClient
from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

# Strategy import
from strategies.multi_timeframe_breakout import MultiTimeframeBreakoutStrategy


class BatchedAngelBacktester:
    """Batched backtester with checkpointing and rate limiting"""

    def __init__(
        self,
        symbol_cache_file: str = "/tmp/angel_symbol_cache.json",
        checkpoint_file: str = "/tmp/backtest_checkpoint.json",
        results_file: str = "/tmp/backtest_signals.json",
        rate_limit_delay: float = 2.0
    ):
        print("🚀 Initializing Batched Angel One Backtester...")
        print("=" * 70)

        # Initialize Angel One client
        self.client = self._init_angel_client()
        self.ohlcv_fetcher = AngelOneOHLCVFetcher(
            client=self.client,
            cache_ttl=86400  # 24 hour cache
        )

        # Initialize strategy
        self.strategy = MultiTimeframeBreakoutStrategy()

        # Load symbol token cache
        self.symbol_cache = self._load_symbol_cache(symbol_cache_file)
        print(f"   Symbol cache: {len(self.symbol_cache)} tokens loaded")

        # Checkpoint management
        self.checkpoint_file = checkpoint_file
        self.results_file = results_file
        self.rate_limit_delay = rate_limit_delay

        # Load checkpoint if exists
        self.checkpoint = self._load_checkpoint()

        print(f"✅ Initialized!")
        print(f"   Beta threshold: {self.strategy.high_beta_threshold}")
        print(f"   ADX threshold: {self.strategy.min_adx}")
        print(f"   S/R quality: {self.strategy.min_sr_quality}")
        print(f"   Min confluences: {self.strategy.min_confluences} of 7")
        print(f"   Rate limit: {self.rate_limit_delay}s between requests")
        print("=" * 70)
        print()

    def _init_angel_client(self) -> AngelOneClient:
        """Initialize Angel One client with authentication"""
        env_path = Path("/Users/srijan/Desktop/aksh/.env.angel")

        if not env_path.exists():
            print(f"❌ Angel One credentials not found at {env_path}")
            sys.exit(1)

        # Load and authenticate
        client = AngelOneClient.from_env_file(str(env_path))

        print("   Authenticating with Angel One...")
        if not client.authenticate():
            print("   ❌ Authentication failed!")
            sys.exit(1)

        print("   ✅ Authenticated successfully!")
        return client

    def _load_symbol_cache(self, cache_file: str) -> Dict[str, str]:
        """Load pre-cached symbol tokens"""
        cache_path = Path(cache_file)

        if not cache_path.exists():
            print(f"\n⚠️  WARNING: Symbol cache not found at {cache_file}")
            print("   Run 'python3 tools/preload_angel_symbols.py' first to pre-load symbols")
            print("   Continuing without cache (will be slower)...\n")
            return {}

        with open(cache_file, 'r') as f:
            return json.load(f)

    def _load_checkpoint(self) -> Dict:
        """Load checkpoint if exists"""
        checkpoint_path = Path(self.checkpoint_file)

        if checkpoint_path.exists():
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            print(f"📦 Resuming from checkpoint: {checkpoint['last_processed']} stocks analyzed")
            return checkpoint
        else:
            return {
                'last_processed': 0,
                'signals_found': 0,
                'errors': 0
            }

    def _save_checkpoint(self, checkpoint: Dict):
        """Save checkpoint"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def _save_signal(self, signal):
        """Append signal to results file"""
        # Load existing results
        results = []
        results_path = Path(self.results_file)

        if results_path.exists():
            with open(self.results_file, 'r') as f:
                results = json.load(f)

        # Add new signal
        signal_dict = {
            'symbol': signal.symbol,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'target': signal.target,
            'risk_reward_ratio': signal.risk_reward_ratio,
            'strength_score': signal.strength_score,
            'beta': signal.beta,
            'adx': signal.adx_metrics['adx'] if signal.adx_metrics else None,
            'rs_30d': signal.rs_metrics['rs_30d'] if signal.rs_metrics else None,
            'rs_trend': signal.rs_metrics['rs_trend'] if signal.rs_metrics else None,
            'confluences': signal.confluences,
            'sr_quality_score': signal.sr_quality_score,
            'timestamp': signal.timestamp.isoformat()
        }
        results.append(signal_dict)

        # Save
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

    def get_symbol_token(self, symbol: str) -> Optional[str]:
        """Get symbol token (from cache or API)"""
        # Check cache first
        if symbol in self.symbol_cache:
            return self.symbol_cache[symbol]

        # Fallback to API lookup (slower)
        try:
            symbol_eq = f"{symbol}-EQ"
            response = self.client._smart_api.searchScrip("NSE", symbol_eq)

            if response.get('status') and response.get('data'):
                for item in response['data']:
                    if item.get('tradingsymbol') == symbol_eq and item.get('exchange') == 'NSE':
                        token = item.get('symboltoken')
                        # Cache for future use
                        self.symbol_cache[symbol] = token
                        return token

            return None

        except Exception as e:
            print(f"   ❌ Token lookup error: {e}")
            return None

    def fetch_angel_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Fetch multi-timeframe data from Angel One"""

        try:
            # Get symbol token
            token = self.get_symbol_token(symbol)

            if not token:
                return {}

            # Rate limiting
            time.sleep(self.rate_limit_delay)

            # Fetch daily data using token directly
            historic_params = {
                'exchange': 'NSE',
                'symboltoken': token,
                'interval': 'ONE_DAY',
                'fromdate': start_date.strftime("%Y-%m-%d %H:%M"),
                'todate': end_date.strftime("%Y-%m-%d %H:%M")
            }

            response = self.client._smart_api.getCandleData(historic_params)

            if not response.get('status'):
                print(f"   ⚠️  API error: {response.get('message', 'Unknown error')}")
                return {}

            # Transform to DataFrame
            data = response.get('data', [])
            if not data:
                return {}

            daily = pd.DataFrame(
                data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            daily['timestamp'] = pd.to_datetime(daily['timestamp'])

            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                daily[col] = pd.to_numeric(daily[col])

            # Resample to weekly
            weekly = daily.set_index('timestamp').resample('W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna().reset_index()

            # Rename columns to match strategy expectations
            daily_renamed = daily.rename(columns={'timestamp': 'date'}).set_index('date')
            weekly_renamed = weekly.rename(columns={'timestamp': 'date'}).set_index('date')

            return {
                'daily': daily_renamed,
                'weekly': weekly_renamed,
                '4h': pd.DataFrame()  # Not needed
            }

        except Exception as e:
            error_msg = str(e)
            if 'access rate' in error_msg.lower():
                print(f"   ⚠️  Rate limit hit, waiting 60s...")
                time.sleep(60)
                # Retry
                return self.fetch_angel_data(symbol, start_date, end_date)
            else:
                print(f"   ❌ Error: {error_msg}")
                return {}

    def run_batch(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        batch_size: int = 50
    ):
        """
        Run backtest in batches with checkpointing

        Args:
            symbols: List of NSE symbols (without .NS suffix)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            batch_size: Number of stocks per batch
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        print(f"\n🔍 BATCHED BACKTESTING")
        print(f"   Total stocks: {len(symbols)}")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Duration: {(end_dt - start_dt).days} days")
        print(f"   Batch size: {batch_size} stocks")
        print(f"   Starting from: Stock #{self.checkpoint['last_processed'] + 1}")
        print("=" * 70)
        print()

        # Resume from checkpoint
        start_idx = self.checkpoint['last_processed']
        signals_found = self.checkpoint['signals_found']
        errors = self.checkpoint['errors']

        # Process in batches
        for batch_start in range(start_idx, len(symbols), batch_size):
            batch_end = min(batch_start + batch_size, len(symbols))
            batch_symbols = symbols[batch_start:batch_end]

            print(f"\n{'='*70}")
            print(f"BATCH: Stocks {batch_start + 1} to {batch_end} of {len(symbols)}")
            print(f"{'='*70}\n")

            for i, symbol in enumerate(batch_symbols, batch_start + 1):
                print(f"[{i}/{len(symbols)}] Analyzing {symbol}...")

                try:
                    # Fetch Angel One data
                    mtf_data = self.fetch_angel_data(symbol, start_dt, end_dt)

                    if not mtf_data or 'daily' not in mtf_data or mtf_data['daily'].empty:
                        print(f"   ⚠️  No data available\n")
                        errors += 1
                        continue

                    # Override strategy's data fetching
                    original_fetch = self.strategy.fetch_multi_timeframe_data

                    def mock_fetch(sym, lookback=365):
                        return mtf_data

                    self.strategy.fetch_multi_timeframe_data = mock_fetch

                    # Generate signal
                    signal = self.strategy.generate_signal(symbol)

                    # Restore original method
                    self.strategy.fetch_multi_timeframe_data = original_fetch

                    if signal:
                        signals_found += 1
                        self._save_signal(signal)
                        print(f"   ✅ SIGNAL #{signals_found} GENERATED!\n")
                    else:
                        print(f"   ❌ No signal (filtered out)\n")

                except KeyboardInterrupt:
                    print(f"\n\n⚠️  Interrupted by user at stock {i}/{len(symbols)}")
                    self._save_checkpoint({
                        'last_processed': i,
                        'signals_found': signals_found,
                        'errors': errors
                    })
                    print(f"   Checkpoint saved. Resume by running script again.")
                    sys.exit(0)

                except Exception as e:
                    print(f"   ❌ Error: {e}\n")
                    errors += 1

                # Update checkpoint every 10 stocks
                if i % 10 == 0:
                    self._save_checkpoint({
                        'last_processed': i,
                        'signals_found': signals_found,
                        'errors': errors
                    })
                    print(f"   💾 Checkpoint saved (signals: {signals_found}, errors: {errors})")

        # Final summary
        print("=" * 70)
        print("📊 BACKTEST COMPLETE")
        print("=" * 70)
        print(f"Total Analyzed: {len(symbols)}")
        print(f"Signals Found: {signals_found}")
        print(f"Errors: {errors}")
        print(f"Results saved to: {self.results_file}")
        print("=" * 70)
        print()

        # Clear checkpoint
        if Path(self.checkpoint_file).exists():
            os.remove(self.checkpoint_file)
            print("✅ Checkpoint cleared (backtest complete)")

        # Display signals
        if signals_found > 0:
            self._display_signals()
        else:
            print("\n❌ NO SIGNALS FOUND")
            print("\nPossible reasons:")
            print("  - Strategy criteria too strict")
            print("  - Market in downtrend/consolidation")
            print("  - No breakouts during test period")

    def _display_signals(self):
        """Display all found signals"""
        results_path = Path(self.results_file)

        if not results_path.exists():
            return

        with open(self.results_file, 'r') as f:
            signals = json.load(f)

        print(f"\n🎯 {len(signals)} TRADING SIGNALS FOUND:\n")

        for i, sig in enumerate(signals, 1):
            print(f"{i}. {sig['symbol']}")
            print(f"   Entry: ₹{sig['entry_price']:.2f}")
            print(f"   Stop: ₹{sig['stop_loss']:.2f}")
            print(f"   Target: ₹{sig['target']:.2f}")
            print(f"   R:R: 1:{sig['risk_reward_ratio']:.2f}")
            print(f"   Strength: {sig['strength_score']:.1f}/100")
            print(f"   Beta: {sig['beta']:.2f}")
            if sig.get('adx'):
                print(f"   ADX: {sig['adx']:.1f}")
            if sig.get('rs_30d'):
                print(f"   RS 30d: {sig['rs_30d']:.2f}x ({sig.get('rs_trend', 'N/A')})")
            print(f"   Confluences ({len(sig['confluences'])}): {', '.join(sig['confluences'])}")
            print()


def load_nse_symbols() -> List[str]:
    """Load NSE symbols from clean stock list (bonds/debt removed)"""
    symbols_file = Path(__file__).parent / "agents/backtesting/symbol_lists/nse_bse_clean_stocks_nse_only.txt"

    with open(symbols_file, 'r') as f:
        symbols = [line.strip().replace('.NS', '') for line in f if '.NS' in line.strip()]

    return symbols


def main():
    """Run batched backtest"""

    print("\n" + "=" * 70)
    print("  BATCHED MULTI-TIMEFRAME BREAKOUT BACKTEST - ANGEL ONE")
    print("=" * 70)
    print()

    # Initialize backtester
    bt = BatchedAngelBacktester(
        rate_limit_delay=2.0  # 2 seconds between requests
    )

    # Load symbols
    symbols = load_nse_symbols()
    print(f"📋 Loaded {len(symbols)} NSE symbols")

    # Estimate time
    estimated_time_hours = (len(symbols) * 2.0) / 3600
    print(f"⏱️  Estimated time: {estimated_time_hours:.1f} hours")
    print(f"   (Can pause/resume using Ctrl+C)")
    print()

    # Run backtest
    bt.run_batch(
        symbols=symbols,
        start_date="2022-01-01",
        end_date="2024-10-31",  # FIXED: Changed from 2024-11-01 to avoid look-ahead bias
        batch_size=50
    )

    print("\n✅ Backtest complete!")


if __name__ == '__main__':
    main()
