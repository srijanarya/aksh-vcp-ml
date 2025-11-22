#!/usr/bin/env python3
"""
Angel One Backtest for Yahoo-Missing Stocks

Runs backtest on the 850 stocks that Yahoo Finance couldn't find.
Runs in parallel with the Yahoo backtest.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("="*80)
print("ANGEL ONE BACKTEST - Yahoo Missing Stocks")
print("="*80)
print()
print("This will backtest the 850 stocks that Yahoo Finance couldn't find")
print("Running in parallel with Yahoo backtest for complete coverage")
print()

# Load the missing stocks list
missing_stocks_file = "/tmp/angel_missing_stocks.txt"

with open(missing_stocks_file, 'r') as f:
    missing_stocks = [line.strip() for line in f if line.strip()]

print(f"📋 Loaded {len(missing_stocks)} stocks from: {missing_stocks_file}")
print(f"   First 10: {', '.join(missing_stocks[:10])}")
print()

# Now run the batched backtest on these stocks
from backtest_angel_batched import BatchedAngelBacktester

# Initialize with separate checkpoint/results files
# INCREASED RATE LIMIT: Angel One has aggressive rate limits
# 5 seconds between stocks to avoid "Access denied because of exceeding access rate"
bt = BatchedAngelBacktester(
    checkpoint_file="/tmp/backtest_angel_missing_checkpoint.json",
    results_file="/tmp/backtest_angel_missing_signals.json",
    rate_limit_delay=5.0  # Increased from 2.0 to avoid rate limits
)

print()
print("🚀 Starting backtest on Yahoo-missing stocks...")
print()

# Run batch
bt.run_batch(
    symbols=missing_stocks,
    start_date="2022-01-01",
    end_date="2024-10-31",  # Exclusive end date (no look-ahead bias)
    batch_size=50
)

print()
print("="*80)
print("✅ Angel One backtest complete!")
print()
print("Results saved to:")
print(f"  - /tmp/backtest_angel_missing_signals.json")
print()
print("Combined with Yahoo results, you now have COMPLETE coverage!")
print("="*80)

