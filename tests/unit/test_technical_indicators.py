"""Tests for Technical Indicators (SHORT-024 to SHORT-027)"""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_ohlc():
    """Sample OHLC data"""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    np.random.seed(42)

    close = 100 + np.cumsum(np.random.randn(50))
    high = close + np.random.uniform(1, 3, 50)
    low = close - np.random.uniform(1, 3, 50)
    open_price = close + np.random.uniform(-2, 2, 50)

    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(100000, 1000000, 50)
    }, index=dates)


def test_calculate_adx(sample_ohlc):
    """Test ADX calculation"""
    from src.signals.technical_indicators import TechnicalIndicators

    adx = TechnicalIndicators.calculate_adx(sample_ohlc, period=14)

    assert len(adx) == len(sample_ohlc)
    assert adx.isna().sum() < len(sample_ohlc)  # Some NaN at start
    assert (adx.dropna() >= 0).all()  # ADX is positive
    assert (adx.dropna() <= 100).all()  # ADX max is 100


def test_calculate_ema(sample_ohlc):
    """Test EMA calculation"""
    from src.signals.technical_indicators import TechnicalIndicators

    ema = TechnicalIndicators.calculate_ema(sample_ohlc['close'], period=20)

    assert len(ema) == len(sample_ohlc)
    assert ema.isna().sum() < len(sample_ohlc)
    # EMA should be close to price
    assert abs(ema.iloc[-1] - sample_ohlc['close'].iloc[-1]) < 20


def test_calculate_dma(sample_ohlc):
    """Test DMA calculation"""
    from src.signals.technical_indicators import TechnicalIndicators

    dma = TechnicalIndicators.calculate_dma(
        sample_ohlc['close'],
        ema_period=20,
        displacement_pct=5.0
    )

    assert len(dma) == len(sample_ohlc)
    # DMA should be below EMA due to displacement
    ema = TechnicalIndicators.calculate_ema(sample_ohlc['close'], 20)
    assert (dma.dropna() < ema.dropna()).all()


def test_calculate_atr(sample_ohlc):
    """Test ATR calculation"""
    from src.signals.technical_indicators import TechnicalIndicators

    atr = TechnicalIndicators.calculate_atr(sample_ohlc, period=14)

    assert len(atr) == len(sample_ohlc)
    assert atr.isna().sum() < len(sample_ohlc)
    assert (atr.dropna() > 0).all()  # ATR is always positive
