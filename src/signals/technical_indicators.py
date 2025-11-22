"""
Technical Indicators (SHORT-024 to SHORT-027)

ADX, EMA, DMA, ATR calculations for signal generation.
"""

import pandas as pd
import numpy as np


class TechnicalIndicators:
    """Calculate technical indicators"""

    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate ADX (Average Directional Index)

        Args:
            df: DataFrame with high, low, close
            period: ADX period (default 14)

        Returns:
            Series with ADX values
        """
        high = df['high']
        low = df['low']
        close = df['close']

        # Calculate +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Smooth True Range and Directional Movements
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx

    @staticmethod
    def calculate_ema(series: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate EMA (Exponential Moving Average)

        Args:
            series: Price series
            period: EMA period (default 20)

        Returns:
            Series with EMA values
        """
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_dma(
        close: pd.Series,
        ema_period: int = 20,
        displacement_pct: float = 5.0
    ) -> pd.Series:
        """
        Calculate DMA (Displaced Moving Average)

        Args:
            close: Close price series
            ema_period: EMA period (default 20)
            displacement_pct: Displacement percentage (default 5%)

        Returns:
            Series with DMA values
        """
        ema = TechnicalIndicators.calculate_ema(close, ema_period)
        dma = ema * (1 - displacement_pct / 100)
        return dma

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate ATR (Average True Range)

        Args:
            df: DataFrame with high, low, close
            period: ATR period (default 14)

        Returns:
            Series with ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr
