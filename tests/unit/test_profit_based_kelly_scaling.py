"""Tests for Profit-Based Kelly Scaling (SHORT-019)"""

import pytest
from src.kelly.profit_based_kelly_scaling import ProfitBasedKellyScaling


class TestProfitBasedKellyScaling:
    """Test suite for Profit-Based Kelly Scaling"""

    def test_half_kelly_at_start(self):
        """TC-1: Half-Kelly when no profit"""
        scaler = ProfitBasedKellyScaling()

        # Zero profit
        assert scaler.scale(0.20, 0, 100000) == pytest.approx(0.10)

        # Negative profit
        assert scaler.scale(0.20, -5000, 100000) == pytest.approx(0.10)
        assert scaler.scale(0.30, -10000, 100000) == pytest.approx(0.15)

    def test_half_kelly_below_10_percent(self):
        """TC-2: Half-Kelly when profit < 10%"""
        scaler = ProfitBasedKellyScaling()

        # 5% profit
        assert scaler.scale(0.20, 5000, 100000) == pytest.approx(0.10)

        # 9% profit
        assert scaler.scale(0.20, 9000, 100000) == pytest.approx(0.10)

    def test_three_quarter_kelly_at_10_percent(self):
        """TC-3: 3/4 Kelly when profit >= 10%"""
        scaler = ProfitBasedKellyScaling()

        # Exactly 10% profit
        assert scaler.scale(0.20, 10000, 100000) == pytest.approx(0.15)

        # 15% profit
        assert scaler.scale(0.20, 15000, 100000) == pytest.approx(0.15)

        # 19% profit (just before full Kelly)
        assert scaler.scale(0.20, 19000, 100000) == pytest.approx(0.15)

    def test_full_kelly_at_20_percent(self):
        """TC-4: Full Kelly when profit >= 20%"""
        scaler = ProfitBasedKellyScaling()

        # Exactly 20% profit
        assert scaler.scale(0.20, 20000, 100000) == pytest.approx(0.20)

        # 30% profit
        assert scaler.scale(0.20, 30000, 100000) == pytest.approx(0.20)

        # 100% profit
        assert scaler.scale(0.20, 100000, 100000) == pytest.approx(0.20)

    def test_different_kelly_fractions(self):
        """TC-5: Test with different Kelly fractions"""
        scaler = ProfitBasedKellyScaling()

        # Kelly = 0.10
        assert scaler.scale(0.10, 0, 100000) == pytest.approx(0.05)
        assert scaler.scale(0.10, 10000, 100000) == pytest.approx(0.075)
        assert scaler.scale(0.10, 20000, 100000) == pytest.approx(0.10)

        # Kelly = 0.30
        assert scaler.scale(0.30, 0, 100000) == pytest.approx(0.15)
        assert scaler.scale(0.30, 10000, 100000) == pytest.approx(0.225)
        assert scaler.scale(0.30, 20000, 100000) == pytest.approx(0.30)

    def test_different_initial_capitals(self):
        """TC-6: Test with different initial capital amounts"""
        scaler = ProfitBasedKellyScaling()

        # Small capital (₹50,000)
        assert scaler.scale(0.20, 5000, 50000) == pytest.approx(0.15)  # 10% profit
        assert scaler.scale(0.20, 10000, 50000) == pytest.approx(0.20)  # 20% profit

        # Large capital (₹10,00,000)
        assert scaler.scale(0.20, 100000, 1000000) == pytest.approx(0.15)  # 10% profit
        assert scaler.scale(0.20, 200000, 1000000) == pytest.approx(0.20)  # 20% profit

    def test_profit_percentage_boundaries(self):
        """TC-7: Test exact boundary conditions"""
        scaler = ProfitBasedKellyScaling()
        initial_capital = 100000

        # Just below 10%
        assert scaler.scale(0.20, 9999, initial_capital) == pytest.approx(0.10)

        # Exactly 10%
        assert scaler.scale(0.20, 10000, initial_capital) == pytest.approx(0.15)

        # Just below 20%
        assert scaler.scale(0.20, 19999, initial_capital) == pytest.approx(0.15)

        # Exactly 20%
        assert scaler.scale(0.20, 20000, initial_capital) == pytest.approx(0.20)

    def test_realistic_trading_progression(self):
        """TC-8: Test realistic profit progression"""
        scaler = ProfitBasedKellyScaling()
        kelly = 0.25
        initial_capital = 100000

        # Month 1: -2% (drawdown)
        result = scaler.scale(kelly, -2000, initial_capital)
        assert result == pytest.approx(0.125)  # Half-Kelly

        # Month 2: +3% (recovery)
        result = scaler.scale(kelly, 3000, initial_capital)
        assert result == pytest.approx(0.125)  # Still Half-Kelly

        # Month 3: +8% (growing)
        result = scaler.scale(kelly, 8000, initial_capital)
        assert result == pytest.approx(0.125)  # Still Half-Kelly

        # Month 4: +12% (milestone 1)
        result = scaler.scale(kelly, 12000, initial_capital)
        assert result == pytest.approx(0.1875)  # 3/4 Kelly

        # Month 6: +22% (milestone 2)
        result = scaler.scale(kelly, 22000, initial_capital)
        assert result == pytest.approx(0.25)  # Full Kelly

    def test_zero_kelly_fraction(self):
        """TC-9: Edge case - zero Kelly fraction"""
        scaler = ProfitBasedKellyScaling()

        # All should return 0 regardless of profit
        assert scaler.scale(0.0, 0, 100000) == pytest.approx(0.0)
        assert scaler.scale(0.0, 10000, 100000) == pytest.approx(0.0)
        assert scaler.scale(0.0, 20000, 100000) == pytest.approx(0.0)

    def test_very_large_profits(self):
        """TC-10: Edge case - very large profits"""
        scaler = ProfitBasedKellyScaling()

        # 200% profit (doubled capital)
        assert scaler.scale(0.20, 200000, 100000) == pytest.approx(0.20)

        # 1000% profit
        assert scaler.scale(0.20, 1000000, 100000) == pytest.approx(0.20)

    def test_negative_kelly_fraction(self):
        """TC-11: Edge case - negative Kelly (no edge)"""
        scaler = ProfitBasedKellyScaling()

        # Negative Kelly should still scale
        assert scaler.scale(-0.10, 0, 100000) == pytest.approx(-0.05)
        assert scaler.scale(-0.10, 10000, 100000) == pytest.approx(-0.075)
        assert scaler.scale(-0.10, 20000, 100000) == pytest.approx(-0.10)

    def test_consistency(self):
        """TC-12: Consistency across multiple calls"""
        scaler = ProfitBasedKellyScaling()

        # Same inputs should give same outputs
        result1 = scaler.scale(0.20, 15000, 100000)
        result2 = scaler.scale(0.20, 15000, 100000)
        result3 = scaler.scale(0.20, 15000, 100000)

        assert result1 == result2 == result3 == pytest.approx(0.15)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.kelly.profit_based_kelly_scaling", "--cov-report=term-missing"])
