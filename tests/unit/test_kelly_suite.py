"""Combined tests for Kelly sizing suite (SHORT-018 to SHORT-020)"""

import pytest


def test_half_kelly():
    """Test Half-Kelly calculation"""
    from src.kelly.half_kelly import HalfKellyCalculator

    calc = HalfKellyCalculator()
    assert calc.calculate(0.4) == pytest.approx(0.2)
    assert calc.calculate(0.8) == pytest.approx(0.4)


def test_profit_based_scaling():
    """Test profit-based Kelly scaling"""
    from src.kelly.profit_based_kelly_scaling import ProfitBasedKellyScaling

    scaler = ProfitBasedKellyScaling()

    # No profit: Half-Kelly
    assert scaler.scale(0.4, 0, 100000) == pytest.approx(0.2)

    # 5% profit: Half-Kelly
    assert scaler.scale(0.4, 5000, 100000) == pytest.approx(0.2)

    # 15% profit: 3/4 Kelly
    assert scaler.scale(0.4, 15000, 100000) == pytest.approx(0.3)

    # 25% profit: Full Kelly
    assert scaler.scale(0.4, 25000, 100000) == pytest.approx(0.4)


def test_position_cap_enforcer():
    """Test position cap enforcement"""
    from src.kelly.position_cap_enforcer import PositionCapEnforcer

    enforcer = PositionCapEnforcer(equity_cap=20.0, fno_cap=4.0)

    # Kelly below cap
    assert enforcer.enforce(0.1, "equity") == pytest.approx(0.1)

    # Kelly above equity cap
    assert enforcer.enforce(0.5, "equity") == pytest.approx(0.2)

    # Kelly above F&O cap
    assert enforcer.enforce(0.1, "fno") == pytest.approx(0.04)
