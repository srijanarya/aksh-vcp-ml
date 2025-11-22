"""Cost Calculators (SHORT-034 to SHORT-036)"""


class CostCalculator:
    """Calculate trading costs for different instrument types"""

    def __init__(
        self,
        equity_delivery_brokerage: float = 0.0,
        equity_delivery_stt: float = 0.1,
        equity_delivery_other: float = 0.0335,
        intraday_brokerage: float = 0.03,
        intraday_stt: float = 0.025,
        intraday_other: float = 0.0335,
        fno_brokerage: float = 20.0,  # Flat per order
        fno_stt: float = 0.0625,
        fno_other: float = 0.053
    ):
        """
        Initialize cost calculator

        Args:
            equity_delivery_*: Costs for equity delivery (%)
            intraday_*: Costs for intraday (%)
            fno_*: Costs for F&O
        """
        self.equity_delivery_brokerage = equity_delivery_brokerage
        self.equity_delivery_stt = equity_delivery_stt
        self.equity_delivery_other = equity_delivery_other

        self.intraday_brokerage = intraday_brokerage
        self.intraday_stt = intraday_stt
        self.intraday_other = intraday_other

        self.fno_brokerage = fno_brokerage
        self.fno_stt = fno_stt
        self.fno_other = fno_other

    def calculate_equity_delivery_cost(self, value: float) -> float:
        """
        Calculate equity delivery cost

        Args:
            value: Trade value

        Returns:
            Total cost
        """
        brokerage = value * (self.equity_delivery_brokerage / 100)
        stt = value * (self.equity_delivery_stt / 100)
        other = value * (self.equity_delivery_other / 100)

        return brokerage + stt + other

    def calculate_intraday_cost(self, value: float) -> float:
        """
        Calculate intraday cost

        Args:
            value: Trade value

        Returns:
            Total cost
        """
        brokerage = value * (self.intraday_brokerage / 100)
        stt = value * (self.intraday_stt / 100)
        other = value * (self.intraday_other / 100)

        return brokerage + stt + other

    def calculate_fno_cost(self, value: float) -> float:
        """
        Calculate F&O cost

        Args:
            value: Trade value

        Returns:
            Total cost
        """
        brokerage = self.fno_brokerage  # Flat
        stt = value * (self.fno_stt / 100)
        other = value * (self.fno_other / 100)

        return brokerage + stt + other
