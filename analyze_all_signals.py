#!/usr/bin/env python3
"""
Analyze ALL backtest signals with clear timeframe explanation
"""

import json
import yfinance as yf
import pandas as pd
from datetime import datetime

print("="*80)
print("BACKTEST TIMEFRAME & SIGNAL PERFORMANCE ANALYSIS")
print("="*80)
print()
print("📅 BACKTEST SETUP:")
print("   Historical Period: January 1, 2022 → October 31, 2024")
print("   Analysis Window: 2 years, 10 months of historical data")
print("   Entry Date: October 31, 2024 (last day of backtest)")
print("   Strategy: Find stocks that showed breakout patterns on Oct 31, 2024")
print()
print("🎯 WHAT WE'RE MEASURING:")
print("   If we had entered these stocks on Oct 31, 2024,")
print("   what would our returns be TODAY (Nov 21, 2024)?")
print("   = 21 days forward performance")
print()
print("="*80)
print()

# Load signals
with open('/tmp/backtest_yahoo_signals.json', 'r') as f:
    signals = json.load(f)

print(f"📊 Total Signals Found: {len(signals)}")
print()

# Get Nifty performance for comparison
nifty = yf.Ticker("^NSEI")
nifty_data = nifty.history(start="2024-10-01", end=datetime.now().strftime("%Y-%m-%d"))
entry_date = pd.to_datetime("2024-10-31")

# Make timezone aware
if nifty_data.index.tz is not None:
    entry_date = entry_date.tz_localize(nifty_data.index.tz)

if entry_date in nifty_data.index:
    nifty_entry = nifty_data.loc[entry_date, 'Close']
    nifty_current = nifty_data['Close'].iloc[-1]
    nifty_return = ((nifty_current / nifty_entry) - 1) * 100
    print(f"📈 NIFTY 50 (Benchmark):")
    print(f"   Entry (Oct 31): {nifty_entry:.2f}")
    print(f"   Current (Nov 21): {nifty_current:.2f}")
    print(f"   Return: {nifty_return:+.2f}% in 21 days")
    print()
    print("="*80)

total_return = 0
winners = 0
losers = 0

for i, sig in enumerate(signals, 1):
    symbol = sig['symbol']
    entry_price = sig['entry_price']
    stop_loss = sig['stop_loss']
    target = sig['target']

    print(f"\n{i}. {symbol}")
    print("-" * 80)

    try:
        # Fetch current price
        stock = yf.Ticker(symbol)
        stock_data = stock.history(start="2024-10-01", end=datetime.now().strftime("%Y-%m-%d"))

        if stock_data.empty:
            print("   ❌ No data available")
            continue

        # Get company info
        info = stock.info
        company_name = info.get('longName', symbol)
        sector = info.get('sector', 'Unknown')
        market_cap = info.get('marketCap', 0)

        print(f"   Company: {company_name}")
        print(f"   Sector: {sector}")
        print(f"   Market Cap: ₹{market_cap/10000000:.2f} Cr" if market_cap > 0 else "   Market Cap: N/A")
        print()

        # Find actual entry price on Oct 31
        entry_date_sig = pd.to_datetime("2024-10-31")
        if stock_data.index.tz is not None:
            entry_date_sig = entry_date_sig.tz_localize(stock_data.index.tz)

        if entry_date_sig not in stock_data.index:
            closest_idx = stock_data.index.get_indexer([entry_date_sig], method='nearest')[0]
            entry_date_sig = stock_data.index[closest_idx]

        actual_entry = stock_data.loc[entry_date_sig, 'Close']
        current_price = stock_data['Close'].iloc[-1]

        # Calculate returns
        actual_return = ((current_price / actual_entry) - 1) * 100
        vs_target = ((current_price / target) - 1) * 100
        risk_reward = sig['risk_reward_ratio']

        print(f"   📅 ENTRY DATE: October 31, 2024")
        print(f"   💰 Entry Price: ₹{actual_entry:.2f}")
        print(f"   🎯 Target: ₹{target:.2f} (R:R = 1:{risk_reward:.1f})")
        print(f"   🛑 Stop Loss: ₹{stop_loss:.2f}")
        print()
        print(f"   📅 CURRENT DATE: November 21, 2024 (21 days later)")
        print(f"   💵 Current Price: ₹{current_price:.2f}")
        print(f"   📊 Actual Return: {actual_return:+.2f}%")

        # vs Nifty
        if 'nifty_return' in locals():
            outperformance = actual_return - nifty_return
            print(f"   🎯 vs Nifty: {outperformance:+.2f}%")

        print(f"   🎯 vs Target: {vs_target:+.2f}%", end="")
        if vs_target >= 0:
            print(" ✅ TARGET HIT!")
        elif actual_return > 0:
            print(" (Moving towards target)")
        else:
            print()

        # Status
        if actual_return > 0:
            winners += 1
            print(f"\n   ✅ WINNER")
        else:
            losers += 1
            print(f"\n   ❌ LOSER")

        # Signal quality
        print(f"\n   📊 Signal Quality:")
        print(f"      Strength Score: {sig['strength_score']:.1f}/100")
        print(f"      Beta: {sig['beta']:.2f}")
        print(f"      ADX: {sig['adx']:.1f}")
        print(f"      Confluences: {', '.join(sig['confluences'][:3])}")

        total_return += actual_return

    except Exception as e:
        print(f"   ❌ Error: {e}")

print()
print("="*80)
print("SUMMARY")
print("="*80)
print()
print(f"📊 TIMEFRAME: October 31, 2024 → November 21, 2024 (21 days)")
print(f"📈 Signals Analyzed: {len(signals)}")
print(f"✅ Winners: {winners} ({winners/len(signals)*100:.1f}%)")
print(f"❌ Losers: {losers} ({losers/len(signals)*100:.1f}%)")
print(f"💰 Average Return: {total_return/len(signals):+.2f}%")
if 'nifty_return' in locals():
    print(f"🎯 Nifty Return: {nifty_return:+.2f}%")
    print(f"📊 Average Outperformance: {(total_return/len(signals)) - nifty_return:+.2f}%")
print()
print("="*80)
print("KEY INSIGHT")
print("="*80)
print()
print("This is a FORWARD-LOOKING test:")
print("• Strategy identified breakout patterns on Oct 31, 2024")
print("• We're measuring 21-day forward returns from that date")
print("• This validates if the strategy finds stocks that CONTINUE to perform")
print("• Not a traditional backtest (which tests historical entry/exit)")
print()
print("="*80)
