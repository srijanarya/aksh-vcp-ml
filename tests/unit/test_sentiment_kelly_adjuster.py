"""Tests for Sentiment-Based Kelly Adjuster (SHORT-023)"""

import pytest
from src.kelly.sentiment_kelly_adjuster import SentimentKellyAdjuster


class TestSentimentKellyAdjuster:
    """Test suite for Sentiment-Based Kelly Adjuster"""

    def test_bearish_sentiment_scale(self):
        """TC-1: Bearish sentiment reduces to 50% Kelly"""
        adjuster = SentimentKellyAdjuster()

        assert adjuster.adjust(0.20, -0.5) == pytest.approx(0.10)
        assert adjuster.adjust(0.30, -0.8) == pytest.approx(0.15)
        assert adjuster.adjust(0.40, -1.0) == pytest.approx(0.20)

    def test_bullish_sentiment_scale(self):
        """TC-2: Bullish sentiment uses full Kelly"""
        adjuster = SentimentKellyAdjuster()

        assert adjuster.adjust(0.20, 0.5) == pytest.approx(0.20)
        assert adjuster.adjust(0.30, 0.8) == pytest.approx(0.30)
        assert adjuster.adjust(0.40, 1.0) == pytest.approx(0.40)

    def test_neutral_sentiment_scale(self):
        """TC-3: Neutral sentiment uses 75% Kelly"""
        adjuster = SentimentKellyAdjuster()

        assert adjuster.adjust(0.20, 0.0) == pytest.approx(0.15)
        assert adjuster.adjust(0.20, 0.1) == pytest.approx(0.15)
        assert adjuster.adjust(0.20, -0.1) == pytest.approx(0.15)
        assert adjuster.adjust(0.40, 0.2) == pytest.approx(0.30)

    def test_threshold_boundaries(self):
        """TC-4: Test exact threshold boundaries"""
        adjuster = SentimentKellyAdjuster(
            bearish_threshold=-0.3,
            bullish_threshold=0.3
        )

        # Just below bearish threshold
        assert adjuster.adjust(0.20, -0.31) == pytest.approx(0.10)

        # At bearish threshold (neutral)
        assert adjuster.adjust(0.20, -0.30) == pytest.approx(0.15)

        # Just above bullish threshold
        assert adjuster.adjust(0.20, 0.31) == pytest.approx(0.20)

        # At bullish threshold (neutral)
        assert adjuster.adjust(0.20, 0.30) == pytest.approx(0.15)

    def test_custom_thresholds(self):
        """TC-5: Custom threshold values"""
        adjuster = SentimentKellyAdjuster(
            bearish_threshold=-0.5,
            bullish_threshold=0.5
        )

        # Wider neutral band
        assert adjuster.adjust(0.20, -0.4) == pytest.approx(0.15)  # Neutral
        assert adjuster.adjust(0.20, 0.4) == pytest.approx(0.15)   # Neutral
        assert adjuster.adjust(0.20, -0.6) == pytest.approx(0.10)  # Bearish
        assert adjuster.adjust(0.20, 0.6) == pytest.approx(0.20)   # Bullish

    def test_custom_scale_factors(self):
        """TC-6: Custom scale factors"""
        adjuster = SentimentKellyAdjuster(
            bearish_scale=0.25,   # More conservative
            neutral_scale=0.60,
            bullish_scale=1.25    # More aggressive
        )

        assert adjuster.adjust(0.20, -0.5) == pytest.approx(0.05)   # 25%
        assert adjuster.adjust(0.20, 0.0) == pytest.approx(0.12)    # 60%
        assert adjuster.adjust(0.20, 0.5) == pytest.approx(0.25)    # 125%

    def test_sentiment_score_clamping(self):
        """TC-7: Sentiment scores outside -1 to +1 are clamped"""
        adjuster = SentimentKellyAdjuster()

        # Values beyond -1 to +1 should be clamped
        assert adjuster.adjust(0.20, -1.5) == pytest.approx(0.10)  # Clamped to -1
        assert adjuster.adjust(0.20, 1.5) == pytest.approx(0.20)   # Clamped to +1
        assert adjuster.adjust(0.20, -2.0) == pytest.approx(0.10)
        assert adjuster.adjust(0.20, 2.0) == pytest.approx(0.20)

    def test_zero_kelly_fraction(self):
        """TC-8: Zero Kelly fraction"""
        adjuster = SentimentKellyAdjuster()

        assert adjuster.adjust(0.0, -0.5) == pytest.approx(0.0)
        assert adjuster.adjust(0.0, 0.0) == pytest.approx(0.0)
        assert adjuster.adjust(0.0, 0.5) == pytest.approx(0.0)

    def test_get_sentiment_regime(self):
        """TC-9: Get sentiment regime labels"""
        adjuster = SentimentKellyAdjuster()

        assert adjuster.get_sentiment_regime(-0.5) == "bearish"
        assert adjuster.get_sentiment_regime(-0.3) == "neutral"
        assert adjuster.get_sentiment_regime(0.0) == "neutral"
        assert adjuster.get_sentiment_regime(0.3) == "neutral"
        assert adjuster.get_sentiment_regime(0.5) == "bullish"
        assert adjuster.get_sentiment_regime(-1.0) == "bearish"
        assert adjuster.get_sentiment_regime(1.0) == "bullish"

    def test_realistic_sentiment_scenarios(self):
        """TC-10: Realistic trading scenarios"""
        adjuster = SentimentKellyAdjuster()
        kelly = 0.25

        # Scenario 1: Market crash (very bearish)
        adjusted = adjuster.adjust(kelly, -0.9)
        assert adjusted == pytest.approx(0.125)
        assert adjuster.get_sentiment_regime(-0.9) == "bearish"

        # Scenario 2: Mild uncertainty (slightly bearish)
        adjusted = adjuster.adjust(kelly, -0.2)
        assert adjusted == pytest.approx(0.1875)  # Neutral
        assert adjuster.get_sentiment_regime(-0.2) == "neutral"

        # Scenario 3: Strong rally (bullish)
        adjusted = adjuster.adjust(kelly, 0.7)
        assert adjusted == pytest.approx(0.25)
        assert adjuster.get_sentiment_regime(0.7) == "bullish"

    def test_combined_with_other_kelly_adjustments(self):
        """TC-11: Combining with other Kelly adjustments"""
        adjuster = SentimentKellyAdjuster()

        # Start with Half-Kelly (0.10)
        half_kelly = 0.20 * 0.5

        # Apply sentiment adjustment (bearish)
        sentiment_adjusted = adjuster.adjust(half_kelly, -0.5)
        assert sentiment_adjusted == pytest.approx(0.05)  # 50% of Half-Kelly

        # Apply sentiment adjustment (bullish)
        sentiment_adjusted = adjuster.adjust(half_kelly, 0.5)
        assert sentiment_adjusted == pytest.approx(0.10)  # Full Half-Kelly

    def test_extreme_sentiment_values(self):
        """TC-12: Extreme sentiment values"""
        adjuster = SentimentKellyAdjuster()

        # Most bearish
        assert adjuster.adjust(0.30, -1.0) == pytest.approx(0.15)

        # Most bullish
        assert adjuster.adjust(0.30, 1.0) == pytest.approx(0.30)

    def test_small_kelly_fractions(self):
        """TC-13: Small Kelly fractions"""
        adjuster = SentimentKellyAdjuster()

        assert adjuster.adjust(0.01, -0.5) == pytest.approx(0.005)
        assert adjuster.adjust(0.01, 0.0) == pytest.approx(0.0075)
        assert adjuster.adjust(0.01, 0.5) == pytest.approx(0.01)

    def test_large_kelly_fractions(self):
        """TC-14: Large Kelly fractions"""
        adjuster = SentimentKellyAdjuster()

        assert adjuster.adjust(0.80, -0.5) == pytest.approx(0.40)
        assert adjuster.adjust(0.80, 0.0) == pytest.approx(0.60)
        assert adjuster.adjust(0.80, 0.5) == pytest.approx(0.80)

    def test_negative_kelly_fraction(self):
        """TC-15: Negative Kelly (no edge)"""
        adjuster = SentimentKellyAdjuster()

        # Negative Kelly should still be scaled
        assert adjuster.adjust(-0.10, -0.5) == pytest.approx(-0.05)
        assert adjuster.adjust(-0.10, 0.0) == pytest.approx(-0.075)
        assert adjuster.adjust(-0.10, 0.5) == pytest.approx(-0.10)

    def test_consistency_across_calls(self):
        """TC-16: Consistency across multiple calls"""
        adjuster = SentimentKellyAdjuster()

        result1 = adjuster.adjust(0.25, 0.5)
        result2 = adjuster.adjust(0.25, 0.5)
        result3 = adjuster.adjust(0.25, 0.5)

        assert result1 == result2 == result3 == pytest.approx(0.25)

    def test_gradual_sentiment_changes(self):
        """TC-17: Gradual sentiment changes"""
        adjuster = SentimentKellyAdjuster()
        kelly = 0.20

        # Sentiment improving from bearish to bullish
        sentiments = [-0.8, -0.5, -0.3, -0.1, 0.0, 0.1, 0.3, 0.5, 0.8]
        results = [adjuster.adjust(kelly, s) for s in sentiments]

        # Bearish regime
        assert results[0] == pytest.approx(0.10)  # -0.8
        assert results[1] == pytest.approx(0.10)  # -0.5

        # Neutral regime
        assert results[2] == pytest.approx(0.15)  # -0.3
        assert results[3] == pytest.approx(0.15)  # -0.1
        assert results[4] == pytest.approx(0.15)  # 0.0
        assert results[5] == pytest.approx(0.15)  # 0.1
        assert results[6] == pytest.approx(0.15)  # 0.3

        # Bullish regime
        assert results[7] == pytest.approx(0.20)  # 0.5
        assert results[8] == pytest.approx(0.20)  # 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.kelly.sentiment_kelly_adjuster", "--cov-report=term-missing"])
