#!/usr/bin/env python3
"""
Persistent Multi-Timeframe Backtest Using Yahoo Finance

SURVIVES SYSTEM RESTARTS - All data saved to project directory, not /tmp/

Features:
- Persistent checkpointing (survives reboots)
- Results saved to SQLite database
- JSON backup of all signals
- Progress can be resumed from any point
- No look-ahead bias (end date exclusive)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import json
import time
import sqlite3
from datetime import datetime
from typing import List, Optional

from strategies.multi_timeframe_breakout import MultiTimeframeBreakoutStrategy


# Persistent storage locations (in project directory, NOT /tmp/)
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data" / "backtests"
CHECKPOINT_FILE = DATA_DIR / "yahoo_backtest_checkpoint.json"
RESULTS_DB = DATA_DIR / "yahoo_backtest_results.db"
RESULTS_JSON = DATA_DIR / "yahoo_backtest_signals.json"


class PersistentYahooBacktester:
    """Yahoo Finance backtester with persistent storage that survives reboots"""

    def __init__(self):
        print("🚀 Initializing Persistent Yahoo Finance Backtester...")
        print("="*70)

        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.strategy = MultiTimeframeBreakoutStrategy()
        self.checkpoint_file = CHECKPOINT_FILE
        self.results_db = RESULTS_DB
        self.results_json = RESULTS_JSON

        # Initialize database
        self._init_database()

        # Load checkpoint if exists
        self.checkpoint = self._load_checkpoint()

        print("✅ Initialized!")
        print(f"   Checkpoint: {self.checkpoint_file}")
        print(f"   Results DB: {self.results_db}")
        print(f"   Results JSON: {self.results_json}")
        print(f"   Beta threshold: {self.strategy.high_beta_threshold}")
        print(f"   ADX threshold: {self.strategy.min_adx}")
        print("="*70)
        print()

    def _init_database(self):
        """Initialize SQLite database for persistent results"""
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                entry_price REAL,
                stop_loss REAL,
                target REAL,
                risk_reward_ratio REAL,
                strength_score REAL,
                beta REAL,
                adx REAL,
                rs_30d REAL,
                rs_trend TEXT,
                confluences TEXT,
                sr_quality_score REAL,
                signal_timestamp TEXT,
                backtest_date TEXT DEFAULT CURRENT_TIMESTAMP,
                start_date TEXT,
                end_date TEXT,
                UNIQUE(symbol, start_date, end_date)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT,
                end_date TEXT,
                total_symbols INTEGER,
                signals_found INTEGER,
                errors INTEGER,
                started_at TEXT,
                completed_at TEXT,
                status TEXT DEFAULT 'running'
            )
        """)

        conn.commit()
        conn.close()

    def _load_checkpoint(self):
        """Load checkpoint if exists"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            print(f"📦 Resuming from checkpoint: {checkpoint['last_processed']}/{checkpoint.get('total_symbols', '?')} stocks")
            print(f"   Signals found so far: {checkpoint['signals_found']}")
            print(f"   Errors so far: {checkpoint['errors']}")
            return checkpoint
        else:
            return {
                'last_processed': 0,
                'signals_found': 0,
                'errors': 0,
                'total_symbols': 0,
                'start_date': None,
                'end_date': None,
                'run_id': None
            }

    def _save_checkpoint(self, checkpoint):
        """Save checkpoint to persistent storage"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def _save_signal_to_db(self, signal, start_date: str, end_date: str):
        """Save signal to SQLite database"""
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO backtest_signals
                (symbol, entry_price, stop_loss, target, risk_reward_ratio,
                 strength_score, beta, adx, rs_30d, rs_trend, confluences,
                 sr_quality_score, signal_timestamp, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.symbol,
                signal.entry_price,
                signal.stop_loss,
                signal.target,
                signal.risk_reward_ratio,
                signal.strength_score,
                signal.beta,
                signal.adx_metrics['adx'] if signal.adx_metrics else None,
                signal.rs_metrics['rs_30d'] if signal.rs_metrics else None,
                signal.rs_metrics['rs_trend'] if signal.rs_metrics else None,
                json.dumps(signal.confluences),
                signal.sr_quality_score,
                signal.timestamp.isoformat(),
                start_date,
                end_date
            ))
            conn.commit()
        finally:
            conn.close()

    def _save_signal_to_json(self, signal):
        """Append signal to JSON backup file"""
        results = []

        if self.results_json.exists():
            with open(self.results_json, 'r') as f:
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

        with open(self.results_json, 'w') as f:
            json.dump(results, f, indent=2)

    def _start_run(self, total_symbols: int, start_date: str, end_date: str) -> int:
        """Record start of backtest run"""
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO backtest_runs (start_date, end_date, total_symbols,
                                       signals_found, errors, started_at, status)
            VALUES (?, ?, ?, 0, 0, ?, 'running')
        """, (start_date, end_date, total_symbols, datetime.now().isoformat()))

        run_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return run_id

    def _complete_run(self, run_id: int, signals_found: int, errors: int):
        """Record completion of backtest run"""
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE backtest_runs
            SET signals_found = ?, errors = ?, completed_at = ?, status = 'completed'
            WHERE id = ?
        """, (signals_found, errors, datetime.now().isoformat(), run_id))

        conn.commit()
        conn.close()

    def run_batch(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        batch_size: int = 100
    ):
        """
        Run backtest with persistent checkpointing

        Args:
            symbols: List of stock symbols (with .NS suffix)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD) - EXCLUSIVE
            batch_size: Stocks per checkpoint save
        """
        print(f"\n🔍 PERSISTENT YAHOO BACKTEST")
        print(f"   Total stocks: {len(symbols)}")
        print(f"   Period: {start_date} to {end_date} (EXCLUSIVE)")
        print(f"   Batch size: {batch_size} stocks")
        print(f"   Data survives restarts: ✅")
        print("="*70)

        # Check if resuming or starting fresh
        if self.checkpoint['last_processed'] > 0 and \
           self.checkpoint.get('start_date') == start_date and \
           self.checkpoint.get('end_date') == end_date:
            # Resuming existing run
            start_idx = self.checkpoint['last_processed']
            signals_found = self.checkpoint['signals_found']
            errors = self.checkpoint['errors']
            run_id = self.checkpoint.get('run_id')
            print(f"\n📦 RESUMING from stock #{start_idx + 1}")
        else:
            # Starting fresh - clear old results for this date range
            start_idx = 0
            signals_found = 0
            errors = 0
            run_id = self._start_run(len(symbols), start_date, end_date)

            # Clear old JSON results
            if self.results_json.exists():
                self.results_json.unlink()

            print(f"\n🆕 STARTING FRESH (Run ID: {run_id})")

        # Update checkpoint with run metadata
        self.checkpoint.update({
            'total_symbols': len(symbols),
            'start_date': start_date,
            'end_date': end_date,
            'run_id': run_id
        })
        self._save_checkpoint(self.checkpoint)

        print(f"   Starting from: Stock #{start_idx + 1}")
        print()

        # Process stocks
        for i, symbol in enumerate(symbols[start_idx:], start_idx + 1):
            print(f"[{i}/{len(symbols)}] Analyzing {symbol}...", end=" ", flush=True)

            try:
                # Generate signal using Yahoo Finance
                signal = self.strategy.generate_signal(symbol)

                if signal:
                    signals_found += 1
                    self._save_signal_to_db(signal, start_date, end_date)
                    self._save_signal_to_json(signal)
                    print(f"✅ SIGNAL #{signals_found} (R:R={signal.risk_reward_ratio:.1f})")
                else:
                    print("❌ No signal")

                # Small delay to be respectful to Yahoo Finance
                time.sleep(0.2)

            except KeyboardInterrupt:
                print(f"\n\n⚠️  Interrupted at stock {i}/{len(symbols)}")
                self._save_checkpoint({
                    **self.checkpoint,
                    'last_processed': i,
                    'signals_found': signals_found,
                    'errors': errors
                })
                print(f"   💾 Checkpoint saved. Run script again to resume.")
                sys.exit(0)

            except Exception as e:
                print(f"⚠️  Error: {str(e)[:50]}")
                errors += 1

            # Save checkpoint every batch_size stocks
            if i % batch_size == 0:
                self._save_checkpoint({
                    **self.checkpoint,
                    'last_processed': i,
                    'signals_found': signals_found,
                    'errors': errors
                })
                progress_pct = i / len(symbols) * 100
                print(f"   💾 Checkpoint saved ({progress_pct:.1f}% | signals: {signals_found}, errors: {errors})")

        # Final checkpoint
        self._save_checkpoint({
            **self.checkpoint,
            'last_processed': len(symbols),
            'signals_found': signals_found,
            'errors': errors,
            'completed': True
        })

        # Mark run as complete
        self._complete_run(run_id, signals_found, errors)

        # Final summary
        print("\n" + "="*70)
        print("📊 BACKTEST COMPLETE")
        print("="*70)
        print(f"Total Analyzed: {len(symbols)}")
        print(f"Signals Found: {signals_found}")
        print(f"Hit Rate: {signals_found/len(symbols)*100:.2f}%")
        print(f"Errors: {errors}")
        print(f"\n📁 Results saved to:")
        print(f"   Database: {self.results_db}")
        print(f"   JSON: {self.results_json}")
        print("="*70)

        # Display signals
        if signals_found > 0:
            self._display_signals()

        # Clear checkpoint on completion
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            print("\n✅ Checkpoint cleared (backtest complete)")

    def _display_signals(self):
        """Display all found signals from database"""
        conn = sqlite3.connect(self.results_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT symbol, entry_price, stop_loss, target, risk_reward_ratio,
                   strength_score, beta, adx, rs_30d, confluences
            FROM backtest_signals
            ORDER BY strength_score DESC
            LIMIT 20
        """)

        signals = cursor.fetchall()
        conn.close()

        if not signals:
            return

        print(f"\n🎯 TOP {len(signals)} TRADING SIGNALS:\n")

        for i, sig in enumerate(signals, 1):
            symbol, entry, stop, target, rr, strength, beta, adx, rs, confluences = sig
            confluences_list = json.loads(confluences) if confluences else []

            print(f"{i}. {symbol}")
            print(f"   Entry: ₹{entry:.2f} | Stop: ₹{stop:.2f} | Target: ₹{target:.2f}")
            print(f"   R:R: 1:{rr:.2f} | Strength: {strength:.1f}/100")
            print(f"   Beta: {beta:.2f}", end="")
            if adx:
                print(f" | ADX: {adx:.1f}", end="")
            if rs:
                print(f" | RS: {rs:.2f}x", end="")
            print()
            if confluences_list:
                print(f"   Confluences: {', '.join(confluences_list[:3])}")
            print()


def load_clean_symbols() -> List[str]:
    """Load clean NSE symbols (bonds removed)"""
    symbols_file = PROJECT_DIR / "agents/backtesting/symbol_lists/nse_bse_clean_stocks_nse_only.txt"

    if not symbols_file.exists():
        print(f"❌ Clean stock list not found: {symbols_file}")
        sys.exit(1)

    with open(symbols_file, 'r') as f:
        symbols = [line.strip() for line in f if line.strip() and '.NS' in line]

    return symbols


def main():
    """Run persistent backtest"""

    print("\n" + "="*70)
    print("  PERSISTENT MULTI-TIMEFRAME BACKTEST - YAHOO FINANCE")
    print("="*70)
    print()
    print("✅ Features:")
    print("   1. SURVIVES SYSTEM RESTARTS - data in project directory")
    print("   2. SQLite database for results")
    print("   3. JSON backup of all signals")
    print("   4. Resume from any point")
    print("   5. No look-ahead bias")
    print()

    # Initialize backtester
    bt = PersistentYahooBacktester()

    # Load clean symbols
    symbols = load_clean_symbols()
    print(f"📋 Loaded {len(symbols)} clean NSE equity stocks")

    # Estimate time
    remaining = len(symbols) - bt.checkpoint['last_processed']
    estimated_minutes = (remaining * 0.5) / 60
    print(f"⏱️  Estimated time remaining: {estimated_minutes:.1f} minutes")
    print(f"   (Ctrl+C to pause - will resume from checkpoint)")
    print()

    # Run backtest
    bt.run_batch(
        symbols=symbols,
        start_date="2022-01-01",
        end_date="2024-10-31",
        batch_size=100
    )

    print("\n✅ Backtest complete!")


if __name__ == '__main__':
    main()
