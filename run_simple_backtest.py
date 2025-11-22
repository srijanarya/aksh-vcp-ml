#!/usr/bin/env python3
"""
Simple Backtest Runner
Tests a basic momentum strategy using available data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf

def simple_momentum_backtest():
    """Run a simple momentum backtest on top stocks"""

    print("\n" + "="*70)
    print("SIMPLE MOMENTUM STRATEGY BACKTEST")
    print("="*70)

    # Test symbols (NSE format)
    symbols = ['TCS.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS']

    # Parameters
    lookback_days = 90
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Symbols: {', '.join([s.replace('.NS', '') for s in symbols])}")
    print("\nStrategy: Buy if 20-day return > 10% and RSI < 70")
    print("-"*70)

    results = []

    for symbol in symbols:
        try:
            print(f"\nAnalyzing {symbol}...")

            # Fetch data
            stock = yf.Ticker(symbol)
            df = stock.history(start=start_date, end=end_date)

            if df.empty or len(df) < 20:
                print(f"  ⚠️  Insufficient data for {symbol}")
                continue

            # Calculate indicators
            df['Returns_20d'] = (df['Close'] / df['Close'].shift(20) - 1) * 100
            df['MA_20'] = df['Close'].rolling(20).mean()
            df['MA_50'] = df['Close'].rolling(50).mean() if len(df) >= 50 else np.nan

            # Simple RSI calculation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Latest values
            latest = df.iloc[-1]
            current_price = latest['Close']
            returns_20d = latest['Returns_20d'] if pd.notna(latest['Returns_20d']) else 0
            rsi = latest['RSI'] if pd.notna(latest['RSI']) else 50
            ma20 = latest['MA_20'] if pd.notna(latest['MA_20']) else current_price

            # Signal generation
            buy_signal = (returns_20d > 10) and (rsi < 70) and (current_price > ma20)

            # Calculate potential return (using 5-day forward looking in backtest)
            if len(df) >= 25:
                future_return = (df['Close'].iloc[-1] / df['Close'].iloc[-5] - 1) * 100
            else:
                future_return = 0

            result = {
                'symbol': symbol.replace('.NS', ''),
                'price': current_price,
                '20d_return': returns_20d,
                'rsi': rsi,
                'above_ma20': current_price > ma20,
                'signal': 'BUY' if buy_signal else 'HOLD',
                'expected_return': future_return
            }

            results.append(result)

            print(f"  Price: ₹{current_price:.2f}")
            print(f"  20-day Return: {returns_20d:.1f}%")
            print(f"  RSI: {rsi:.1f}")
            print(f"  Signal: {'🟢 ' + result['signal'] if buy_signal else '⭕ ' + result['signal']}")

        except Exception as e:
            print(f"  ❌ Error processing {symbol}: {e}")

    # Summary
    print("\n" + "="*70)
    print("BACKTEST SUMMARY")
    print("="*70)

    if results:
        buy_signals = [r for r in results if r['signal'] == 'BUY']

        print(f"\nSignals Generated:")
        print(f"  • Total Stocks Analyzed: {len(results)}")
        print(f"  • Buy Signals: {len(buy_signals)}")
        print(f"  • Hold Signals: {len(results) - len(buy_signals)}")

        if buy_signals:
            print(f"\n🟢 BUY SIGNALS:")
            for sig in buy_signals:
                print(f"  • {sig['symbol']}: ₹{sig['price']:.2f} (20d: {sig['20d_return']:.1f}%, RSI: {sig['rsi']:.1f})")

        # Performance metrics
        avg_return = np.mean([r['expected_return'] for r in results])
        print(f"\n📊 Performance Metrics:")
        print(f"  • Average Expected Return: {avg_return:.2f}%")
        print(f"  • Win Rate: {len([r for r in results if r['expected_return'] > 0])/len(results)*100:.1f}%")

    print("\n" + "="*70)
    print("Backtest complete!")
    print("="*70)

if __name__ == "__main__":
    simple_momentum_backtest()