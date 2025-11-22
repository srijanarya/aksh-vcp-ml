"""
Regime Detection (SHORT-052 to SHORT-055)

Detect market regime (trending/ranging) and select strategies accordingly.
"""

import pandas as pd
from enum import Enum


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"


class RegimeDetector:
    """Detect market regime using volatility and trend indicators"""

    def __init__(
        self,
        adx_threshold: float = 25.0,
        volatility_threshold: float = 2.0
    ):
        """
        Initialize regime detector

        Args:
            adx_threshold: ADX threshold for trending vs ranging
            volatility_threshold: Volatility threshold for volatile regime
        """
        self.adx_threshold = adx_threshold
        self.volatility_threshold = volatility_threshold

    def detect_regime(
        self,
        df: pd.DataFrame,
        adx: pd.Series
    ) -> MarketRegime:
        """
        Detect current market regime

        Args:
            df: OHLC DataFrame
            adx: ADX series

        Returns:
            MarketRegime enum
        """
        # Calculate volatility
        returns = df['close'].pct_change()
        volatility = returns.std() * 100

        # Get latest ADX
        current_adx = adx.iloc[-1]

        # Determine regime
        if volatility > self.volatility_threshold:
            return MarketRegime.VOLATILE
        elif current_adx >= self.adx_threshold:
            return MarketRegime.TRENDING
        else:
            return MarketRegime.RANGING

    def select_strategy(self, regime: MarketRegime) -> str:
        """
        Select strategy based on regime

        Args:
            regime: Detected market regime

        Returns:
            Strategy name
        """
        strategy_map = {
            MarketRegime.TRENDING: "trend_following",
            MarketRegime.RANGING: "mean_reversion",
            MarketRegime.VOLATILE: "risk_off"
        }

        return strategy_map[regime]
