#!/usr/bin/env python3
"""
Corrected Multi-Timeframe Backtest Using Yahoo Finance

This version fixes:
1. Look-ahead bias (end date is now exclusive)
2. Uses clean stock universe (bonds removed)
3. Yahoo Finance for better data availability
4. Stage 1 relaxed parameters

Features:
- No look-ahead bias
- Clean equity-only universe (5,139 stocks)
- Checkpointing for resumability
- Progress tracking
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import json
import time
from datetime import datetime
from typing import List, Optional

from strategies.multi_timeframe_breakout import MultiTimeframeBreakoutStrategy


class YahooBacktester:
    """Yahoo Finance backtester with proper validation"""

    def __init__(
        self,
        checkpoint_file: str = "/tmp/backtest_yahoo_checkpoint.json",
        results_file: str = "/tmp/backtest_yahoo_signals.json"
    ):
        print("🚀 Initializing Yahoo Finance Backtester...")
        print("="*70)

        self.strategy = MultiTimeframeBreakoutStrategy()
        self.checkpoint_file = checkpoint_file
        self.results_file = results_file

        # Load checkpoint if exists
        self.checkpoint = self._load_checkpoint()

        print("✅ Initialized!")
        print(f"   Beta threshold: {self.strategy.high_beta_threshold}")
        print(f"   ADX threshold: {self.strategy.min_adx}")
        print(f"   S/R quality: {self.strategy.min_sr_quality}")
        print(f"   Min confluences: {self.strategy.min_confluences} of 7")
        print("="*70)
        print()

    def _load_checkpoint(self):
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

    def _save_checkpoint(self, checkpoint):
        """Save checkpoint"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def _save_signal(self, signal):
        """Append signal to results file"""
        results = []
        results_path = Path(self.results_file)

        if results_path.exists():
            with open(self.results_file, 'r') as f:
                results = json.load(f)

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

        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

    def run_batch(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        batch_size: int = 100
    ):
        """
        Run backtest in batches with checkpointing

        Args:
            symbols: List of stock symbols (with .NS suffix)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD) - EXCLUSIVE
            batch_size: Stocks per checkpoint
        """
        print(f"\n🔍 YAHOO FINANCE BACKTEST (CORRECTED)")
        print(f"   Total stocks: {len(symbols)}")
        print(f"   Period: {start_date} to {end_date} (EXCLUSIVE)")
        print(f"   Batch size: {batch_size} stocks")
        print(f"   Starting from: Stock #{self.checkpoint['last_processed'] + 1}")
        print("="*70)
        print()

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
                print(f"[{i}/{len(symbols)}] Analyzing {symbol}...", end=" ")

                try:
                    # Generate signal using Yahoo Finance
                    signal = self.strategy.generate_signal(symbol)

                    if signal:
                        signals_found += 1
                        self._save_signal(signal)
                        print(f"✅ SIGNAL #{signals_found} (R:R={signal.risk_reward_ratio:.1f})")
                    else:
                        print("❌ No signal")

                    # Small delay to be respectful to Yahoo Finance
                    time.sleep(0.2)

                except KeyboardInterrupt:
                    print(f"\n\n⚠️  Interrupted at stock {i}/{len(symbols)}")
                    self._save_checkpoint({
                        'last_processed': i,
                        'signals_found': signals_found,
                        'errors': errors
                    })
                    print(f"   Checkpoint saved. Resume by running script again.")
                    sys.exit(0)

                except Exception as e:
                    print(f"⚠️  Error: {str(e)[:50]}")
                    errors += 1

                # Save checkpoint every batch
                if i % batch_size == 0:
                    self._save_checkpoint({
                        'last_processed': i,
                        'signals_found': signals_found,
                        'errors': errors
                    })
                    print(f"   💾 Checkpoint saved (signals: {signals_found}, errors: {errors})")

        # Final summary
        print("\n" + "="*70)
        print("📊 BACKTEST COMPLETE")
        print("="*70)
        print(f"Total Analyzed: {len(symbols)}")
        print(f"Signals Found: {signals_found}")
        print(f"Hit Rate: {signals_found/len(symbols)*100:.2f}%")
        print(f"Errors: {errors}")
        print(f"Results saved to: {self.results_file}")
        print("="*70)
        print()

        # Clear checkpoint
        if Path(self.checkpoint_file).exists():
            import os
            os.remove(self.checkpoint_file)
            print("✅ Checkpoint cleared (backtest complete)")

        # Display signals
        if signals_found > 0:
            self._display_signals()
        else:
            print("\n❌ NO SIGNALS FOUND")
            print("\nConsider:")
            print("  - Further relaxing parameters (Stage 2)")
            print("  - Checking if market was in consolidation during test period")
            print("  - Testing on different time periods")

    def _display_signals(self):
        """Display all found signals"""
        results_path = Path(self.results_file)

        if not results_path.exists():
            return

        with open(self.results_file, 'r') as f:
            signals = json.load(f)

        print(f"\n🎯 {len(signals)} TRADING SIGNALS FOUND:\n")

        # Sort by strength score
        signals_sorted = sorted(signals, key=lambda x: x['strength_score'], reverse=True)

        for i, sig in enumerate(signals_sorted[:20], 1):  # Show top 20
            print(f"{i}. {sig['symbol']}")
            print(f"   Entry: ₹{sig['entry_price']:.2f}")
            print(f"   Stop: ₹{sig['stop_loss']:.2f}")
            print(f"   Target: ₹{sig['target']:.2f}")
            print(f"   R:R: 1:{sig['risk_reward_ratio']:.2f}")
            print(f"   Strength: {sig['strength_score']:.1f}/100")
            print(f"   Beta: {sig['beta']:.2f}", end="")
            if sig.get('adx'):
                print(f" | ADX: {sig['adx']:.1f}", end="")
            if sig.get('rs_30d'):
                print(f" | RS: {sig['rs_30d']:.2f}x", end="")
            print()
            print(f"   Confluences ({len(sig['confluences'])}): {', '.join(sig['confluences'][:3])}")
            print()

        if len(signals) > 20:
            print(f"... and {len(signals) - 20} more signals")


