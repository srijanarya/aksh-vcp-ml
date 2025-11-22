"""Half-Kelly Implementation (SHORT-018)"""


class HalfKellyCalculator:
    """Calculate Half-Kelly (more conservative than full Kelly)"""

    def calculate(self, kelly_fraction: float) -> float:
        """
        Calculate Half-Kelly fraction

        Args:
            kelly_fraction: Full Kelly fraction

        Returns:
            Half of Kelly fraction
        """
        return kelly_fraction * 0.5
