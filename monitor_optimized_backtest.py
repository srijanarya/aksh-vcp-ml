#!/usr/bin/env python3
"""Monitor optimized backtest progress"""

import json
import os
from datetime import datetime

print("="*80)
print("OPTIMIZED BACKTEST MONITOR")
print("="*80)
print()

# Check if backtest is running
import subprocess
result = subprocess.run(
    ["ps", "aux"],
    capture_output=True,
    text=True
)

backtest_running = "run_optimized_backtest_with_cache.py" in result.stdout

if backtest_running:
    print("✅ Backtest is RUNNING")
else:
    print("❌ Backtest is NOT running")

print()

# Check cache stats
from src.data.historical_data_cache import HistoricalDataCache

cache = HistoricalDataCache()
cache_stats = cache.get_stats()

print("📦 CACHE STATUS:")
print(f"   Files cached: {cache_stats['file_count']}")
print(f"   Total size: {cache_stats['total_size_mb']:.2f} MB")
print()

# Check checkpoint
checkpoint_file = "/tmp/optimized_backtest_checkpoint.json"
if os.path.exists(checkpoint_file):
    with open(checkpoint_file, 'r') as f:
        checkpoint = json.load(f)

    print("📊 BACKTEST PROGRESS:")
    processed = len(checkpoint.get('processed_symbols', []))
    total = checkpoint.get('total', 5139)
    signals = len(checkpoint.get('signals', []))
    errors = checkpoint.get('errors', 0)

    progress_pct = (processed / total * 100) if total > 0 else 0

    print(f"   Progress: {processed}/{total} ({progress_pct:.1f}%)")
    print(f"   Signals found: {signals}")
    print(f"   Errors: {errors}")

    if 'last_update' in checkpoint:
        print(f"   Last update: {checkpoint['last_update']}")

    if checkpoint.get('completed'):
        print("\n   ✅ BACKTEST COMPLETE!")
else:
    print("⏳ No checkpoint yet (backtest just started)")

print()

# Check signals file
signals_file = "/tmp/optimized_backtest_signals.json"
if os.path.exists(signals_file):
    with open(signals_file, 'r') as f:
        signals = json.load(f)

    print(f"📈 SIGNALS FOUND: {len(signals)}")
    if signals:
        print("\n   Latest signals:")
        for sig in signals[-3:]:
            print(f"   - {sig['symbol']}: Entry ₹{sig['entry_price']:.2f}, R:R {sig['risk_reward_ratio']:.1f}")
else:
    print("📈 No signals found yet")

print()
print("="*80)
print("\nTo view live log:")
print("  tail -f /tmp/optimized_backtest.log")
print("="*80)
