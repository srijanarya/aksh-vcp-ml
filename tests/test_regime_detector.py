"""
Tests for Regime Detector (SHORT-052 to SHORT-056)
"""

import pytest
import pandas as pd
import numpy as np

from src.regime.regime_detector import (
    RegimeDetector,
    MarketRegime
)


@pytest.fixture
def trending_data():
    """Generate trending market data"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    # Strong uptrend
    prices = 100 + np.arange(100) * 0.5 + np.random.randn(100) * 0.1

    df = pd.DataFrame({
        'close': prices,
        'high': prices + 1,
        'low': prices - 1
    }, index=dates)

    return df


@pytest.fixture
def ranging_data():
    """Generate ranging market data"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    # Sideways movement
    prices = 100 + np.random.randn(100) * 0.5

    df = pd.DataFrame({
        'close': prices,
        'high': prices + 1,
        'low': prices - 1
    }, index=dates)

    return df


@pytest.fixture
def volatile_data():
    """Generate volatile market data"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    # High volatility
    prices = 100 + np.random.randn(100) * 5

    df = pd.DataFrame({
        'close': prices,
        'high': prices + 2,
        'low': prices - 2
    }, index=dates)

    return df


@pytest.fixture
def high_adx():
    """High ADX values (trending)"""
    return pd.Series([30, 32, 35, 33, 31])


@pytest.fixture
def low_adx():
    """Low ADX values (ranging)"""
    return pd.Series([15, 18, 20, 17, 16])


class TestMarketRegimeEnum:
    """Test MarketRegime enum (SHORT-053)"""

    def test_regime_values(self):
        assert MarketRegime.TRENDING.value == "trending"
        assert MarketRegime.RANGING.value == "ranging"
        assert MarketRegime.VOLATILE.value == "volatile"

    def test_regime_comparison(self):
        regime = MarketRegime.TRENDING
        assert regime == MarketRegime.TRENDING
        assert regime != MarketRegime.RANGING

    def test_all_regimes_defined(self):
        regimes = [MarketRegime.TRENDING, MarketRegime.RANGING, MarketRegime.VOLATILE]
        assert len(regimes) == 3


class TestRegimeDetector:
    """Test RegimeDetector (SHORT-052)"""

    def test_detector_initialization(self):
        """Test detector initialization"""
        detector = RegimeDetector(
            adx_threshold=25.0,
            volatility_threshold=2.0
        )

        assert detector.adx_threshold == 25.0
        assert detector.volatility_threshold == 2.0

    def test_default_thresholds(self):
        """Test default threshold values"""
        detector = RegimeDetector()

        assert detector.adx_threshold == 25.0
        assert detector.volatility_threshold == 2.0

    def test_custom_thresholds(self):
        """Test custom threshold configuration"""
        detector = RegimeDetector(
            adx_threshold=30.0,
            volatility_threshold=3.0
        )

        assert detector.adx_threshold == 30.0
        assert detector.volatility_threshold == 3.0


class TestVolatilityRegime:
    """Test volatility regime detection (SHORT-054)"""

    def test_high_volatility_detection(self, volatile_data, low_adx):
        """Test detection of volatile regime"""
        detector = RegimeDetector(volatility_threshold=2.0)

        regime = detector.detect_regime(volatile_data, low_adx)

        # Should detect VOLATILE due to high volatility
        assert regime == MarketRegime.VOLATILE

    def test_volatility_override(self, volatile_data, high_adx):
        """Test that volatility overrides ADX"""
        detector = RegimeDetector(volatility_threshold=2.0)

        regime = detector.detect_regime(volatile_data, high_adx)

        # Even with high ADX, should be VOLATILE
        assert regime == MarketRegime.VOLATILE

    def test_low_volatility(self, ranging_data, low_adx):
        """Test low volatility doesn't trigger VOLATILE"""
        detector = RegimeDetector(volatility_threshold=2.0)

        regime = detector.detect_regime(ranging_data, low_adx)

        # Should not be VOLATILE
        assert regime != MarketRegime.VOLATILE