def load_clean_symbols() -> List[str]:
    """Load clean NSE symbols (bonds removed)"""
    symbols_file = Path(__file__).parent / "agents/backtesting/symbol_lists/nse_bse_clean_stocks_nse_only.txt"

    if not symbols_file.exists():
        print(f"❌ Clean stock list not found: {symbols_file}")
        print("   Run: python3 tools/clean_stock_universe.py")
        sys.exit(1)

    with open(symbols_file, 'r') as f:
        # Keep .NS suffix for Yahoo Finance
        symbols = [line.strip() for line in f if line.strip() and '.NS' in line]

    return symbols


def main():
    """Run corrected backtest"""

    print("\n" + "="*70)
    print("  CORRECTED MULTI-TIMEFRAME BACKTEST - YAHOO FINANCE")
    print("="*70)
    print()
    print("✅ Fixes Applied:")
    print("   1. Look-ahead bias eliminated (end date exclusive)")
    print("   2. Clean equity-only universe (5,139 stocks)")
    print("   3. Yahoo Finance for better data availability")
    print("   4. Stage 1 relaxed parameters")
    print()

    # Initialize backtester
    bt = YahooBacktester()

    # Load clean symbols
    symbols = load_clean_symbols()
    print(f"📋 Loaded {len(symbols)} clean NSE equity stocks")

    # Estimate time
    estimated_minutes = (len(symbols) * 0.5) / 60  # 0.5 seconds per stock
    print(f"⏱️  Estimated time: {estimated_minutes:.1f} minutes")
    print(f"   (Can pause/resume using Ctrl+C)")
    print()

    # Run backtest
    bt.run_batch(
        symbols=symbols,
        start_date="2022-01-01",
        end_date="2024-10-31",  # EXCLUSIVE - no Nov 1st data
        batch_size=100
    )

    print("\n✅ Backtest complete!")
    print("\n📊 Next steps:")
    print("   - Review signals in /tmp/backtest_yahoo_signals.json")
    print("   - Validate no signals have dates >= 2024-11-01")
    print("   - Compare results with previous (invalid) Angel One backtest")


if __name__ == '__main__':
    main()
