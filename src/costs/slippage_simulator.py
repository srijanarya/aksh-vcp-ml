"""Slippage Simulator (SHORT-037 to SHORT-039)"""


class SlippageSimulator:
    """Simulate slippage based on spread and liquidity"""

    def __init__(
        self,
        spread_based_pct: float = 0.05,
        liquidity_factor: float = 0.01
    ):
        """
        Initialize slippage simulator

        Args:
            spread_based_pct: Base slippage % from spread
            liquidity_factor: Additional slippage factor for liquidity
        """
        self.spread_based_pct = spread_based_pct
        self.liquidity_factor = liquidity_factor

    def calculate_slippage(
        self,
        price: float,
        volume: int,
        avg_volume: int
    ) -> float:
        """
        Calculate slippage

        Args:
            price: Entry/exit price
            volume: Trade volume
            avg_volume: Average daily volume

        Returns:
            Slippage amount
        """
        # Spread-based slippage
        spread_slippage = price * (self.spread_based_pct / 100)

        # Liquidity-based slippage
        liquidity_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        liquidity_slippage = price * (self.liquidity_factor / 100) * liquidity_ratio

        # Total slippage
        return spread_slippage + liquidity_slippage
