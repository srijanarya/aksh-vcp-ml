"""Tests for Signal Strength Scorer (SHORT-029)"""

import pytest
import pandas as pd
import numpy as np
from src.signals.signal_strength_scorer import SignalStrengthScorer


class TestSignalStrengthScorer:
    """Test suite for Signal Strength Scorer"""

    def test_perfect_signal(self):
        """TC-1: Perfect signal scores 100"""
        scorer = SignalStrengthScorer()

        # Strong trend (ADX=50), well above DMA (10%), high volume (2x)
        score = scorer.score_signal(
            close=110,
            adx=50,
            dma=100,
            volume=200000,
            avg_volume=100000
        )

        assert score == pytest.approx(100, abs=5)

    def test_weak_signal(self):
        """TC-2: Weak signal scores low"""
        scorer = SignalStrengthScorer()

        # Weak trend (ADX=20), near DMA (1%), low volume (0.5x)
        score = scorer.score_signal(
            close=101,
            adx=20,
            dma=100,
            volume=50000,
            avg_volume=100000
        )

        assert score < 20

    def test_adx_component_scoring(self):
        """TC-3: ADX component scoring"""
        scorer = SignalStrengthScorer()

        # Hold DMA and volume constant, vary ADX
        # ADX = 25 (threshold) -> component score ~0
        score_25 = scorer.score_signal(
            close=105, adx=25, dma=100, volume=100000, avg_volume=100000
        )

        # ADX = 37.5 (mid) -> component score ~50
        score_mid = scorer.score_signal(
            close=105, adx=37.5, dma=100, volume=100000, avg_volume=100000
        )

        # ADX = 50 (strong) -> component score ~100
        score_50 = scorer.score_signal(
            close=105, adx=50, dma=100, volume=100000, avg_volume=100000
        )

        assert score_25 < score_mid < score_50

    def test_dma_component_scoring(self):
        """TC-4: DMA component scoring"""
        scorer = SignalStrengthScorer()

        # Hold ADX and volume constant, vary distance above DMA
        # At DMA (0%) -> low score
        score_at = scorer.score_signal(
            close=100, adx=30, dma=100, volume=100000, avg_volume=100000
        )

        # 5% above DMA -> medium score
        score_5pct = scorer.score_signal(
            close=105, adx=30, dma=100, volume=100000, avg_volume=100000
        )

        # 10% above DMA -> high score
        score_10pct = scorer.score_signal(
            close=110, adx=30, dma=100, volume=100000, avg_volume=100000
        )

        assert score_at < score_5pct < score_10pct

    def test_volume_component_scoring(self):
        """TC-5: Volume component scoring"""
        scorer = SignalStrengthScorer()

        # Hold ADX and DMA constant, vary volume
        # Below avg volume -> low score (volume component = 0)
        score_low = scorer.score_signal(
            close=105, adx=30, dma=100, volume=50000, avg_volume=100000
        )

        # At avg volume -> same as low (volume component still 0, needs >1x)
        score_avg = scorer.score_signal(
            close=105, adx=30, dma=100, volume=100000, avg_volume=100000
        )

        # 1.5x avg volume -> medium score
        score_medium = scorer.score_signal(
            close=105, adx=30, dma=100, volume=150000, avg_volume=100000
        )

        # 2x avg volume -> high score
        score_high = scorer.score_signal(
            close=105, adx=30, dma=100, volume=200000, avg_volume=100000
        )

        # At/below average should be same (0 volume component)
        assert score_low == pytest.approx(score_avg)
        # Higher volume should increase score
        assert score_avg < score_medium < score_high

    def test_custom_weights(self):
        """TC-6: Custom component weights"""
        # ADX-heavy weighting
        scorer_adx = SignalStrengthScorer(
            adx_weight=0.70,
            dma_weight=0.20,
            volume_weight=0.10
        )

        # Strong ADX, weak other components
        score = scorer_adx.score_signal(
            close=101, adx=50, dma=100, volume=50000, avg_volume=100000
        )

        # Should score higher than balanced weights due to strong ADX
        assert score > 40

    def test_score_signals_dataframe(self):
        """TC-7: Score signals in DataFrame"""
        scorer = SignalStrengthScorer()

        # Create sample data
        df = pd.DataFrame({
            'close': [100, 102, 105, 108, 110],
            'volume': [100000, 120000, 150000, 180000, 200000]
        })

        adx = pd.Series([25, 28, 32, 40, 50])
        dma = pd.Series([95, 96, 98, 100, 102])

        scores = scorer.score_signals(df, adx, dma, volume_period=3)

        # Scores should generally increase as trend strengthens
        assert len(scores) == len(df)
        assert all(0 <= s <= 100 for s in scores)

    def test_nan_handling(self):
        """TC-8: Handle NaN values"""
        scorer = SignalStrengthScorer()

        df = pd.DataFrame({
            'close': [np.nan, 100, 105, 110],
            'volume': [100000, np.nan, 150000, 200000]
        })

        adx = pd.Series([np.nan, 30, 35, 40])
        dma = pd.Series([95, 96, np.nan, 100])

        scores = scorer.score_signals(df, adx, dma, volume_period=2)

        # NaN rows should have score 0
        assert scores.iloc[0] == 0
        assert scores.iloc[1] == 0  # NaN volume -> NaN avg_volume
        assert scores.iloc[2] == 0  # NaN dma

    def test_get_score_breakdown(self):
        """TC-9: Get detailed score breakdown"""
        scorer = SignalStrengthScorer()

        breakdown = scorer.get_score_breakdown(
            close=108,
            adx=40,
            dma=100,
            volume=150000,
            avg_volume=100000
        )

        assert 'adx_score' in breakdown
        assert 'dma_score' in breakdown
        assert 'volume_score' in breakdown
        assert 'total_score' in breakdown
        assert 'adx_weight' in breakdown

        # Component scores should be 0-100
        assert 0 <= breakdown['adx_score'] <= 100
        assert 0 <= breakdown['dma_score'] <= 100
        assert 0 <= breakdown['volume_score'] <= 100

        # Weights should sum to 100
        total_weight = (
            breakdown['adx_weight'] +
            breakdown['dma_weight'] +
            breakdown['volume_weight']
        )
        assert total_weight == pytest.approx(100, abs=0.1)

    def test_score_below_dma(self):
        """TC-10: Price below DMA scores low"""
        scorer = SignalStrengthScorer()

        # Price below DMA should score 0 on DMA component
        score = scorer.score_signal(
            close=95,
            adx=40,
            dma=100,
            volume=150000,
            avg_volume=100000
        )

        breakdown = scorer.get_score_breakdown(
            close=95, adx=40, dma=100, volume=150000, avg_volume=100000
        )

        assert breakdown['dma_score'] == 0

    def test_very_high_adx(self):
        """TC-11: Very high ADX capped at 100"""
        scorer = SignalStrengthScorer()

        # ADX > 50 should still score 100 (not exceed)
        breakdown = scorer.get_score_breakdown(
            close=105, adx=80, dma=100, volume=100000, avg_volume=100000
        )

        assert breakdown['adx_score'] == 100

    def test_very_high_volume(self):
        """TC-12: Very high volume capped at 100"""
        scorer = SignalStrengthScorer()

        # 5x volume should score 100 (not exceed)
        breakdown = scorer.get_score_breakdown(
            close=105, adx=30, dma=100, volume=500000, avg_volume=100000
        )

        assert breakdown['volume_score'] == 100

    def test_zero_average_volume(self):
        """TC-13: Zero average volume handling"""
        scorer = SignalStrengthScorer()

        # Should not crash with zero avg volume
        score = scorer.score_signal(
            close=105, adx=30, dma=100, volume=100000, avg_volume=0
        )

        assert score >= 0
        assert score <= 100

    def test_equal_weights(self):
        """TC-14: Equal component weights"""
        scorer = SignalStrengthScorer(
            adx_weight=1.0,
            dma_weight=1.0,
            volume_weight=1.0
        )

        breakdown = scorer.get_score_breakdown(
            close=105, adx=30, dma=100, volume=100000, avg_volume=100000
        )

        # Each component should have ~33.3% weight
        assert breakdown['adx_weight'] == pytest.approx(33.3, abs=0.1)
        assert breakdown['dma_weight'] == pytest.approx(33.3, abs=0.1)
        assert breakdown['volume_weight'] == pytest.approx(33.3, abs=0.1)

    def test_realistic_trading_scenarios(self):
        """TC-15: Realistic trading scenarios"""
        scorer = SignalStrengthScorer()

        # Strong setup: ADX=45, 8% above DMA, 1.8x volume
        strong_score = scorer.score_signal(
            close=108, adx=45, dma=100, volume=180000, avg_volume=100000
        )

        # Moderate setup: ADX=35, 5% above DMA, 1.5x volume
        moderate_score = scorer.score_signal(
            close=105, adx=35, dma=100, volume=150000, avg_volume=100000
        )

        # Weak setup: ADX=26, 2% above DMA, 0.9x volume
        weak_score = scorer.score_signal(
            close=102, adx=26, dma=100, volume=90000, avg_volume=100000
        )

        assert strong_score > moderate_score > weak_score
        assert strong_score > 50
        assert moderate_score > 25
        assert weak_score < 25

    def test_score_consistency(self):
        """TC-16: Score consistency"""
        scorer = SignalStrengthScorer()

        # Same inputs should give same score
        score1 = scorer.score_signal(105, 35, 100, 150000, 100000)
        score2 = scorer.score_signal(105, 35, 100, 150000, 100000)
        score3 = scorer.score_signal(105, 35, 100, 150000, 100000)

        assert score1 == score2 == score3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.signals.signal_strength_scorer", "--cov-report=term-missing"])
