"""Stop-Loss Calculator (SHORT-032)"""

import pandas as pd


class StopLossCalculator:
    """Calculate ATR-based stop-loss levels"""

    def __init__(self, atr_multiplier: float = 2.0):
        """
        Initialize calculator

        Args:
            atr_multiplier: ATR multiplier for stop distance (default 2.0)
        """
        self.atr_multiplier = atr_multiplier

    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        direction: str = "long"
    ) -> float:
        """
        Calculate stop-loss price

        Args:
            entry_price: Entry price
            atr: Current ATR value
            direction: "long" or "short"

        Returns:
            Stop-loss price
        """
        stop_distance = atr * self.atr_multiplier

        if direction == "long":
            return entry_price - stop_distance
        else:  # short
            return entry_price + stop_distance

    def calculate_stop_losses(
        self,
        df: pd.DataFrame,
        atr: pd.Series,
        direction: str = "long"
    ) -> pd.Series:
        """
        Calculate stop-loss for all bars

        Args:
            df: DataFrame with close prices
            atr: ATR series
            direction: "long" or "short"

        Returns:
            Series of stop-loss levels
        """
        close = df['close']
        stop_distance = atr * self.atr_multiplier

        if direction == "long":
            return close - stop_distance
        else:
            return close + stop_distance
