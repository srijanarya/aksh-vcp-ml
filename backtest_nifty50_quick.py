#!/usr/bin/env python3
"""
Quick NIFTY 50 Backtest with Stage 1 Relaxed Parameters

This script tests the relaxed strategy on just 50 stocks for quick validation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import time
from datetime import datetime

# Import our components
from src.data.angel_one_client import AngelOneClient
from strategies.multi_timeframe_breakout import MultiTimeframeBreakoutStrategy

# NIFTY 50 stocks (as of Nov 2024)
NIFTY_50_SYMBOLS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BHARTIARTL", "BPCL",
    "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH", "HDFC", "HDFCBANK",
    "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "INDUSINDBK", "INFY", "ITC", "JSWSTEEL", "KOTAKBANK",
    "LT", "M&M", "MARUTI", "NESTLEIND", "NTPC",
    "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN",
    "SUNPHARMA", "TATACONSUM", "TATAMOTORS", "TATASTEEL", "TCS",
    "TECHM", "TITAN", "ULTRACEMCO", "UPL", "WIPRO"
]

def main():
    print("="*70)
    print("NIFTY 50 QUICK TEST - STAGE 1 RELAXED PARAMETERS")
    print("="*70)
    print()
    print("Parameters:")
    print("  Beta threshold: 0.9 (relaxed from 1.0)")
    print("  ADX threshold: 18 (relaxed from 20)")
    print("  S/R quality: 50 (relaxed from 60)")
    print("  Min confluences: 2 of 7")
    print()
    print(f"Testing {len(NIFTY_50_SYMBOLS)} stocks...")
    print("="*70)
    print()

    # Initialize strategy
    strategy = MultiTimeframeBreakoutStrategy()

    # Verify parameters were updated
    print("Loaded strategy parameters:")
    print(f"  Beta: {strategy.high_beta_threshold}")
    print(f"  ADX: {strategy.min_adx}")
    print(f"  S/R: {strategy.min_sr_quality}")
    print(f"  Confluences: {strategy.min_confluences}")
    print()

    signals_found = []
    errors = 0

    start_time = time.time()

    for i, symbol in enumerate(NIFTY_50_SYMBOLS, 1):
        print(f"[{i}/{len(NIFTY_50_SYMBOLS)}] Testing {symbol}...", end="")

        try:
            # Generate signal using Yahoo Finance (faster for quick test)
            signal = strategy.generate_signal(symbol + ".NS")

            if signal:
                signals_found.append({
                    'symbol': symbol,
                    'entry': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'target': signal.target,
                    'risk_reward': signal.risk_reward_ratio,
                    'strength': signal.strength_score,
                    'beta': signal.beta,
                    'adx': signal.adx_metrics['adx'] if signal.adx_metrics else None,
                    'rs_30d': signal.rs_metrics['rs_30d'] if signal.rs_metrics else None,
                    'confluences': len(signal.confluences)
                })
                print(f" ✅ SIGNAL FOUND! (R:R={signal.risk_reward_ratio:.1f})")
            else:
                print(" ❌ No signal")

            # Small delay to avoid rate limits
            time.sleep(0.5)

        except Exception as e:
            print(f" ⚠️ Error: {str(e)[:50]}")
            errors += 1
            time.sleep(1)  # Extra delay on error

    elapsed = time.time() - start_time

    print()
    print("="*70)
    print("QUICK TEST RESULTS")
    print("="*70)
    print(f"Time taken: {elapsed:.1f} seconds")
    print(f"Stocks tested: {len(NIFTY_50_SYMBOLS)}")
    print(f"Signals found: {len(signals_found)}")
    print(f"Hit rate: {len(signals_found)/len(NIFTY_50_SYMBOLS)*100:.1f}%")
    print(f"Errors: {errors}")
    print()

    if signals_found:
        print("SIGNALS DETAILS:")
        print("-"*70)
        for sig in signals_found:
            print(f"\n{sig['symbol']}:")
            print(f"  Entry: ₹{sig['entry']:.2f}")
            print(f"  Stop: ₹{sig['stop_loss']:.2f}")
            print(f"  Target: ₹{sig['target']:.2f}")
            print(f"  R:R: 1:{sig['risk_reward']:.1f}")
            print(f"  Beta: {sig['beta']:.2f}")
            if sig['adx']:
                print(f"  ADX: {sig['adx']:.1f}")
            if sig['rs_30d']:
                print(f"  RS 30d: {sig['rs_30d']:.2f}x")
            print(f"  Confluences: {sig['confluences']}")
            print(f"  Strength: {sig['strength']:.1f}/100")

        # Save results
        with open("/tmp/nifty50_stage1_results.json", "w") as f:
            json.dump(signals_found, f, indent=2)
        print(f"\nResults saved to /tmp/nifty50_stage1_results.json")
    else:
        print("❌ NO SIGNALS FOUND WITH STAGE 1 RELAXATION")
        print()
        print("This suggests we need Stage 2 relaxation:")
        print("  Beta: 0.8")
        print("  ADX: 15")
        print("  S/R: 40")

    print()
    print("="*70)
    print("RECOMMENDATION:")
    if len(signals_found) >= 2:
        print("✅ Stage 1 relaxation working! Found", len(signals_found), "signals.")
        print("   Proceed with full 5,574 stock backtest.")
    elif len(signals_found) == 1:
        print("⚠️ Only 1 signal. Consider Stage 2 relaxation.")
    else:
        print("❌ No signals. Move to Stage 2 relaxation immediately.")
    print("="*70)

if __name__ == "__main__":
    main()