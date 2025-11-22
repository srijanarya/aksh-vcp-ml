#!/usr/bin/env python3
"""
Multi-Timeframe Support & Resistance Analysis

Identifies key support/resistance zones across Weekly, Daily, and 4H timeframes.
Critical for improving breakout quality and avoiding false breaks.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class SupportResistanceZone:
    """Support or Resistance zone"""
    level: float
    strength: int  # Number of touches
    timeframe: str  # 'weekly', 'daily', '4h'
    zone_type: str  # 'support' or 'resistance'
    last_test: pd.Timestamp


class MultiTimeframeSR:
    """
    Identify support and resistance zones across multiple timeframes

    Why Multi-Timeframe S/R Matters:
    - Weekly S/R = Major institutional levels (strongest)
    - Daily S/R = Swing trading levels (medium strength)
    - 4H S/R = Intraday levels (weaker but relevant)

    Key Concepts:
    1. Zones vs Lines: Use zones (price ranges) not exact lines
    2. Touch Count: More touches = stronger level
    3. Confluence: Multiple timeframes at same level = very strong
    4. Old Resistance becomes New Support (and vice versa)
    """

    def __init__(self, zone_tolerance: float = 0.02):
        """
        Initialize SR analyzer

        Args:
            zone_tolerance: % tolerance for zone width (default 2%)
        """
        self.zone_tolerance = zone_tolerance

    def find_swing_points(self, data: pd.DataFrame, window: int = 5) -> Tuple[List, List]:
        """
        Find swing highs and swing lows

        Swing High: High that is higher than N bars before and after
        Swing Low: Low that is lower than N bars before and after

        Args:
            data: OHLCV DataFrame
            window: Lookback/forward window for swing detection

        Returns:
            (swing_highs, swing_lows) as lists of (index, price)
        """
        swing_highs = []
        swing_lows = []

        for i in range(window, len(data) - window):
            # Check if current high is a swing high
            is_swing_high = True
            is_swing_low = True

            current_high = data['high'].iloc[i]
            current_low = data['low'].iloc[i]

            # Compare with previous and next N bars
            for j in range(1, window + 1):
                # Swing high check
                if (data['high'].iloc[i-j] >= current_high or
                    data['high'].iloc[i+j] >= current_high):
                    is_swing_high = False

                # Swing low check
                if (data['low'].iloc[i-j] <= current_low or
                    data['low'].iloc[i+j] <= current_low):
                    is_swing_low = False

            if is_swing_high:
                swing_highs.append((data.index[i], current_high))

            if is_swing_low:
                swing_lows.append((data.index[i], current_low))

        return swing_highs, swing_lows

    def cluster_levels(self, levels: List[Tuple], tolerance: float) -> List[Dict]:
        """
        Cluster nearby levels into zones

        Args:
            levels: List of (timestamp, price) tuples
            tolerance: % tolerance for clustering

        Returns:
            List of zones with average price and strength
        """
        if not levels:
            return []

        # Sort by price
        sorted_levels = sorted(levels, key=lambda x: x[1])

        zones = []
        current_zone = [sorted_levels[0]]

        for i in range(1, len(sorted_levels)):
            prev_price = current_zone[-1][1]
            curr_price = sorted_levels[i][1]

            # Check if within tolerance
            if abs(curr_price - prev_price) / prev_price <= tolerance:
                current_zone.append(sorted_levels[i])
            else:
                # Save current zone and start new one
                zones.append(self._create_zone(current_zone))
                current_zone = [sorted_levels[i]]

        # Don't forget the last zone
        if current_zone:
            zones.append(self._create_zone(current_zone))

        return zones

    def _create_zone(self, levels: List[Tuple]) -> Dict:
        """Create zone dict from clustered levels"""
        prices = [l[1] for l in levels]
        timestamps = [l[0] for l in levels]

        return {
            'level': np.mean(prices),
            'min_price': min(prices),
            'max_price': max(prices),
            'strength': len(levels),
            'last_test': max(timestamps),
            'first_test': min(timestamps)
        }

    def identify_sr_zones(
        self,
        data: pd.DataFrame,
        timeframe: str,
        min_strength: int = 2
    ) -> Dict[str, List[SupportResistanceZone]]:
        """
        Identify support and resistance zones for a timeframe

        Args:
            data: OHLCV DataFrame
            timeframe: 'weekly', 'daily', or '4h'
            min_strength: Minimum touches to be considered valid

        Returns:
            Dict with 'support' and 'resistance' zone lists
        """
        # Find swing points
        swing_highs, swing_lows = self.find_swing_points(data)

        # Cluster into zones
        resistance_zones = self.cluster_levels(swing_highs, self.zone_tolerance)
        support_zones = self.cluster_levels(swing_lows, self.zone_tolerance)

        # Filter by minimum strength and convert to objects
        resistances = [
            SupportResistanceZone(
                level=z['level'],
                strength=z['strength'],
                timeframe=timeframe,
                zone_type='resistance',
                last_test=z['last_test']
            )
            for z in resistance_zones if z['strength'] >= min_strength
        ]

        supports = [
            SupportResistanceZone(
                level=z['level'],
                strength=z['strength'],
                timeframe=timeframe,
                zone_type='support',
                last_test=z['last_test']
            )
            for z in support_zones if z['strength'] >= min_strength
        ]

        return {
            'resistance': resistances,
            'support': supports
        }

    def analyze_multi_timeframe_sr(
        self,
        weekly_data: pd.DataFrame,
        daily_data: pd.DataFrame,
        data_4h: pd.DataFrame
    ) -> Dict:
        """
        Analyze S/R across all timeframes

        Returns:
            Dict with S/R zones for each timeframe
        """
        result = {}

        # Weekly S/R (strongest)
        if not weekly_data.empty:
            result['weekly'] = self.identify_sr_zones(weekly_data, 'weekly', min_strength=2)

        # Daily S/R (medium)
        if not daily_data.empty:
            result['daily'] = self.identify_sr_zones(daily_data, 'daily', min_strength=3)

        # 4H S/R (weaker but relevant for entries)
        if not data_4h.empty:
            result['4h'] = self.identify_sr_zones(data_4h, '4h', min_strength=2)

        return result

    def find_confluent_levels(
        self,
        all_sr_zones: Dict,
        price_tolerance: float = 0.03
    ) -> List[Dict]:
        """
        Find S/R levels that align across multiple timeframes (confluences)

        These are VERY strong levels - institutional zones

        Args:
            all_sr_zones: Output from analyze_multi_timeframe_sr()
            price_tolerance: % tolerance for considering levels aligned

        Returns:
            List of confluent zones with combined strength
        """
        confluences = []

        # Get all levels across all timeframes
        all_levels = []
        for tf, zones in all_sr_zones.items():
            for zone_type in ['support', 'resistance']:
                if zone_type in zones:
                    for zone in zones[zone_type]:
                        all_levels.append({
                            'level': zone.level,
                            'strength': zone.strength,
                            'timeframe': zone.timeframe,
                            'type': zone.zone_type
                        })

        # Find confluences
        checked = set()
        for i, level1 in enumerate(all_levels):
            if i in checked:
                continue

            # Find all levels within tolerance
            matching_levels = [level1]
            matched_indices = {i}

            for j, level2 in enumerate(all_levels):
                if j <= i or j in checked:
                    continue

                # Check if within tolerance and same type
                price_diff = abs(level1['level'] - level2['level']) / level1['level']
                if price_diff <= price_tolerance and level1['type'] == level2['type']:
                    matching_levels.append(level2)
                    matched_indices.add(j)

            # If we found confluence (2+ timeframes)
            if len(matching_levels) >= 2:
                timeframes = set(l['timeframe'] for l in matching_levels)
                if len(timeframes) >= 2:  # Must be different timeframes
                    checked.update(matched_indices)

                    confluences.append({
                        'level': np.mean([l['level'] for l in matching_levels]),
                        'type': level1['type'],
                        'timeframes': list(timeframes),
                        'total_strength': sum(l['strength'] for l in matching_levels),
                        'confluence_count': len(timeframes)
                    })

        # Sort by confluence strength
        confluences.sort(key=lambda x: (x['confluence_count'], x['total_strength']), reverse=True)

        return confluences

    def is_near_resistance(
        self,
        price: float,
        resistance_zones: List[SupportResistanceZone],
        tolerance: float = 0.02
    ) -> Tuple[bool, float]:
        """
        Check if price is near a resistance zone

        Returns:
            (is_near, distance_pct)
        """
        for zone in resistance_zones:
            distance = (zone.level - price) / price
            if abs(distance) <= tolerance:
                return True, distance

        return False, 0.0

    def is_near_support(
        self,
        price: float,
        support_zones: List[SupportResistanceZone],
        tolerance: float = 0.02
    ) -> Tuple[bool, float]:
        """
        Check if price is near a support zone

        Returns:
            (is_near, distance_pct)
        """
        for zone in support_zones:
            distance = (price - zone.level) / price
            if abs(distance) <= tolerance:
                return True, distance

        return False, 0.0

    def analyze_breakout_quality(
        self,
        current_price: float,
        all_sr_zones: Dict
    ) -> Dict:
        """
        Analyze breakout quality based on S/R structure

        Returns quality assessment and nearby levels
        """
        # Find nearest resistance above current price
        all_resistances = []
        for tf, zones in all_sr_zones.items():
            if 'resistance' in zones:
                all_resistances.extend([
                    (r.level, r.strength, r.timeframe)
                    for r in zones['resistance']
                    if r.level > current_price
                ])

        all_resistances.sort(key=lambda x: x[0])  # Sort by price

        # Find nearest support below current price
        all_supports = []
        for tf, zones in all_sr_zones.items():
            if 'support' in zones:
                all_supports.extend([
                    (s.level, s.strength, s.timeframe)
                    for s in zones['support']
                    if s.level < current_price
                ])

        all_supports.sort(key=lambda x: x[0], reverse=True)  # Sort descending

        # Calculate quality score
        quality_score = 100
        issues = []

        # Check if just broke a resistance
        if all_resistances:
            nearest_resistance = all_resistances[0]
            distance_to_resistance = (nearest_resistance[0] - current_price) / current_price

            if distance_to_resistance < -0.01:  # Already 1%+ above
                issues.append("Already extended above resistance")
                quality_score -= 20
            elif distance_to_resistance < 0.03:  # Within 3%
                quality_score += 20  # Good - fresh breakout

        # Check support below (for stop placement)
        if all_supports:
            nearest_support = all_supports[0]
            distance_to_support = (current_price - nearest_support[0]) / current_price

            if distance_to_support > 0.10:  # Support > 10% away
                issues.append("Support too far - wide stop needed")
                quality_score -= 15
        else:
            issues.append("No clear support below")
            quality_score -= 25

        return {
            'quality_score': max(0, quality_score),
            'nearest_resistance_above': all_resistances[0] if all_resistances else None,
            'nearest_support_below': all_supports[0] if all_supports else None,
            'resistance_levels': all_resistances[:3],  # Top 3
            'support_levels': all_supports[:3],  # Top 3
            'issues': issues
        }


def example_usage():
    """Example of how to use multi-timeframe S/R analysis"""
    import yfinance as yf
    from datetime import datetime, timedelta

    # Fetch data
    symbol = "RELIANCE.NS"
    ticker = yf.Ticker(symbol)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    daily_data = ticker.history(start=start_date, end=end_date, interval='1d')
    daily_data.columns = [col.lower() for col in daily_data.columns]

    # Create weekly data by resampling
    weekly_data = daily_data.resample('W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    print(f"\n{'='*70}")
    print(f"Multi-Timeframe S/R Analysis: {symbol}")
    print(f"{'='*70}\n")

    # Initialize analyzer
    sr_analyzer = MultiTimeframeSR(zone_tolerance=0.02)

    # Analyze weekly
    print("📅 Weekly Support & Resistance:")
    weekly_sr = sr_analyzer.identify_sr_zones(weekly_data, 'weekly', min_strength=2)

    print(f"\n   Resistance Zones ({len(weekly_sr['resistance'])}):")
    for r in weekly_sr['resistance'][:5]:  # Top 5
        print(f"      ₹{r.level:.2f} (Strength: {r.strength}, Last: {r.last_test.strftime('%Y-%m-%d')})")

    print(f"\n   Support Zones ({len(weekly_sr['support'])}):")
    for s in weekly_sr['support'][:5]:  # Top 5
        print(f"      ₹{s.level:.2f} (Strength: {s.strength}, Last: {s.last_test.strftime('%Y-%m-%d')})")

    # Analyze daily
    print(f"\n📊 Daily Support & Resistance:")
    daily_sr = sr_analyzer.identify_sr_zones(daily_data, 'daily', min_strength=3)

    print(f"\n   Resistance Zones ({len(daily_sr['resistance'])}):")
    for r in daily_sr['resistance'][:5]:
        print(f"      ₹{r.level:.2f} (Strength: {r.strength}, Last: {r.last_test.strftime('%Y-%m-%d')})")

    print(f"\n   Support Zones ({len(daily_sr['support'])}):")
    for s in daily_sr['support'][:5]:
        print(f"      ₹{s.level:.2f} (Strength: {s.strength}, Last: {s.last_test.strftime('%Y-%m-%d')})")

    # Find confluences
    all_sr = {
        'weekly': weekly_sr,
        'daily': daily_sr
    }

    confluences = sr_analyzer.find_confluent_levels(all_sr, price_tolerance=0.03)

    print(f"\n🎯 Multi-Timeframe Confluences ({len(confluences)}):")
    for conf in confluences:
        print(f"\n   ₹{conf['level']:.2f} ({conf['type'].upper()})")
        print(f"      Timeframes: {', '.join(conf['timeframes'])}")
        print(f"      Total Strength: {conf['total_strength']}")
        print(f"      Confluence Score: {conf['confluence_count']}")

    # Analyze current price
    current_price = daily_data['close'].iloc[-1]
    analysis = sr_analyzer.analyze_breakout_quality(current_price, all_sr)

    print(f"\n📈 Current Price Analysis (₹{current_price:.2f}):")
    print(f"   Quality Score: {analysis['quality_score']}/100")

    if analysis['nearest_resistance_above']:
        r = analysis['nearest_resistance_above']
        distance = (r[0] - current_price) / current_price * 100
        print(f"   Next Resistance: ₹{r[0]:.2f} ({distance:+.2f}%) - {r[2]} TF")

    if analysis['nearest_support_below']:
        s = analysis['nearest_support_below']
        distance = (current_price - s[0]) / current_price * 100
        print(f"   Nearest Support: ₹{s[0]:.2f} (-{distance:.2f}%) - {s[2]} TF")

    if analysis['issues']:
        print(f"\n   ⚠️  Issues:")
        for issue in analysis['issues']:
            print(f"      • {issue}")

    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    example_usage()
