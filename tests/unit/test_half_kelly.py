"""Tests for Half-Kelly Implementation (SHORT-018)"""

import pytest
from src.kelly.half_kelly import HalfKellyCalculator


class TestHalfKellyCalculator:
    """Test suite for Half-Kelly calculator"""

    def test_basic_half_kelly(self):
        """TC-1: Basic Half-Kelly calculation"""
        calculator = HalfKellyCalculator()
        assert calculator.calculate(0.20) == pytest.approx(0.10)
        assert calculator.calculate(0.50) == pytest.approx(0.25)
        assert calculator.calculate(0.10) == pytest.approx(0.05)

    def test_edge_cases(self):
        """TC-2: Edge cases"""
        calculator = HalfKellyCalculator()
        assert calculator.calculate(0.0) == pytest.approx(0.0)
        assert calculator.calculate(1.0) == pytest.approx(0.5)

    def test_negative_kelly(self):
        """TC-3: Negative input (no position)"""
        calculator = HalfKellyCalculator()
        assert calculator.calculate(-0.10) == pytest.approx(-0.05)
        assert calculator.calculate(-0.20) == pytest.approx(-0.10)

    def test_very_small_fractions(self):
        """TC-4: Very small fractions"""
        calculator = HalfKellyCalculator()
        assert calculator.calculate(0.001) == pytest.approx(0.0005)
        assert calculator.calculate(0.0001) == pytest.approx(0.00005)

    def test_very_large_fractions(self):
        """TC-5: Very large fractions (edge case)"""
        calculator = HalfKellyCalculator()
        assert calculator.calculate(2.0) == pytest.approx(1.0)
        assert calculator.calculate(10.0) == pytest.approx(5.0)

    def test_typical_trading_scenarios(self):
        """TC-6: Typical trading scenarios"""
        calculator = HalfKellyCalculator()

        # Conservative strategy (5% full Kelly)
        assert calculator.calculate(0.05) == pytest.approx(0.025)

        # Moderate strategy (15% full Kelly)
        assert calculator.calculate(0.15) == pytest.approx(0.075)

        # Aggressive strategy (30% full Kelly)
        assert calculator.calculate(0.30) == pytest.approx(0.15)

    def test_precision(self):
        """TC-7: Calculation precision"""
        calculator = HalfKellyCalculator()

        # Test with high precision values
        result = calculator.calculate(0.123456789)
        expected = 0.123456789 * 0.5
        assert result == pytest.approx(expected, rel=1e-9)

    def test_consistency(self):
        """TC-8: Consistency across multiple calls"""
        calculator = HalfKellyCalculator()

        # Same input should give same output
        kelly = 0.25
        result1 = calculator.calculate(kelly)
        result2 = calculator.calculate(kelly)
        result3 = calculator.calculate(kelly)

        assert result1 == result2 == result3 == pytest.approx(0.125)

    def test_mathematical_property(self):
        """TC-9: Mathematical property - Half-Kelly is exactly 50%"""
        calculator = HalfKellyCalculator()

        test_values = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.50, 1.0]
        for kelly in test_values:
            result = calculator.calculate(kelly)
            assert result == pytest.approx(kelly * 0.5)
            assert result / kelly == pytest.approx(0.5) if kelly != 0 else True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.kelly.half_kelly", "--cov-report=term-missing"])
