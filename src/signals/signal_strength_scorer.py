"""Signal Strength Scorer (SHORT-029)"""

import pandas as pd
from typing import Dict


class SignalStrengthScorer:
    """Score signal strength based on multiple factors"""

    def __init__(
        self,
        adx_weight: float = 0.35,
        dma_weight: float = 0.35,
        volume_weight: float = 0.30
    ):
        """
        Initialize scorer

        Args:
            adx_weight: Weight for ADX component (default 35%)
            dma_weight: Weight for DMA component (default 35%)
            volume_weight: Weight for volume component (default 30%)
        """
        total = adx_weight + dma_weight + volume_weight
        self.adx_weight = adx_weight / total
        self.dma_weight = dma_weight / total
        self.volume_weight = volume_weight / total

    def score_signal(
        self,
        close: float,
        adx: float,
        dma: float,
        volume: float,
        avg_volume: float
    ) -> float:
        """
        Score individual signal strength

        Args:
            close: Current close price
            adx: ADX value
            dma: DMA value
            volume: Current volume
            avg_volume: Average volume

        Returns:
            Signal strength score (0-100)
        """
        # Component 1: ADX strength (0-100)
        # ADX > 50 = very strong trend (100)
        # ADX = 25 = moderate trend (50)
        # ADX < 25 = weak trend (0)
        adx_score = min(100, max(0, (adx - 25) * 4))

        # Component 2: Distance above DMA (0-100)
        # 10%+ above DMA = 100
        # 5% above DMA = 50
        # At/below DMA = 0
        pct_above_dma = ((close - dma) / dma) * 100
        dma_score = min(100, max(0, pct_above_dma * 10))

        # Component 3: Volume confirmation (0-100)
        # 2x avg volume = 100
        # 1x avg volume = 50
        # Below avg = 0
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            volume_score = min(100, max(0, (volume_ratio - 1) * 100))
        else:
            volume_score = 0

        # Weighted combination
        total_score = (
            self.adx_weight * adx_score +
            self.dma_weight * dma_score +
            self.volume_weight * volume_score
        )

        return round(total_score, 2)

    def score_signals(
        self,
        df: pd.DataFrame,
        adx: pd.Series,
        dma: pd.Series,
        volume_period: int = 20
    ) -> pd.Series:
        """
        Score all signals in DataFrame

        Args:
            df: OHLC DataFrame with volume
            adx: ADX series
            dma: DMA series
            volume_period: Period for average volume calculation

        Returns:
            Series with signal strength scores (0-100)
        """
        close = df['close']
        volume = df['volume']
        avg_volume = volume.rolling(window=volume_period).mean()

        scores = []
        for i in range(len(df)):
            if pd.isna(adx.iloc[i]) or pd.isna(dma.iloc[i]) or pd.isna(avg_volume.iloc[i]):
                scores.append(0.0)
            else:
                score = self.score_signal(
                    close=close.iloc[i],
                    adx=adx.iloc[i],
                    dma=dma.iloc[i],
                    volume=volume.iloc[i],
                    avg_volume=avg_volume.iloc[i]
                )
                scores.append(score)

        return pd.Series(scores, index=df.index)

    def get_score_breakdown(
        self,
        close: float,
        adx: float,
        dma: float,
        volume: float,
        avg_volume: float
    ) -> Dict[str, float]:
        """
        Get detailed score breakdown

        Args:
            close: Current close price
            adx: ADX value
            dma: DMA value
            volume: Current volume
            avg_volume: Average volume

        Returns:
            Dictionary with component scores and total
        """
        # ADX component
        adx_score = min(100, max(0, (adx - 25) * 4))

        # DMA component
        pct_above_dma = ((close - dma) / dma) * 100
        dma_score = min(100, max(0, pct_above_dma * 10))

        # Volume component
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            volume_score = min(100, max(0, (volume_ratio - 1) * 100))
        else:
            volume_score = 0

        # Total
        total_score = (
            self.adx_weight * adx_score +
            self.dma_weight * dma_score +
            self.volume_weight * volume_score
        )

        return {
            'adx_score': round(adx_score, 2),
            'dma_score': round(dma_score, 2),
            'volume_score': round(volume_score, 2),
            'total_score': round(total_score, 2),
            'adx_weight': round(self.adx_weight * 100, 1),
            'dma_weight': round(self.dma_weight * 100, 1),
            'volume_weight': round(self.volume_weight * 100, 1)
        }
