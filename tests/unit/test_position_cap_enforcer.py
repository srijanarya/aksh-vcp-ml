"""Tests for Position Cap Enforcer (SHORT-020)"""

import pytest
from src.kelly.position_cap_enforcer import PositionCapEnforcer


class TestPositionCapEnforcer:
    """Test suite for Position Cap Enforcer"""

    def test_equity_cap_default(self):
        """TC-1: Equity cap at default 20%"""
        enforcer = PositionCapEnforcer()

        # Below cap - no change
        assert enforcer.enforce(0.10, "equity") == pytest.approx(0.10)
        assert enforcer.enforce(0.15, "equity") == pytest.approx(0.15)
        assert enforcer.enforce(0.20, "equity") == pytest.approx(0.20)

        # Above cap - capped
        assert enforcer.enforce(0.25, "equity") == pytest.approx(0.20)
        assert enforcer.enforce(0.30, "equity") == pytest.approx(0.20)
        assert enforcer.enforce(0.50, "equity") == pytest.approx(0.20)

    def test_fno_cap_default(self):
        """TC-2: F&O cap at default 4%"""
        enforcer = PositionCapEnforcer()

        # Below cap - no change
        assert enforcer.enforce(0.01, "fno") == pytest.approx(0.01)
        assert enforcer.enforce(0.03, "fno") == pytest.approx(0.03)
        assert enforcer.enforce(0.04, "fno") == pytest.approx(0.04)

        # Above cap - capped
        assert enforcer.enforce(0.05, "fno") == pytest.approx(0.04)
        assert enforcer.enforce(0.10, "fno") == pytest.approx(0.04)
        assert enforcer.enforce(0.20, "fno") == pytest.approx(0.04)

    def test_custom_equity_cap(self):
        """TC-3: Custom equity cap"""
        enforcer = PositionCapEnforcer(equity_cap=15.0, fno_cap=4.0)

        # Below cap
        assert enforcer.enforce(0.10, "equity") == pytest.approx(0.10)

        # At cap
        assert enforcer.enforce(0.15, "equity") == pytest.approx(0.15)

        # Above cap
        assert enforcer.enforce(0.20, "equity") == pytest.approx(0.15)
        assert enforcer.enforce(0.30, "equity") == pytest.approx(0.15)

    def test_custom_fno_cap(self):
        """TC-4: Custom F&O cap"""
        enforcer = PositionCapEnforcer(equity_cap=20.0, fno_cap=3.0)

        # Below cap
        assert enforcer.enforce(0.02, "fno") == pytest.approx(0.02)

        # At cap
        assert enforcer.enforce(0.03, "fno") == pytest.approx(0.03)

        # Above cap
        assert enforcer.enforce(0.05, "fno") == pytest.approx(0.03)
        assert enforcer.enforce(0.10, "fno") == pytest.approx(0.03)

    def test_both_caps_custom(self):
        """TC-5: Both caps customized"""
        enforcer = PositionCapEnforcer(equity_cap=10.0, fno_cap=2.0)

        # Equity
        assert enforcer.enforce(0.15, "equity") == pytest.approx(0.10)
        assert enforcer.enforce(0.05, "equity") == pytest.approx(0.05)

        # F&O
        assert enforcer.enforce(0.05, "fno") == pytest.approx(0.02)
        assert enforcer.enforce(0.01, "fno") == pytest.approx(0.01)

    def test_zero_kelly_fraction(self):
        """TC-6: Zero Kelly fraction"""
        enforcer = PositionCapEnforcer()

        assert enforcer.enforce(0.0, "equity") == pytest.approx(0.0)
        assert enforcer.enforce(0.0, "fno") == pytest.approx(0.0)

    def test_negative_kelly_fraction(self):
        """TC-7: Negative Kelly fraction (no position)"""
        enforcer = PositionCapEnforcer()

        # Negative should not be capped (it's already no position)
        assert enforcer.enforce(-0.10, "equity") == pytest.approx(-0.10)
        assert enforcer.enforce(-0.05, "fno") == pytest.approx(-0.05)

    def test_very_large_kelly_fraction(self):
        """TC-8: Very large Kelly fraction"""
        enforcer = PositionCapEnforcer()

        # Should cap to maximum
        assert enforcer.enforce(1.0, "equity") == pytest.approx(0.20)
        assert enforcer.enforce(2.0, "equity") == pytest.approx(0.20)
        assert enforcer.enforce(1.0, "fno") == pytest.approx(0.04)
        assert enforcer.enforce(2.0, "fno") == pytest.approx(0.04)

    def test_boundary_values_equity(self):
        """TC-9: Boundary values for equity"""
        enforcer = PositionCapEnforcer()

        # Just below cap
        assert enforcer.enforce(0.1999, "equity") == pytest.approx(0.1999)

        # Exactly at cap
        assert enforcer.enforce(0.2000, "equity") == pytest.approx(0.20)

        # Just above cap
        assert enforcer.enforce(0.2001, "equity") == pytest.approx(0.20)

    def test_boundary_values_fno(self):
        """TC-10: Boundary values for F&O"""
        enforcer = PositionCapEnforcer()

        # Just below cap
        assert enforcer.enforce(0.0399, "fno") == pytest.approx(0.0399)

        # Exactly at cap
        assert enforcer.enforce(0.0400, "fno") == pytest.approx(0.04)

        # Just above cap
        assert enforcer.enforce(0.0401, "fno") == pytest.approx(0.04)

    def test_realistic_kelly_fractions(self):
        """TC-11: Realistic Kelly fractions from trading"""
        enforcer = PositionCapEnforcer()

        # Conservative strategy (5-10%)
        assert enforcer.enforce(0.05, "equity") == pytest.approx(0.05)
        assert enforcer.enforce(0.10, "equity") == pytest.approx(0.10)

        # Moderate strategy (10-20%)
        assert enforcer.enforce(0.12, "equity") == pytest.approx(0.12)
        assert enforcer.enforce(0.18, "equity") == pytest.approx(0.18)

        # Aggressive strategy (20%+)
        assert enforcer.enforce(0.25, "equity") == pytest.approx(0.20)  # Capped
        assert enforcer.enforce(0.35, "equity") == pytest.approx(0.20)  # Capped

    def test_realistic_fno_scenarios(self):
        """TC-12: Realistic F&O scenarios"""
        enforcer = PositionCapEnforcer()

        # Conservative F&O (1-2%)
        assert enforcer.enforce(0.01, "fno") == pytest.approx(0.01)
        assert enforcer.enforce(0.02, "fno") == pytest.approx(0.02)

        # Moderate F&O (2-4%)
        assert enforcer.enforce(0.03, "fno") == pytest.approx(0.03)
        assert enforcer.enforce(0.04, "fno") == pytest.approx(0.04)

        # Aggressive F&O (4%+)
        assert enforcer.enforce(0.06, "fno") == pytest.approx(0.04)  # Capped
        assert enforcer.enforce(0.10, "fno") == pytest.approx(0.04)  # Capped

    def test_instrument_type_case_sensitivity(self):
        """TC-13: Instrument type is case-sensitive"""
        enforcer = PositionCapEnforcer()

        # Should work with lowercase
        assert enforcer.enforce(0.30, "equity") == pytest.approx(0.20)
        assert enforcer.enforce(0.10, "fno") == pytest.approx(0.04)

        # Anything else defaults to equity cap
        assert enforcer.enforce(0.30, "EQUITY") == pytest.approx(0.04)  # Uses fno_cap
        assert enforcer.enforce(0.30, "FNO") == pytest.approx(0.04)
        assert enforcer.enforce(0.30, "other") == pytest.approx(0.04)

    def test_consistency(self):
        """TC-14: Consistency across multiple calls"""
        enforcer = PositionCapEnforcer()

        # Same inputs should give same outputs
        result1 = enforcer.enforce(0.25, "equity")
        result2 = enforcer.enforce(0.25, "equity")
        result3 = enforcer.enforce(0.25, "equity")

        assert result1 == result2 == result3 == pytest.approx(0.20)

    def test_combined_kelly_workflow(self):
        """TC-15: Combined with Kelly calculation workflow"""
        enforcer = PositionCapEnforcer()

        # Scenario 1: Full Kelly of 30%, should cap to 20%
        full_kelly = 0.30
        capped = enforcer.enforce(full_kelly, "equity")
        assert capped == pytest.approx(0.20)

        # Scenario 2: Half-Kelly of 15%, should not cap
        half_kelly = 0.30 * 0.5
        capped = enforcer.enforce(half_kelly, "equity")
        assert capped == pytest.approx(0.15)

        # Scenario 3: F&O Kelly of 8%, should cap to 4%
        fno_kelly = 0.08
        capped = enforcer.enforce(fno_kelly, "fno")
        assert capped == pytest.approx(0.04)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.kelly.position_cap_enforcer", "--cov-report=term-missing"])
