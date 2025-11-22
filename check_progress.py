#!/usr/bin/env python3
"""Quick progress check for Yahoo backtest"""

import json
from pathlib import Path

checkpoint_file = "/tmp/backtest_yahoo_checkpoint.json"
results_file = "/tmp/backtest_yahoo_signals.json"

print("=" * 70)
print("BACKTEST PROGRESS CHECK")
print("=" * 70)
print()

# Check checkpoint
if Path(checkpoint_file).exists():
    with open(checkpoint_file, 'r') as f:
        checkpoint = json.load(f)
    print(f"✅ Checkpoint found")
    print(f"   Stocks analyzed: {checkpoint['last_processed']}")
    print(f"   Signals found: {checkpoint['signals_found']}")
    print(f"   Errors: {checkpoint['errors']}")
    print(f"   Progress: {checkpoint['last_processed']}/5139 ({checkpoint['last_processed']/5139*100:.1f}%)")
else:
    print("⏳ No checkpoint yet (backtest just started)")

print()

# Check results
if Path(results_file).exists():
    with open(results_file, 'r') as f:
        results = json.load(f)
    print(f"📊 Signals file exists: {len(results)} signals found so far")

    if results:
        print("\nLatest signals:")
        for i, sig in enumerate(results[-3:], 1):
            print(f"  {i}. {sig['symbol']} - Entry: ₹{sig['entry_price']:.2f}, R:R: {sig['risk_reward_ratio']:.1f}")
else:
    print("📊 No signals found yet")

print()
print("=" * 70)
