#!/usr/bin/env python3
"""
Test Indicator Confluence Detection

Demonstrates the new research-backed confluence system with real market data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yfinance as yf
import pandas as pd
from strategies.indicator_confluence import IndicatorConfluence, ConfluenceZone


def fetch_test_data(symbol: str = "TATAMOTORS.NS", period: str = "6mo") -> pd.DataFrame:
    """Fetch test data from Yahoo Finance"""
    print(f"Fetching data for {symbol}...")
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period)

    if data.empty:
        raise ValueError(f"No data fetched for {symbol}")

    # Normalize column names
    data.columns = [col.lower() for col in data.columns]
    print(f"✅ Fetched {len(data)} bars\n")

    return data


def demonstrate_confluence_detection():
    """Demonstrate confluence detection with real data"""

    print("="*80)
    print("🔍 INDICATOR CONFLUENCE DETECTION TEST")
    print("="*80)
    print("\nThis demonstrates the NEW research-backed confluence system:")
    print("- Proper indicator confluence (not just timeframe confluence)")
    print("- Research-backed weights (VWAP: 30, Camarilla: 27, Fibonacci: 8-18)")
    print("- Cross-timeframe multiplier: 1.75x")
    print("- Confluence tolerance: 1.5% (tighter = better)")
    print("="*80 + "\n")

    # Fetch data
    data = fetch_test_data("TATAMOTORS.NS", period="6mo")
    current_price = data['close'].iloc[-1]

    print(f"📊 Stock: TATAMOTORS.NS")
    print(f"Current Price: ₹{current_price:.2f}")
    print(f"Date: {data.index[-1].strftime('%Y-%m-%d')}\n")

    # Initialize confluence detector
    detector = IndicatorConfluence(confluence_tolerance=0.015)  # 1.5%

    # Detect confluences
    print("-" * 80)
    print("🔎 DETECTING CONFLUENCES (Daily Timeframe)")
    print("-" * 80)

    confluences = detector.detect_all_confluences(
        data=data,
        current_price=current_price,
        timeframe='daily',
        hours_since_open=None,  # Not intraday
        volume_ratio=1.0,
        is_trending=True  # Assume trending for Fibonacci boost
    )

    print(f"\n✅ Found {len(confluences)} confluence zones\n")

    # Display top 10 confluences
    print("="*80)
    print("TOP 10 CONFLUENCE ZONES (by weighted score)")
    print("="*80)

    for i, conf in enumerate(confluences[:10], 1):
        print(f"\n{'─'*80}")
        print(f"#{i} CONFLUENCE ZONE - ₹{conf.price_level:.2f}")
        print(f"{'─'*80}")
        print(f"Direction: {conf.direction.upper()}")
        print(f"Distance from current: {abs(conf.price_level - current_price) / current_price * 100:.2f}%")
        print(f"")
        print(f"📊 Strength Metrics:")
        print(f"   Confluence Count: {conf.confluence_count} indicators")
        print(f"   Total Weight: {conf.total_weight:.1f} points")
        print(f"   Weighted Score: {conf.weighted_score:.1f} points ⭐")
        print(f"   Timeframes: {', '.join(conf.timeframes)}")
        print(f"   Has Crossover: {'YES ✅' if conf.has_crossover else 'No'}")
        print(f"")
        print(f"📋 Indicators at this level:")

        for ind in conf.indicators:
            print(f"   • {ind.indicator_name:30s} | Weight: {ind.weight:5.1f} | TF: {ind.timeframe}")

    # Find key support/resistance
    print("\n" + "="*80)
    print("🎯 KEY LEVELS FOR TRADING")
    print("="*80)

    nearest_support = detector.get_nearest_confluence(
        confluences, current_price, direction='support', max_distance_pct=0.10
    )

    nearest_resistance = detector.get_nearest_confluence(
        confluences, current_price, direction='resistance', max_distance_pct=0.10
    )

    if nearest_support:
        distance_pct = (current_price - nearest_support.price_level) / current_price * 100
        print(f"\n🛡️  NEAREST SUPPORT: ₹{nearest_support.price_level:.2f}")
        print(f"   Distance: {distance_pct:.2f}% below")
        print(f"   Strength: {nearest_support.weighted_score:.1f} points")
        print(f"   {nearest_support.confluence_count} indicators:")
        for ind in nearest_support.indicators:
            print(f"      • {ind.indicator_name}")

    if nearest_resistance:
        distance_pct = (nearest_resistance.price_level - current_price) / current_price * 100
        print(f"\n⚔️  NEAREST RESISTANCE: ₹{nearest_resistance.price_level:.2f}")
        print(f"   Distance: {distance_pct:.2f}% above")
        print(f"   Strength: {nearest_resistance.weighted_score:.1f} points")
        print(f"   {nearest_resistance.confluence_count} indicators:")
        for ind in nearest_resistance.indicators:
            print(f"      • {ind.indicator_name}")

    # Comparison with old system
    print("\n" + "="*80)
    print("📊 COMPARISON: NEW vs OLD CONFLUENCE LOGIC")
    print("="*80)

    print("\n❌ OLD SYSTEM (Incorrect):")
    print("   - Only checked S/R zones from multiple timeframes")
    print("   - Example: Weekly S/R + Daily S/R at same price = confluence")
    print("   - Missing: MAs, VWAP, Fibonacci, Camarilla, Crossovers")

    print("\n✅ NEW SYSTEM (Research-Backed):")
    print("   - Checks ALL indicators: MAs, VWAP, Fib, Camarilla, S/R, Crossovers")
    print("   - Example: Daily 50MA + VWAP + Support Zone at ₹1150 = 3-indicator confluence")
    print("   - Weighted by research (VWAP: 30, Fibonacci standalone: 8)")
    print("   - Cross-timeframe multiplier: 1.75x")

    print("\n📈 Expected Improvements:")
    print("   - Better stop placement (below strong support confluences)")
    print("   - Better target placement (before resistance confluences)")
    print("   - Higher win rate (+4-7% expected)")
    print("   - Fewer false signals")

    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80)

    return confluences


if __name__ == '__main__':
    try:
        confluences = demonstrate_confluence_detection()
        print(f"\n✅ Successfully detected {len(confluences)} confluence zones!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
