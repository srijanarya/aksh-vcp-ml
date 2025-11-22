#!/usr/bin/env python3
"""
Monitor the progress of the running backtest
"""

import json
import time
from pathlib import Path

def monitor_backtest():
    checkpoint_file = Path("/tmp/backtest_checkpoint.json")
    signals_file = Path("/tmp/backtest_signals.json")

    print("="*70)
    print("BACKTEST MONITOR - STAGE 1 RELAXED PARAMETERS")
    print("="*70)
    print()
    print("Parameters:")
    print("  Beta: 0.9 (relaxed from 1.0)")
    print("  ADX: 18 (relaxed from 20)")
    print("  S/R: 50 (relaxed from 60)")
    print()
    print("Monitoring progress...")
    print("-"*70)
    print()

    last_processed = 0

    while True:
        try:
            # Check checkpoint
            if checkpoint_file.exists():
                with open(checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)

                current = checkpoint.get('last_processed', 0)
                signals = checkpoint.get('signals_found', 0)
                errors = checkpoint.get('errors', 0)

                if current != last_processed:
                    progress = (current / 5574) * 100
                    rate = signals / current if current > 0 else 0
                    projected = int(rate * 5574)

                    print(f"\r[{current}/5574] {progress:.1f}% | "
                          f"Signals: {signals} | "
                          f"Rate: {rate*100:.2f}% | "
                          f"Projected: ~{projected} | "
                          f"Errors: {errors}", end="", flush=True)

                    last_processed = current

            # Check if signals file exists and show recent signals
            if signals_file.exists():
                with open(signals_file, 'r') as f:
                    all_signals = json.load(f)
                    if len(all_signals) > signals:
                        print(f"\n   NEW SIGNAL: {all_signals[-1]['symbol']}")

            # Check if complete
            if last_processed >= 5574:
                print("\n\n" + "="*70)
                print("BACKTEST COMPLETE!")
                print("="*70)

                if signals_file.exists():
                    with open(signals_file, 'r') as f:
                        final_signals = json.load(f)

                    print(f"Total Signals Found: {len(final_signals)}")
                    print(f"Hit Rate: {len(final_signals)/5574*100:.2f}%")
                    print()
                    print("Top 5 Signals by Strength:")
                    sorted_signals = sorted(final_signals,
                                          key=lambda x: x.get('strength_score', 0),
                                          reverse=True)[:5]
                    for i, sig in enumerate(sorted_signals, 1):
                        print(f"  {i}. {sig['symbol']} - Strength: {sig['strength_score']:.1f}")

                break

            time.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_backtest()