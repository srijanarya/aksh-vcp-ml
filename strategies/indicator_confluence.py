#!/usr/bin/env python3
"""
Indicator Confluence Detection System

Detects confluence between multiple technical indicators at price levels:
- Moving Averages (20/50/100/200)
- MA Crossovers (50x100, 50x200 Golden Cross)
- VWAP (Volume-Weighted Average Price)
- Fibonacci Retracement Levels
- Camarilla Pivot Points
- Support/Resistance Zones

Research-backed weights based on backtested success rates:
- VWAP (intraday): 30 points (institutional benchmark)
- Camarilla H4/L4: 27 points (65-70% success rate)
- S/R Zones: 28 points (60-75% success rate)
- Major MAs: 22 points (55-70% success rate)
- Golden Cross: 35 points (2.5x regular crossover)
- Fibonacci: 8-18 points (only 37-40% success standalone)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ConfluenceIndicator:
    """Single indicator at a price level"""
    price: float
    indicator_name: str  # e.g., "Daily_MA50", "VWAP", "FIB_61.8"
    indicator_type: str  # 'ma', 'vwap', 'fibonacci', 'camarilla', 'sr_zone', 'crossover'
    timeframe: str  # 'weekly', 'daily', '4h', '1h'
    direction: str  # 'support' or 'resistance'
    weight: float  # Research-backed weight
    metadata: Dict  # Additional info (e.g., crossover details, zone strength)


@dataclass
class ConfluenceZone:
    """Cluster of indicators at same price level"""
    price_level: float  # Average price
    min_price: float
    max_price: float
    direction: str  # 'support' or 'resistance'
    indicators: List[ConfluenceIndicator]
    confluence_count: int  # Number of indicators
    total_weight: float  # Sum of all weights
    weighted_score: float  # With cross-timeframe multiplier
    has_crossover: bool  # Extra strength if crossover present
    timeframes: List[str]  # Unique timeframes represented


class IndicatorConfluence:
    """
    Comprehensive indicator confluence detection system

    Based on financial research:
    - Confluence tolerance: 1.5% (tighter = better quality)
    - Cross-timeframe multiplier: 1.75x (up to 2.5x)
    - VWAP highest weight for intraday (institutional benchmark)
    - Fibonacci low weight (only 37-40% success rate)
    - Camarilla high weight for intraday (60-70% success rate)
    """

    def __init__(self, confluence_tolerance: float = 0.015):
        """
        Args:
            confluence_tolerance: Price tolerance for clustering (default 1.5%)
        """
        self.confluence_tolerance = confluence_tolerance

        # Research-backed base weights
        self.base_weights = {
            'vwap_intraday': 30,
            'vwap_swing': 12,
            'camarilla_h4_l4': 27,
            'camarilla_h3_l3': 22,
            'sr_zone': 28,
            'ma_major': 22,  # 50-day, 200-day
            'ma_minor': 18,  # 20-day, 100-day
            'golden_cross': 35,
            'regular_crossover': 17,
            'fibonacci_standalone': 8,
            'fibonacci_confluence': 18,
        }

    def detect_all_confluences(
        self,
        data: pd.DataFrame,
        current_price: float,
        timeframe: str,
        sr_zones: Optional[List] = None,
        hours_since_open: Optional[int] = None,
        volume_ratio: float = 1.0,
        is_trending: bool = False
    ) -> List[ConfluenceZone]:
        """
        Detect all indicator confluences in the data

        Args:
            data: OHLCV DataFrame
            current_price: Current price for directional classification
            timeframe: 'weekly', 'daily', '4h', '1h'
            sr_zones: Pre-calculated S/R zones (optional)
            hours_since_open: Hours since market open (for VWAP/Camarilla weighting)
            volume_ratio: Current volume / average volume
            is_trending: Whether market is in strong trend (affects Fibonacci weight)

        Returns:
            List of ConfluenceZone objects, sorted by weighted_score
        """
        all_indicators = []

        # 1. Moving Average levels
        ma_indicators = self._get_ma_levels(data, current_price, timeframe)
        all_indicators.extend(ma_indicators)

        # 2. MA Crossovers (special high-weight indicators)
        crossover_indicators = self._detect_ma_crossovers(data, current_price, timeframe)
        all_indicators.extend(crossover_indicators)

        # 3. VWAP
        vwap_indicator = self._calculate_vwap(data, current_price, timeframe, hours_since_open)
        if vwap_indicator:
            all_indicators.append(vwap_indicator)

        # 4. Fibonacci retracements (intraday/4H only, or if trending)
        if timeframe in ['4h', '1h'] or is_trending:
            fib_indicators = self._calculate_fibonacci_levels(
                data, current_price, timeframe,
                is_trending=is_trending,
                has_other_confluence=(len(all_indicators) >= 2)
            )
            all_indicators.extend(fib_indicators)

        # 5. Camarilla pivots (intraday only)
        if timeframe in ['4h', '1h']:
            camarilla_indicators = self._calculate_camarilla_pivots(
                data, current_price, timeframe,
                hours_since_open=hours_since_open,
                volume_ratio=volume_ratio
            )
            all_indicators.extend(camarilla_indicators)

        # 6. S/R zones (if provided)
        if sr_zones:
            sr_indicators = self._convert_sr_zones(sr_zones, current_price, timeframe)
            all_indicators.extend(sr_indicators)

        # Cluster indicators into confluence zones
        confluence_zones = self._cluster_into_confluences(all_indicators)

        return confluence_zones

    def _get_ma_levels(
        self,
        data: pd.DataFrame,
        current_price: float,
        timeframe: str
    ) -> List[ConfluenceIndicator]:
        """Calculate moving average levels"""
        indicators = []

        ma_periods = {
            'MA_20': (20, 'ma_minor'),
            'MA_50': (50, 'ma_major'),
            'MA_100': (100, 'ma_minor'),
            'MA_200': (200, 'ma_major'),
        }

        for ma_name, (period, weight_type) in ma_periods.items():
            if len(data) < period:
                continue

            ma_value = data['close'].rolling(period).mean().iloc[-1]

            if pd.isna(ma_value):
                continue

            indicators.append(ConfluenceIndicator(
                price=ma_value,
                indicator_name=f'{timeframe}_{ma_name}',
                indicator_type='ma',
                timeframe=timeframe,
                direction='support' if current_price > ma_value else 'resistance',
                weight=self.base_weights[weight_type],
                metadata={'period': period}
            ))

        return indicators

    def _detect_ma_crossovers(
        self,
        data: pd.DataFrame,
        current_price: float,
        timeframe: str,
        lookback: int = 10
    ) -> List[ConfluenceIndicator]:
        """
        Detect MA crossovers in last N bars

        Research shows:
        - Golden Cross (50x200) is 2.5x more significant than regular crossover
        - Crossovers remain valid for ~50 bars (daily) with decay
        """
        indicators = []

        if len(data) < 200:
            return indicators

        # Calculate MAs
        ma_50 = data['close'].rolling(50).mean()
        ma_100 = data['close'].rolling(100).mean()
        ma_200 = data['close'].rolling(200).mean()

        # Check for crossovers in last N bars
        for i in range(max(-lookback, -len(data)+1), 0):
            # Golden Cross (50x200)
            if (not pd.isna(ma_50.iloc[i-1]) and not pd.isna(ma_200.iloc[i-1]) and
                not pd.isna(ma_50.iloc[i]) and not pd.isna(ma_200.iloc[i])):

                if ma_50.iloc[i-1] < ma_200.iloc[i-1] and ma_50.iloc[i] > ma_200.iloc[i]:
                    # Bullish Golden Cross
                    bars_ago = abs(i)
                    weight = self._calculate_crossover_weight('golden_cross', timeframe, bars_ago)

                    indicators.append(ConfluenceIndicator(
                        price=ma_50.iloc[i],
                        indicator_name=f'{timeframe}_GOLDEN_CROSS',
                        indicator_type='crossover',
                        timeframe=timeframe,
                        direction='support',
                        weight=weight,
                        metadata={
                            'crossover_type': 'golden_cross',
                            'bars_ago': bars_ago,
                            'bullish': True
                        }
                    ))
                    break  # Only report most recent

                elif ma_50.iloc[i-1] > ma_200.iloc[i-1] and ma_50.iloc[i] < ma_200.iloc[i]:
                    # Bearish Death Cross
                    bars_ago = abs(i)
                    weight = self._calculate_crossover_weight('golden_cross', timeframe, bars_ago)

                    indicators.append(ConfluenceIndicator(
                        price=ma_50.iloc[i],
                        indicator_name=f'{timeframe}_DEATH_CROSS',
                        indicator_type='crossover',
                        timeframe=timeframe,
                        direction='resistance',
                        weight=weight,
                        metadata={
                            'crossover_type': 'death_cross',
                            'bars_ago': bars_ago,
                            'bullish': False
                        }
                    ))
                    break

            # Regular Crossover (50x100)
            if (not pd.isna(ma_50.iloc[i-1]) and not pd.isna(ma_100.iloc[i-1]) and
                not pd.isna(ma_50.iloc[i]) and not pd.isna(ma_100.iloc[i])):

                if ma_50.iloc[i-1] < ma_100.iloc[i-1] and ma_50.iloc[i] > ma_100.iloc[i]:
                    bars_ago = abs(i)
                    weight = self._calculate_crossover_weight('regular', timeframe, bars_ago)

                    indicators.append(ConfluenceIndicator(
                        price=ma_50.iloc[i],
                        indicator_name=f'{timeframe}_MA50x100_BULLISH',
                        indicator_type='crossover',
                        timeframe=timeframe,
                        direction='support',
                        weight=weight,
                        metadata={
                            'crossover_type': '50x100',
                            'bars_ago': bars_ago,
                            'bullish': True
                        }
                    ))
                    break

        return indicators

    def _calculate_crossover_weight(
        self,
        crossover_type: str,
        timeframe: str,
        bars_ago: int
    ) -> float:
        """
        Calculate weight for crossover with decay function

        Research:
        - Golden Cross: Valid for ~50 bars on daily, 10 bars on intraday
        - Use exponential decay: Weight = Base × e^(-t/λ)
        """
        if crossover_type == 'golden_cross':
            base_weight = self.base_weights['golden_cross']
        else:
            base_weight = self.base_weights['regular_crossover']

        # Decay constant (half-life)
        lambda_values = {
            'monthly': 100,
            'weekly': 50,
            'daily': 50,
            '4h': 20,
            '1h': 10
        }
        lambda_decay = lambda_values.get(timeframe, 50)

        # Exponential decay
        decay_factor = np.exp(-bars_ago / lambda_decay)

        return base_weight * decay_factor

    def _calculate_vwap(
        self,
        data: pd.DataFrame,
        current_price: float,
        timeframe: str,
        hours_since_open: Optional[int] = None
    ) -> Optional[ConfluenceIndicator]:
        """
        Calculate VWAP with time-of-day weighting

        Research:
        - VWAP is institutional benchmark, highest weight for intraday
        - Peak reliability: Mid-session (60-180 min after open)
        - Lower reliability: First 30 min (forming), last hour (distorted flows)
        """
        if len(data) < 2:
            return None

        # Calculate VWAP
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).cumsum() / data['volume'].cumsum()
        current_vwap = vwap.iloc[-1]

        if pd.isna(current_vwap):
            return None

        # Determine base weight
        if timeframe in ['4h', '1h']:
            base_weight = self.base_weights['vwap_intraday']
        else:
            base_weight = self.base_weights['vwap_swing']

        # Adjust for time of day (intraday only)
        if timeframe in ['4h', '1h'] and hours_since_open is not None:
            if hours_since_open < 0.5:  # First 30 min
                time_adj = 0.6
            elif hours_since_open < 1:  # 30-60 min
                time_adj = 0.9
            elif hours_since_open < 3:  # 1-3 hours (peak)
                time_adj = 1.0
            else:  # Late session
                time_adj = 0.8
        else:
            time_adj = 1.0

        weight = base_weight * time_adj

        return ConfluenceIndicator(
            price=current_vwap,
            indicator_name=f'{timeframe}_VWAP',
            indicator_type='vwap',
            timeframe=timeframe,
            direction='support' if current_price > current_vwap else 'resistance',
            weight=weight,
            metadata={'hours_since_open': hours_since_open}
        )

    def _calculate_fibonacci_levels(
        self,
        data: pd.DataFrame,
        current_price: float,
        timeframe: str,
        lookback: int = 20,
        is_trending: bool = False,
        has_other_confluence: bool = False
    ) -> List[ConfluenceIndicator]:
        """
        Calculate Fibonacci retracement levels

        Research WARNING:
        - Only 37-40% success rate standalone
        - Use LOW weight (8 points) unless combined with other indicators
        - Works better in trending markets with pullbacks
        """
        indicators = []

        if len(data) < lookback:
            return indicators

        # Find recent swing high/low
        recent_data = data.iloc[-lookback:]
        swing_high = recent_data['high'].max()
        swing_low = recent_data['low'].min()
        diff = swing_high - swing_low

        if diff == 0:
            return indicators

        # Fibonacci ratios
        fib_levels = {
            'FIB_23.6': 0.236,
            'FIB_38.2': 0.382,
            'FIB_50.0': 0.500,
            'FIB_61.8': 0.618,
            'FIB_78.6': 0.786,
        }

        # Determine weight based on context
        if has_other_confluence:
            base_weight = self.base_weights['fibonacci_confluence']  # 18
        else:
            base_weight = self.base_weights['fibonacci_standalone']  # 8

        # Boost if trending (better in trend pullbacks)
        if is_trending:
            base_weight *= 1.5

        for fib_name, ratio in fib_levels.items():
            fib_price = swing_high - (diff * ratio)

            indicators.append(ConfluenceIndicator(
                price=fib_price,
                indicator_name=f'{timeframe}_{fib_name}',
                indicator_type='fibonacci',
                timeframe=timeframe,
                direction='support' if current_price > fib_price else 'resistance',
                weight=base_weight,
                metadata={
                    'ratio': ratio,
                    'swing_high': swing_high,
                    'swing_low': swing_low
                }
            ))

        return indicators

    def _calculate_camarilla_pivots(
        self,
        data: pd.DataFrame,
        current_price: float,
        timeframe: str,
        hours_since_open: Optional[int] = None,
        volume_ratio: float = 1.0
    ) -> List[ConfluenceIndicator]:
        """
        Calculate Camarilla pivot points

        Research:
        - High reliability for intraday (60-70% success rate)
        - H3/L3: Mean reversion levels (22 weight)
        - H4/L4: Breakout levels (27 weight)
        - Best in first 2-3 hours with high volume
        """
        indicators = []

        if len(data) < 2:
            return indicators

        # Use previous bar
        prev_bar = data.iloc[-2]
        H = prev_bar['high']
        L = prev_bar['low']
        C = prev_bar['close']

        # Camarilla pivot formulas
        pivots = {
            'CAM_R4': (C + ((H - L) * 1.1 / 2), 'camarilla_h4_l4'),
            'CAM_R3': (C + ((H - L) * 1.1 / 4), 'camarilla_h3_l3'),
            'CAM_R2': (C + ((H - L) * 1.1 / 6), 'camarilla_h3_l3'),
            'CAM_R1': (C + ((H - L) * 1.1 / 12), 'camarilla_h3_l3'),
            'CAM_S1': (C - ((H - L) * 1.1 / 12), 'camarilla_h3_l3'),
            'CAM_S2': (C - ((H - L) * 1.1 / 6), 'camarilla_h3_l3'),
            'CAM_S3': (C - ((H - L) * 1.1 / 4), 'camarilla_h3_l3'),
            'CAM_S4': (C - ((H - L) * 1.1 / 2), 'camarilla_h4_l4'),
        }

        for pivot_name, (pivot_price, weight_type) in pivots.items():
            base_weight = self.base_weights[weight_type]

            # Time-of-day adjustment
            if hours_since_open is not None:
                if hours_since_open <= 3:
                    time_adj = 1.4  # Peak reliability
                elif hours_since_open > 5:
                    time_adj = 0.7  # End-of-day deterioration
                else:
                    time_adj = 1.0
            else:
                time_adj = 1.0

            # Volume confirmation
            if volume_ratio > 1.5:
                volume_adj = 1.3
            elif volume_ratio < 0.7:
                volume_adj = 0.6
            else:
                volume_adj = 1.0

            weight = base_weight * time_adj * volume_adj

            indicators.append(ConfluenceIndicator(
                price=pivot_price,
                indicator_name=f'{timeframe}_{pivot_name}',
                indicator_type='camarilla',
                timeframe=timeframe,
                direction='support' if 'S' in pivot_name else 'resistance',
                weight=weight,
                metadata={
                    'level_type': pivot_name,
                    'hours_since_open': hours_since_open,
                    'volume_ratio': volume_ratio
                }
            ))

        return indicators

    def _convert_sr_zones(
        self,
        sr_zones: List,
        current_price: float,
        timeframe: str
    ) -> List[ConfluenceIndicator]:
        """Convert S/R zones to confluence indicators"""
        indicators = []

        for zone in sr_zones:
            # zone is SupportResistanceZone object
            indicators.append(ConfluenceIndicator(
                price=zone.level,
                indicator_name=f'{timeframe}_SR_ZONE',
                indicator_type='sr_zone',
                timeframe=zone.timeframe,
                direction=zone.zone_type,
                weight=self.base_weights['sr_zone'],
                metadata={
                    'strength': zone.strength,
                    'last_test': zone.last_test
                }
            ))

        return indicators

    def _cluster_into_confluences(
        self,
        indicators: List[ConfluenceIndicator]
    ) -> List[ConfluenceZone]:
        """
        Cluster indicators within tolerance into confluence zones

        Research:
        - Cross-timeframe confluence: 1.75x multiplier (up to 2.5x for distant TFs)
        - Tighter tolerance (1.5%) = better quality
        """
        if not indicators:
            return []

        confluences = []
        checked = set()

        for i, ind1 in enumerate(indicators):
            if i in checked:
                continue

            # Find all indicators within tolerance
            matching = [ind1]
            matched_idx = {i}

            for j, ind2 in enumerate(indicators):
                if j <= i or j in checked:
                    continue

                # Check price proximity and same direction
                price_diff = abs(ind1.price - ind2.price) / ind1.price
                if price_diff <= self.confluence_tolerance and ind1.direction == ind2.direction:
                    matching.append(ind2)
                    matched_idx.add(j)

            # If confluence (2+ indicators)
            if len(matching) >= 2:
                checked.update(matched_idx)

                # Calculate metrics
                prices = [m.price for m in matching]
                avg_price = np.mean(prices)
                total_weight = sum(m.weight for m in matching)
                timeframes = list(set(m.timeframe for m in matching))
                has_crossover = any(m.indicator_type == 'crossover' for m in matching)

                # Cross-timeframe multiplier
                if len(timeframes) >= 2:
                    # More timeframes = stronger multiplier
                    cross_tf_multiplier = min(1.5 + (len(timeframes) - 2) * 0.25, 2.5)
                else:
                    cross_tf_multiplier = 1.0

                weighted_score = total_weight * cross_tf_multiplier

                confluences.append(ConfluenceZone(
                    price_level=avg_price,
                    min_price=min(prices),
                    max_price=max(prices),
                    direction=ind1.direction,
                    indicators=matching,
                    confluence_count=len(matching),
                    total_weight=total_weight,
                    weighted_score=weighted_score,
                    has_crossover=has_crossover,
                    timeframes=timeframes
                ))

        # Sort by weighted score (strongest first)
        confluences.sort(key=lambda x: x.weighted_score, reverse=True)

        return confluences

    def get_nearest_confluence(
        self,
        confluences: List[ConfluenceZone],
        current_price: float,
        direction: str,
        max_distance_pct: float = 0.10
    ) -> Optional[ConfluenceZone]:
        """
        Get nearest confluence zone in specified direction

        Args:
            confluences: List of confluence zones
            current_price: Current price
            direction: 'support' (below) or 'resistance' (above)
            max_distance_pct: Maximum distance to search (default 10%)

        Returns:
            Nearest ConfluenceZone or None
        """
        candidates = []

        for conf in confluences:
            if conf.direction != direction:
                continue

            if direction == 'support' and conf.price_level < current_price:
                distance = (current_price - conf.price_level) / current_price
                if distance <= max_distance_pct:
                    candidates.append((distance, conf))

            elif direction == 'resistance' and conf.price_level > current_price:
                distance = (conf.price_level - current_price) / current_price
                if distance <= max_distance_pct:
                    candidates.append((distance, conf))

        if not candidates:
            return None

        # Return nearest
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
