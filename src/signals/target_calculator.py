"""Target Calculator (SHORT-033)"""

import pandas as pd


class TargetCalculator:
    """Calculate profit targets with 2:1 risk-reward"""

    def __init__(self, risk_reward_ratio: float = 2.0):
        """
        Initialize calculator

        Args:
            risk_reward_ratio: Risk-reward ratio (default 2.0 for 2:1)
        """
        self.risk_reward_ratio = risk_reward_ratio

    def calculate_target(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str = "long"
    ) -> float:
        """
        Calculate profit target

        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            direction: "long" or "short"

        Returns:
            Target price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * self.risk_reward_ratio

        if direction == "long":
            return entry_price + reward
        else:  # short
            return entry_price - reward

    def calculate_targets(
        self,
        df: pd.DataFrame,
        stop_losses: pd.Series,
        direction: str = "long"
    ) -> pd.Series:
        """
        Calculate targets for all bars

        Args:
            df: DataFrame with close prices
            stop_losses: Stop-loss series
            direction: "long" or "short"

        Returns:
            Series of target levels
        """
        close = df['close']
        risk = abs(close - stop_losses)
        reward = risk * self.risk_reward_ratio

        if direction == "long":
            return close + reward
        else:
            return close - reward
