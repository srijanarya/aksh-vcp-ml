"""Support/Resistance Detector (SHORT-031)"""

import pandas as pd
import numpy as np
from typing import List, Tuple


class SupportResistanceDetector:
    """Detect support and resistance levels"""

    def __init__(self, lookback: int = 20, tolerance: float = 0.02):
        """
        Initialize detector

        Args:
            lookback: Lookback period for pivot detection
            tolerance: Price clustering tolerance (2% default)
        """
        self.lookback = lookback
        self.tolerance = tolerance

    def detect_pivots(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """
        Detect pivot highs and lows

        Args:
            df: OHLC DataFrame

        Returns:
            Tuple of (resistance_levels, support_levels)
        """
        high = df['high'].values
        low = df['low'].values

        resistance = []
        support = []

        for i in range(self.lookback, len(df) - self.lookback):
            # Check if local maximum (resistance)
            if high[i] == max(high[i - self.lookback:i + self.lookback + 1]):
                resistance.append(high[i])

            # Check if local minimum (support)
            if low[i] == min(low[i - self.lookback:i + self.lookback + 1]):
                support.append(low[i])

        # Cluster nearby levels
        resistance = self._cluster_levels(resistance)
        support = self._cluster_levels(support)

        return resistance, support

    def _cluster_levels(self, levels: List[float]) -> List[float]:
        """Cluster nearby price levels"""
        if not levels:
            return []

        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] <= self.tolerance:
                current_cluster.append(level)
            else:
                # Average the cluster
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]

        # Add last cluster
        if current_cluster:
            clustered.append(np.mean(current_cluster))

        return clustered

    def is_near_resistance(self, price: float, resistance_levels: List[float]) -> bool:
        """Check if price is near resistance"""
        for level in resistance_levels:
            if abs(price - level) / level <= self.tolerance:
                return True
        return False

    def is_near_support(self, price: float, support_levels: List[float]) -> bool:
        """Check if price is near support"""
        for level in support_levels:
            if abs(price - level) / level <= self.tolerance:
                return True
        return False
