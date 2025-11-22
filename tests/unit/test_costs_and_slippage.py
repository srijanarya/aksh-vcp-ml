"""Tests for costs and slippage"""

import pytest


def test_equity_delivery_cost():
    """Test equity delivery cost calculation"""
    from src.costs.cost_calculator import CostCalculator

    calc = CostCalculator()
    cost = calc.calculate_equity_delivery_cost(100000)

    # Should include STT and other charges
    assert cost > 0
    assert cost < 1000  # Reasonable for 1L trade


def test_intraday_cost():
    """Test intraday cost calculation"""
    from src.costs.cost_calculator import CostCalculator

    calc = CostCalculator()
    cost = calc.calculate_intraday_cost(100000)

    assert cost > 0


def test_fno_cost():
    """Test F&O cost calculation"""
    from src.costs.cost_calculator import CostCalculator

    calc = CostCalculator()
    cost = calc.calculate_fno_cost(100000)

    # Should include flat brokerage
    assert cost >= 20  # Minimum flat brokerage


def test_slippage_calculation():
    """Test slippage calculation"""
    from src.costs.slippage_simulator import SlippageSimulator

    sim = SlippageSimulator()

    # Small volume: low slippage
    slippage1 = sim.calculate_slippage(
        price=1000,
        volume=100,
        avg_volume=100000
    )

    # Large volume: higher slippage
    slippage2 = sim.calculate_slippage(
        price=1000,
        volume=10000,
        avg_volume=100000
    )

    assert slippage1 > 0
    assert slippage2 > slippage1
