"""Profit-Based Kelly Scaling (SHORT-019)"""


class ProfitBasedKellyScaling:
    """Scale Kelly fraction based on cumulative profits"""

    def scale(
        self,
        kelly_fraction: float,
        cumulative_profit: float,
        initial_capital: float
    ) -> float:
        """
        Scale Kelly fraction based on profits

        Start with Half-Kelly, scale up to Full Kelly as profits grow.

        Args:
            kelly_fraction: Full Kelly fraction
            cumulative_profit: Cumulative profit amount
            initial_capital: Initial capital

        Returns:
            Scaled Kelly fraction
        """
        if cumulative_profit <= 0:
            # Start with Half-Kelly if no profits
            return kelly_fraction * 0.5

        profit_pct = (cumulative_profit / initial_capital) * 100

        if profit_pct >= 20:
            # Full Kelly after 20% profit
            return kelly_fraction
        elif profit_pct >= 10:
            # 3/4 Kelly after 10% profit
            return kelly_fraction * 0.75
        else:
            # Half Kelly otherwise
            return kelly_fraction * 0.5
