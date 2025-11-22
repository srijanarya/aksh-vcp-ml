"""Total Risk Constraint Validator (SHORT-021)"""


class TotalRiskValidator:
    """Validate total portfolio risk constraints"""

    def __init__(self, max_total_risk: float = 0.50):
        """
        Initialize validator

        Args:
            max_total_risk: Maximum total risk as fraction of capital (default 50%)
        """
        self.max_total_risk = max_total_risk

    def validate_new_position(
        self,
        proposed_position_size: float,
        existing_positions: list[float]
    ) -> float:
        """
        Validate and potentially scale down new position to maintain risk limits

        Args:
            proposed_position_size: Proposed new position size as fraction
            existing_positions: List of existing position sizes as fractions

        Returns:
            Validated position size (may be scaled down or 0 if at limit)
        """
        current_risk = self.get_current_total_risk(existing_positions)
        available_risk = self.max_total_risk - current_risk

        if available_risk <= 0:
            return 0.0

        return min(proposed_position_size, available_risk)

    def get_current_total_risk(self, positions: list[float]) -> float:
        """
        Calculate current total portfolio risk

        Args:
            positions: List of position sizes as fractions

        Returns:
            Total risk as fraction of capital
        """
        return sum(positions)

    def can_add_position(
        self,
        proposed_position_size: float,
        existing_positions: list[float]
    ) -> bool:
        """
        Check if new position can be added without exceeding risk limit

        Args:
            proposed_position_size: Proposed new position size
            existing_positions: List of existing position sizes

        Returns:
            True if position can be added, False otherwise
        """
        validated_size = self.validate_new_position(
            proposed_position_size,
            existing_positions
        )
        return validated_size > 0

    def get_max_position_size(self, existing_positions: list[float]) -> float:
        """
        Get maximum allowable position size given existing positions

        Args:
            existing_positions: List of existing position sizes

        Returns:
            Maximum allowable new position size
        """
        current_risk = self.get_current_total_risk(existing_positions)
        return max(0.0, self.max_total_risk - current_risk)
