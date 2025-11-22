"""Sentiment-Based Kelly Adjuster (SHORT-023)"""


class SentimentKellyAdjuster:
    """Adjust Kelly fraction based on market sentiment"""

    def __init__(
        self,
        bearish_threshold: float = -0.3,
        bullish_threshold: float = 0.3,
        bearish_scale: float = 0.5,
        neutral_scale: float = 0.75,
        bullish_scale: float = 1.0
    ):
        """
        Initialize adjuster

        Args:
            bearish_threshold: Sentiment below this is bearish
            bullish_threshold: Sentiment above this is bullish
            bearish_scale: Kelly scale factor in bearish sentiment
            neutral_scale: Kelly scale factor in neutral sentiment
            bullish_scale: Kelly scale factor in bullish sentiment
        """
        self.bearish_threshold = bearish_threshold
        self.bullish_threshold = bullish_threshold
        self.bearish_scale = bearish_scale
        self.neutral_scale = neutral_scale
        self.bullish_scale = bullish_scale

    def adjust(self, kelly_fraction: float, sentiment_score: float) -> float:
        """
        Adjust Kelly fraction based on sentiment

        Args:
            kelly_fraction: Base Kelly fraction
            sentiment_score: Sentiment score (-1 to +1)

        Returns:
            Adjusted Kelly fraction
        """
        # Clamp sentiment to valid range
        sentiment_score = max(-1.0, min(1.0, sentiment_score))

        # Determine sentiment regime
        if sentiment_score < self.bearish_threshold:
            scale = self.bearish_scale
        elif sentiment_score > self.bullish_threshold:
            scale = self.bullish_scale
        else:
            scale = self.neutral_scale

        return kelly_fraction * scale

    def get_sentiment_regime(self, sentiment_score: float) -> str:
        """
        Get sentiment regime label

        Args:
            sentiment_score: Sentiment score (-1 to +1)

        Returns:
            Regime label: "bearish", "neutral", or "bullish"
        """
        if sentiment_score < self.bearish_threshold:
            return "bearish"
        elif sentiment_score > self.bullish_threshold:
            return "bullish"
        else:
            return "neutral"
