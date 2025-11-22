"""Position Cap Enforcer (SHORT-020)"""


class PositionCapEnforcer:
    """Enforce position size caps (20% equity, 4% F&O)"""

    def __init__(self, equity_cap: float = 20.0, fno_cap: float = 4.0):
        """
        Initialize enforcer

        Args:
            equity_cap: Max % of capital in single equity position
            fno_cap: Max % of capital in single F&O position
        """
        self.equity_cap = equity_cap
        self.fno_cap = fno_cap

    def enforce(
        self,
        kelly_fraction: float,
        instrument_type: str = "equity"
    ) -> float:
        """
        Enforce position caps

        Args:
            kelly_fraction: Calculated Kelly fraction
            instrument_type: "equity" or "fno"

        Returns:
            Capped Kelly fraction
        """
        cap = self.equity_cap if instrument_type == "equity" else self.fno_cap
        cap_fraction = cap / 100

        return min(kelly_fraction, cap_fraction)
