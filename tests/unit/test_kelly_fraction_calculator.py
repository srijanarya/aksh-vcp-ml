"""Tests for Kelly Fraction Calculator (SHORT-017)"""

import pytest


class TestKellyFractionCalculator:
    """Test Kelly fraction calculation"""

    def test_calculate_kelly_fraction(self):
        """Test basic Kelly fraction calculation"""
        from src.kelly.kelly_fraction_calculator import KellyFractionCalculator

        calc = KellyFractionCalculator()

        # Win rate = 60%, Avg win = 100, Avg loss = -50
        # R = 100/50 = 2, W = 0.6, L = 0.4
        # F = (0.6 * 2 - 0.4) / 2 = (1.2 - 0.4) / 2 = 0.4
        fraction = calc.calculate(
            win_rate=60.0,
            avg_profit=100,
            avg_loss=-50
        )

        assert fraction == pytest.approx(0.4, abs=0.01)

    def test_handle_zero_trades(self):
        """Test with no trading history"""
        from src.kelly.kelly_fraction_calculator import KellyFractionCalculator

        calc = KellyFractionCalculator()

        fraction = calc.calculate(
            win_rate=0,
            avg_profit=0,
            avg_loss=0
        )

        assert fraction == 0

    def test_handle_perfect_win_rate(self):
        """Test with 100% win rate"""
        from src.kelly.kelly_fraction_calculator import KellyFractionCalculator

        calc = KellyFractionCalculator()

        fraction = calc.calculate(
            win_rate=100.0,
            avg_profit=100,
            avg_loss=0
        )

        # Should cap at reasonable max
        assert 0 <= fraction <= 1

    def test_negative_kelly_returns_zero(self):
        """Test that negative Kelly returns 0"""
        from src.kelly.kelly_fraction_calculator import KellyFractionCalculator

        calc = KellyFractionCalculator()

        # Losing strategy
        fraction = calc.calculate(
            win_rate=30.0,
            avg_profit=50,
            avg_loss=-100
        )

        assert fraction == 0

    def test_validate_inputs(self):
        """Test input validation"""
        from src.kelly.kelly_fraction_calculator import KellyFractionCalculator

        calc = KellyFractionCalculator()

        # Invalid win rate
        with pytest.raises(ValueError):
            calc.calculate(win_rate=150.0, avg_profit=100, avg_loss=-50)

        # Invalid avg_loss (should be negative)
        with pytest.raises(ValueError):
            calc.calculate(win_rate=60.0, avg_profit=100, avg_loss=50)
