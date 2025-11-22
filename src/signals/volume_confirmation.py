"""Volume Confirmation Checker (SHORT-030)"""

import pandas as pd


class VolumeConfirmationChecker:
    """Check volume confirmation for signals"""

    def __init__(self, volume_threshold: float = 1.5):
        """
        Initialize checker

        Args:
            volume_threshold: Minimum volume multiple (default 1.5x avg)
        """
        self.volume_threshold = volume_threshold

    def check_confirmation(
        self,
        volume: float,
        avg_volume: float
    ) -> bool:
        """
        Check if volume confirms signal

        Args:
            volume: Current volume
            avg_volume: Average volume

        Returns:
            True if volume >= threshold * avg_volume
        """
        if avg_volume == 0:
            return False

        return volume >= (self.volume_threshold * avg_volume)

    def check_signals(
        self,
        df: pd.DataFrame,
        volume_period: int = 20
    ) -> pd.Series:
        """
        Check volume confirmation for all bars

        Args:
            df: DataFrame with 'volume' column
            volume_period: Period for average volume

        Returns:
            Boolean series of volume confirmations
        """
        volume = df['volume']
        avg_volume = volume.rolling(window=volume_period).mean()

        return volume >= (self.volume_threshold * avg_volume)