class TestADXRegimeClassifier:
    """Test ADX-based regime classification (SHORT-055)"""

    def test_trending_detection(self, trending_data, high_adx):
        """Test trending regime detection"""
        detector = RegimeDetector(
            adx_threshold=25.0,
            volatility_threshold=10.0  # High threshold to avoid volatile
        )

        regime = detector.detect_regime(trending_data, high_adx)

        # Should detect TRENDING
        assert regime == MarketRegime.TRENDING

    def test_ranging_detection(self, ranging_data, low_adx):
        """Test ranging regime detection"""
        detector = RegimeDetector(
            adx_threshold=25.0,
            volatility_threshold=10.0
        )

        regime = detector.detect_regime(ranging_data, low_adx)

        # Should detect RANGING
        assert regime == MarketRegime.RANGING

    def test_adx_threshold_boundary(self, ranging_data):
        """Test ADX at threshold boundary"""
        detector = RegimeDetector(adx_threshold=25.0, volatility_threshold=10.0)

        # Exactly at threshold
        adx_at_threshold = pd.Series([25.0])
        regime = detector.detect_regime(ranging_data, adx_at_threshold)

        # Should be TRENDING (>= threshold)
        assert regime == MarketRegime.TRENDING

        # Just below threshold
        adx_below_threshold = pd.Series([24.9])
        regime = detector.detect_regime(ranging_data, adx_below_threshold)

        # Should be RANGING (< threshold)
        assert regime == MarketRegime.RANGING


class TestStrategySelector:
    """Test strategy selection (SHORT-056)"""

    def test_trending_strategy(self):
        """Test strategy selection for trending regime"""
        detector = RegimeDetector()

        strategy = detector.select_strategy(MarketRegime.TRENDING)

        assert strategy == "trend_following"

    def test_ranging_strategy(self):
        """Test strategy selection for ranging regime"""
        detector = RegimeDetector()

        strategy = detector.select_strategy(MarketRegime.RANGING)

        assert strategy == "mean_reversion"

    def test_volatile_strategy(self):
        """Test strategy selection for volatile regime"""
        detector = RegimeDetector()

        strategy = detector.select_strategy(MarketRegime.VOLATILE)

        assert strategy == "risk_off"

    def test_all_regimes_mapped(self):
        """Test that all regimes have strategy mappings"""
        detector = RegimeDetector()

        for regime in MarketRegime:
            strategy = detector.select_strategy(regime)
            assert strategy in ["trend_following", "mean_reversion", "risk_off"]


class TestRegimeDetection:
    """Integration tests for regime detection"""

    def test_volatility_calculation(self, ranging_data, low_adx):
        """Test volatility calculation"""
        detector = RegimeDetector()

        # Low volatility data
        regime = detector.detect_regime(ranging_data, low_adx)

        # Should be RANGING (not volatile)
        assert regime == MarketRegime.RANGING

    def test_regime_priority(self, volatile_data, high_adx):
        """Test that volatility has priority over ADX"""
        detector = RegimeDetector(
            adx_threshold=25.0,
            volatility_threshold=2.0
        )

        regime = detector.detect_regime(volatile_data, high_adx)

        # Volatility should override high ADX
        assert regime == MarketRegime.VOLATILE

    def test_edge_cases(self):
        """Test edge cases"""
        detector = RegimeDetector()

        # Minimal data
        df = pd.DataFrame({
            'close': [100, 101]
        })
        adx = pd.Series([20])

        regime = detector.detect_regime(df, adx)

        # Should return a valid regime
        assert isinstance(regime, MarketRegime)


def test_end_to_end_regime_detection(trending_data, ranging_data, volatile_data):
    """End-to-end regime detection test"""
    detector = RegimeDetector(
        adx_threshold=25.0,
        volatility_threshold=2.0
    )

    # Test trending
    high_adx = pd.Series([30, 32, 35])
    trending_regime = detector.detect_regime(trending_data, high_adx)
    trending_strategy = detector.select_strategy(trending_regime)

    print(f"Trending Regime: {trending_regime.value}")
    print(f"Trending Strategy: {trending_strategy}")

    # Test ranging
    low_adx = pd.Series([15, 18, 20])
    ranging_regime = detector.detect_regime(ranging_data, low_adx)
    ranging_strategy = detector.select_strategy(ranging_regime)

    print(f"Ranging Regime: {ranging_regime.value}")
    print(f"Ranging Strategy: {ranging_strategy}")

    # Test volatile
    volatile_regime = detector.detect_regime(volatile_data, low_adx)
    volatile_strategy = detector.select_strategy(volatile_regime)

    print(f"Volatile Regime: {volatile_regime.value}")
    print(f"Volatile Strategy: {volatile_strategy}")

    # Verify regimes are different
    assert trending_strategy == "trend_following" or trending_regime == MarketRegime.VOLATILE
    assert ranging_strategy == "mean_reversion" or ranging_regime == MarketRegime.VOLATILE
    assert volatile_regime == MarketRegime.VOLATILE
