"""Signal Filter (SHORT-028)"""

import pandas as pd


class SignalFilter:
    """Filter signals based on ADX and DMA thresholds"""

    def __init__(self, adx_threshold: float = 25.0, dma_threshold: float = 5.0):
        """
        Initialize filter

        Args:
            adx_threshold: Minimum ADX value
            dma_threshold: Minimum % above DMA
        """
        self.adx_threshold = adx_threshold
        self.dma_threshold = dma_threshold

    def filter_signals(
        self,
        df: pd.DataFrame,
        adx: pd.Series,
        dma: pd.Series
    ) -> pd.Series:
        """
        Filter buy signals

        Args:
            df: OHLC DataFrame
            adx: ADX series
            dma: DMA series

        Returns:
            Boolean series indicating valid signals
        """
        close = df['close']

        # ADX above threshold (strong trend)
        adx_condition = adx >= self.adx_threshold

        # Close above DMA by threshold %
        pct_above_dma = ((close - dma) / dma * 100)
        dma_condition = pct_above_dma >= self.dma_threshold

        return adx_condition & dma_condition
