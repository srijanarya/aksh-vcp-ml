#!/usr/bin/env python3
"""
Extract stocks that failed in Yahoo backtest for Angel One retry
"""

import json

# Load checkpoint
with open('/tmp/backtest_yahoo_checkpoint.json', 'r') as f:
    checkpoint = json.load(f)

# Load signals  
try:
    with open('/tmp/backtest_yahoo_signals.json', 'r') as f:
        signals = json.load(f)
    signal_symbols = set(s['symbol'] for s in signals)
except:
    signal_symbols = set()

# Load all symbols
with open('agents/backtesting/symbol_lists/nse_bse_clean_stocks_nse_only.txt', 'r') as f:
    all_symbols = [line.strip() for line in f]

# Determine which stocks failed (no data on Yahoo)
processed = checkpoint['last_processed']
processed_symbols = set(all_symbols[:processed])

# Failed = processed but not in signals
yahoo_failed = []
for symbol in all_symbols[:processed]:
    if symbol not in signal_symbols:
        yahoo_failed.append(symbol)

print(f"Total processed: {processed}")
print(f"Signals found: {len(signal_symbols)}")
print(f"Yahoo-failed stocks: {len(yahoo_failed)}")

# Save for Angel One backtest
with open('/tmp/angel_missing_stocks.txt', 'w') as f:
    for symbol in yahoo_failed:
        f.write(f"{symbol}
")

print(f"
Saved {len(yahoo_failed)} stocks to /tmp/angel_missing_stocks.txt")
print("Ready for Angel One backtest!")
