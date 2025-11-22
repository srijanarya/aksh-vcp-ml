"""
Kelly Fraction Calculator (SHORT-017)

Calculate optimal position size using Kelly formula.
"""


class KellyFractionCalculator:
    """Calculate Kelly fraction for position sizing"""

    def calculate(
        self,
        win_rate: float,
        avg_profit: float,
        avg_loss: float
    ) -> float:
        """
        Calculate Kelly fraction

        Formula: F = (W * R - L) / R
        where:
            W = win rate (as decimal, e.g., 0.6 for 60%)
            R = reward/risk ratio (avg_profit / abs(avg_loss))
            L = loss rate (1 - W)

        Args:
            win_rate: Win rate as percentage (0-100)
            avg_profit: Average profit per winning trade (positive)
            avg_loss: Average loss per losing trade (negative)

        Returns:
            Kelly fraction between 0 and 1

        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if win_rate < 0 or win_rate > 100:
            raise ValueError("Win rate must be between 0 and 100")

        if avg_loss > 0:
            raise ValueError("avg_loss must be negative or zero")

        # Handle zero trades case
        if win_rate == 0 or avg_profit == 0:
            return 0.0

        # Handle perfect win rate
        if win_rate == 100 or avg_loss == 0:
            # No losses, but be conservative
            return min(0.25, 1.0)  # Cap at 25% for safety

        # Convert win rate to decimal
        W = win_rate / 100

        # Calculate reward/risk ratio
        R = avg_profit / abs(avg_loss)

        # Calculate loss rate
        L = 1 - W

        # Kelly formula
        kelly = (W * R - L) / R

        # Cap at 0 if negative (losing strategy)
        if kelly < 0:
            return 0.0

        # Cap at 1 (never bet more than 100%)
        return min(kelly, 1.0)
