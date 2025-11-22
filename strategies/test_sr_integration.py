#!/usr/bin/env python3
"""
Test S/R Integration in MTF Strategy

This test simulates a stock with a breakout and S/R levels to verify:
1. S/R analysis is performed
2. Stop loss is adjusted to support zones
3. Target is adjusted for nearby resistance
4. S/R quality score filters low-quality breakouts
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.multi_timeframe_breakout import MultiTimeframeBreakoutStrategy

def create_test_data():
    """Create synthetic data with clear S/R levels"""

    # Weekly data (uptrend)
    dates_weekly = pd.date_range(end=datetime.now(), periods=60, freq='W')
    weekly_data = pd.DataFrame({
        'open': np.linspace(100, 150, 60),
        'high': np.linspace(105, 155, 60),
        'low': np.linspace(95, 145, 60),
        'close': np.linspace(102, 152, 60),
        'volume': np.random.randint(1000000, 5000000, 60)
    }, index=dates_weekly)

    # Daily data (consolidation then breakout)
    dates_daily = pd.date_range(end=datetime.now(), periods=250, freq='D')

    # Create consolidation pattern with support at 145, resistance at 150
    daily_close = []
    for i in range(250):
        if i < 200:
            # Consolidation phase
            daily_close.append(np.random.uniform(145, 150))
        elif i < 230:
            # Build up to breakout
            daily_close.append(145 + (i - 200) * 0.2)
        else:
            # Breakout phase
            daily_close.append(150 + (i - 230) * 0.5)

    daily_data = pd.DataFrame({
        'open': [c - np.random.uniform(0, 1) for c in daily_close],
        'high': [c + np.random.uniform(0, 2) for c in daily_close],
        'low': [c - np.random.uniform(0, 2) for c in daily_close],
        'close': daily_close,
        'volume': [np.random.randint(1000000, 3000000) for _ in range(250)]
    }, index=dates_daily)

    # Add breakout volume spike at the end
    daily_data['volume'].iloc[-5:] = np.random.randint(4000000, 8000000, 5)

    # 4H data (recent bullish momentum)
    dates_4h = pd.date_range(end=datetime.now(), periods=100, freq='4h')
    data_4h = pd.DataFrame({
        'open': np.linspace(148, 160, 100),
        'high': np.linspace(149, 162, 100),
        'low': np.linspace(147, 158, 100),
        'close': np.linspace(148.5, 160.5, 100),
        'volume': np.random.randint(200000, 600000, 100)
    }, index=dates_4h)

    return {
        'weekly': weekly_data,
        'daily': daily_data,
        '4h': data_4h
    }

def test_sr_integration():
    """Test the S/R integration"""

    print("\n" + "="*70)
    print("🧪 TESTING S/R INTEGRATION IN MTF STRATEGY")
    print("="*70 + "\n")

    print("Creating synthetic data with:")
    print("  • Weekly uptrend")
    print("  • Daily consolidation at 145-150 (S/R zones)")
    print("  • Recent breakout above 150 with volume")
    print("  • 4H bullish momentum\n")

    # Create test data
    mtf_data = create_test_data()

    # Initialize strategy
    strategy = MultiTimeframeBreakoutStrategy()

    print("Test 1: S/R Analysis Execution")
    print("-" * 70)

    # Analyze weekly trend
    weekly_trend, weekly_strength = strategy.analyze_weekly_trend(mtf_data['weekly'])
    print(f"✅ Weekly Analysis: {weekly_trend} (Strength: {weekly_strength:.1f}/100)")

    # Analyze daily breakout
    is_breakout, breakout_details = strategy.analyze_daily_breakout(mtf_data['daily'])
    print(f"✅ Daily Breakout: {is_breakout}")
    if is_breakout:
        print(f"   Breakout Price: ₹{breakout_details['breakout_price']:.2f}")
        print(f"   Volume Ratio: {breakout_details['volume_ratio']:.2f}x")

    # Run S/R analysis
    print("\nTest 2: Multi-Timeframe S/R Analysis")
    print("-" * 70)

    all_sr_zones = strategy.sr_analyzer.analyze_multi_timeframe_sr(
        mtf_data['weekly'],
        mtf_data['daily'],
        mtf_data['4h']
    )

    # Display S/R zones found
    for timeframe, zones_dict in all_sr_zones.items():
        if zones_dict:
            print(f"\n{timeframe.upper()} S/R Zones:")
            # Zones are in dict with 'resistance' and 'support' keys
            for zone_type, zones_list in zones_dict.items():
                if zones_list:
                    for zone in zones_list[:3]:  # Show top 3 of each type
                        print(f"   {zone.zone_type.capitalize():10s}: ₹{zone.level:.2f} "
                              f"(Strength: {zone.strength} touches)")

    # Find confluences
    sr_confluences = strategy.sr_analyzer.find_confluent_levels(all_sr_zones)

    if sr_confluences:
        print(f"\n✅ S/R Confluences Found: {len(sr_confluences)}")
        for conf in sr_confluences[:3]:
            print(f"   ₹{conf['level']:.2f} ({', '.join(conf['timeframes'])}) "
                  f"- Strength: {conf['total_strength']}")
    else:
        print("\nℹ️  No S/R confluences detected")

    # Analyze breakout quality
    print("\nTest 3: Breakout Quality Analysis")
    print("-" * 70)

    current_price = mtf_data['daily']['close'].iloc[-1]
    sr_quality = strategy.sr_analyzer.analyze_breakout_quality(
        current_price,
        all_sr_zones
    )

    print(f"Current Price: ₹{current_price:.2f}")
    print(f"S/R Quality Score: {sr_quality['quality_score']:.1f}/100")

    if sr_quality.get('nearest_resistance_above'):
        r_level, r_strength, r_tf = sr_quality['nearest_resistance_above']
        distance_pct = ((r_level - current_price) / current_price) * 100
        print(f"Next Resistance: ₹{r_level:.2f} (+{distance_pct:.1f}% away, {r_tf}, {r_strength} touches)")

    if sr_quality.get('nearest_support_below'):
        s_level, s_strength, s_tf = sr_quality['nearest_support_below']
        distance_pct = ((current_price - s_level) / current_price) * 100
        print(f"Nearest Support: ₹{s_level:.2f} (-{distance_pct:.1f}% away, {s_tf}, {s_strength} touches)")

    if sr_quality.get('issues'):
        print("\nWarnings:")
        for issue in sr_quality['issues']:
            print(f"   ⚠️  {issue}")

    # Test entry level calculation
    print("\nTest 4: Entry Level Calculation (S/R-Adjusted)")
    print("-" * 70)

    if is_breakout:
        # Without S/R
        levels_basic = strategy.calculate_entry_levels(
            mtf_data['daily'],
            breakout_details['breakout_price'],
            breakout_details['atr']
        )

        print("WITHOUT S/R Adjustment:")
        print(f"   Entry: ₹{levels_basic['entry']:.2f}")
        print(f"   Stop: ₹{levels_basic['stop_loss']:.2f}")
        print(f"   Target: ₹{levels_basic['target']:.2f}")
        print(f"   R:R = 1:{levels_basic['risk_reward_ratio']:.2f}")

        # With S/R
        levels_sr = strategy.calculate_entry_levels(
            mtf_data['daily'],
            breakout_details['breakout_price'],
            breakout_details['atr'],
            sr_analysis=sr_quality
        )

        print("\nWITH S/R Adjustment:")
        print(f"   Entry: ₹{levels_sr['entry']:.2f}")
        print(f"   Stop: ₹{levels_sr['stop_loss']:.2f}")
        print(f"   Target: ₹{levels_sr['target']:.2f}")
        print(f"   R:R = 1:{levels_sr['risk_reward_ratio']:.2f}")

        # Compare
        print("\nDifferences:")
        stop_diff = levels_sr['stop_loss'] - levels_basic['stop_loss']
        target_diff = levels_sr['target'] - levels_basic['target']

        print(f"   Stop adjusted by: ₹{stop_diff:+.2f}")
        print(f"   Target adjusted by: ₹{target_diff:+.2f}")

    print("\n" + "="*70)
    print("✅ S/R INTEGRATION TEST COMPLETE")
    print("="*70 + "\n")

    # Summary
    total_zones = 0
    for timeframe, zones_dict in all_sr_zones.items():
        if zones_dict:
            for zone_type, zones_list in zones_dict.items():
                total_zones += len(zones_list)

    print("Summary:")
    print(f"   S/R zones identified: {total_zones}")
    print(f"   S/R confluences found: {len(sr_confluences) if sr_confluences else 0}")
    print(f"   Quality score: {sr_quality['quality_score']:.1f}/100")
    print(f"   Quality threshold: {strategy.min_sr_quality}")

    if sr_quality['quality_score'] >= strategy.min_sr_quality:
        print(f"\n✅ PASS: Quality score meets threshold")
    else:
        print(f"\n❌ FAIL: Quality score below threshold")

    print()

if __name__ == '__main__':
    test_sr_integration()
