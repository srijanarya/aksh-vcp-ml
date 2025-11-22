"""
Tests for Backtest Engine (SHORT-040 to SHORT-051)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backtest.backtest_engine import (
    BacktestEngine,
    Trade,
    BacktestResult
)


@pytest.fixture
def sample_data():
    """Generate sample OHLC data"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    close_prices = 100 + np.cumsum(np.random.randn(100) * 2)

    data = pd.DataFrame({
        'open': close_prices + np.random.randn(100) * 0.5,
        'high': close_prices + abs(np.random.randn(100) * 1),
        'low': close_prices - abs(np.random.randn(100) * 1),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)

    return data


@pytest.fixture
def buy_signals(sample_data):
    """Generate buy signals - every 10 days"""
    signals = pd.Series(False, index=sample_data.index)
    signals.iloc[::10] = True
    return signals


class TestTrade:
    """Test Trade dataclass (SHORT-046)"""

    def test_trade_creation(self):
        trade = Trade(
            symbol="TEST",
            entry_date=datetime(2024, 1, 1),
            entry_price=100.0,
            quantity=10
        )

        assert trade.symbol == "TEST"
        assert trade.quantity == 10
        assert trade.entry_price == 100.0
        assert trade.exit_date is None
        assert trade.exit_price is None

    def test_trade_with_exit(self):
        trade = Trade(
            symbol="TEST",
            entry_date=datetime(2024, 1, 1),
            entry_price=100.0,
            exit_date=datetime(2024, 1, 15),
            exit_price=105.0,
            quantity=10,
            pnl=50.0,
            pnl_pct=5.0
        )

        assert trade.exit_price == 105.0
        assert trade.pnl == 50.0
        assert trade.pnl_pct == 5.0


class TestBacktestResult:
    """Test BacktestResult dataclass (SHORT-047)"""

    def test_result_creation(self):
        result = BacktestResult()

        assert isinstance(result.trades, list)
        assert len(result.trades) == 0
        assert isinstance(result.equity_curve, pd.Series)
        assert isinstance(result.metrics, dict)

    def test_result_with_data(self):
        trades = [
            Trade("TEST", datetime.now(), 100.0, quantity=10)
        ]
        equity_curve = pd.Series([100000, 105000], index=pd.date_range('2024-01-01', periods=2))
        metrics = {'total_trades': 1}

        result = BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics
        )

        assert len(result.trades) == 1
        assert len(result.equity_curve) == 2
        assert result.metrics['total_trades'] == 1


class TestBacktestEngine:
    """Test BacktestEngine (SHORT-040 to SHORT-051)"""

    def test_engine_initialization(self):
        """Test engine initialization (SHORT-040)"""
        engine = BacktestEngine(initial_capital=100000)

        assert engine.initial_capital == 100000
        assert engine.capital == 100000
        assert len(engine.positions) == 0
        assert len(engine.trades) == 0

    def test_basic_backtest(self, sample_data, buy_signals):
        """Test basic backtest execution (SHORT-040)"""
        engine = BacktestEngine(initial_capital=100000)

        result = engine.run(
            data=sample_data,
            signals=buy_signals,
            stop_loss_pct=2.0,
            target_pct=4.0
        )

        assert isinstance(result, BacktestResult)
        assert len(result.trades) > 0
        assert len(result.equity_curve) == len(sample_data)
        assert 'total_trades' in result.metrics

    def test_position_entry(self, sample_data):
        """Test position entry (SHORT-041)"""
        engine = BacktestEngine(initial_capital=100000)

        # Enter position
        date = sample_data.index[0]
        row = sample_data.iloc[0]
        initial_capital = engine.capital

        engine._enter_position(date, row)

        # Should have one position
        assert len(engine.positions) == 1
        # Capital should be reduced
        assert engine.capital < initial_capital

    def test_max_positions_limit(self, sample_data):
        """Test max position limit (SHORT-041)"""
        engine = BacktestEngine(initial_capital=100000)

        # Try to enter 6 positions (max is 5)
        for i in range(6):
            date = sample_data.index[i]
            row = sample_data.iloc[i]
            engine._enter_position(date, row)

        # Should only have 5 positions
        assert len(engine.positions) == 5

    def test_stop_loss_trigger(self, sample_data):
        """Test stop loss execution (SHORT-042)"""
        engine = BacktestEngine(initial_capital=100000)

        # Enter position
        entry_date = sample_data.index[0]
        entry_row = sample_data.iloc[0]
        engine._enter_position(entry_date, entry_row)

        # Create exit row with -3% loss
        exit_date = sample_data.index[1]
        exit_row = sample_data.iloc[1].copy()
        entry_price = entry_row['close']
        exit_row['close'] = entry_price * 0.97  # -3% loss

        # Check exits (should trigger stop loss at -2%)
        engine._check_exits(exit_date, exit_row, stop_loss_pct=2.0, target_pct=4.0)

        # Position should be closed
        assert len(engine.positions) == 0
        # Should have one trade
        assert len(engine.trades) == 1
        # Trade should be a loss
        assert engine.trades[0].pnl < 0

    def test_target_hit(self, sample_data):
        """Test target execution (SHORT-042)"""
        engine = BacktestEngine(initial_capital=100000)

        # Enter position
        entry_date = sample_data.index[0]
        entry_row = sample_data.iloc[0]
        engine._enter_position(entry_date, entry_row)

        # Create exit row with +5% gain
        exit_date = sample_data.index[1]
        exit_row = sample_data.iloc[1].copy()
        entry_price = entry_row['close']
        exit_row['close'] = entry_price * 1.05  # +5% gain

        # Check exits (should trigger target at +4%)
        engine._check_exits(exit_date, exit_row, stop_loss_pct=2.0, target_pct=4.0)

        # Position should be closed
        assert len(engine.positions) == 0
        # Should have one trade
        assert len(engine.trades) == 1
        # Trade should be profitable
        assert engine.trades[0].pnl > 0

    def test_equity_curve_generation(self, sample_data, buy_signals):
        """Test equity curve generation (SHORT-043)"""
        engine = BacktestEngine(initial_capital=100000)

        result = engine.run(sample_data, buy_signals)

        # Equity curve should have same length as data
        assert len(result.equity_curve) == len(sample_data)
        # All equity values should be positive
        assert (result.equity_curve > 0).all()
        # First equity should be close to initial capital
        assert abs(result.equity_curve.iloc[0] - 100000) < 10000

    def test_capital_tracking(self, sample_data):
        """Test capital tracking (SHORT-049)"""
        engine = BacktestEngine(initial_capital=100000)

        initial_capital = engine.capital

        # Enter position
        date = sample_data.index[0]
        row = sample_data.iloc[0]
        engine._enter_position(date, row)

        # Capital should decrease
        assert engine.capital < initial_capital

        # Exit position
        exit_date = sample_data.index[1]
        exit_row = sample_data.iloc[1]
        list(engine.positions.values())[0].exit_date = exit_date
        engine._exit_position(
            list(engine.positions.values())[0],
            exit_date,
            exit_row['close']
        )

        # Capital should be updated
        assert engine.capital > 0

    def test_insufficient_capital(self, sample_data):
        """Test insufficient capital handling (SHORT-049)"""
        engine = BacktestEngine(initial_capital=1000)  # Low capital

        # Try to enter position
        date = sample_data.index[0]
        row = sample_data.iloc[0].copy()
        row['close'] = 10000  # Expensive stock

        engine._enter_position(date, row)

        # Should not enter position
        assert len(engine.positions) == 0

    def test_metrics_calculation(self, sample_data, buy_signals):
        """Test metrics calculation (SHORT-044)"""
        engine = BacktestEngine(initial_capital=100000)

        result = engine.run(sample_data, buy_signals)

        # Check all metrics present
        assert 'total_trades' in result.metrics
        assert 'wins' in result.metrics
        assert 'losses' in result.metrics
        assert 'win_rate' in result.metrics
        assert 'total_pnl' in result.metrics
        assert 'total_return_pct' in result.metrics
        assert 'sharpe_ratio' in result.metrics
        assert 'max_drawdown' in result.metrics

        # Check metric types
        assert isinstance(result.metrics['total_trades'], int)
        assert isinstance(result.metrics['win_rate'], float)

    def test_sharpe_ratio_calculation(self, sample_data, buy_signals):
        """Test Sharpe ratio calculation (SHORT-050)"""
        engine = BacktestEngine(initial_capital=100000)

        result = engine.run(sample_data, buy_signals)

        # Sharpe ratio should be calculated
        assert 'sharpe_ratio' in result.metrics
        assert isinstance(result.metrics['sharpe_ratio'], (int, float))

    def test_max_drawdown_calculation(self, sample_data, buy_signals):
        """Test max drawdown calculation (SHORT-051)"""
        engine = BacktestEngine(initial_capital=100000)

        result = engine.run(sample_data, buy_signals)

        # Max drawdown should be negative
        assert result.metrics['max_drawdown'] <= 0

    def test_empty_signals(self, sample_data):
        """Test backtest with no signals"""
        engine = BacktestEngine(initial_capital=100000)
        signals = pd.Series(False, index=sample_data.index)

        result = engine.run(sample_data, signals)

        # Should have no trades
        assert len(result.trades) == 0
        assert result.metrics['total_trades'] == 0

    def test_cost_integration(self, sample_data, buy_signals):
        """Test cost calculator integration (SHORT-045)"""
        # Mock cost calculator
        class MockCostCalculator:
            def calculate_equity_delivery_cost(self, value):
                return value * 0.001  # 0.1% cost

        engine = BacktestEngine(
            initial_capital=100000,
            cost_calculator=MockCostCalculator()
        )

        result = engine.run(sample_data, buy_signals)

        # Should complete without errors
        assert len(result.trades) > 0


class TestSignalIntegration:
    """Test signal-backtest integration (SHORT-048)"""

    def test_signal_alignment(self, sample_data):
        """Test signal alignment with data"""
        engine = BacktestEngine(initial_capital=100000)

        # Create signals with specific dates
        signals = pd.Series(False, index=sample_data.index)
        signals.iloc[0] = True
        signals.iloc[10] = True

        result = engine.run(sample_data, signals, stop_loss_pct=10, target_pct=20)

        # Should attempt to enter at signal points
        # (may not succeed if capital insufficient)
        assert isinstance(result, BacktestResult)


def test_end_to_end_backtest(sample_data, buy_signals):
    """End-to-end backtest test"""
    engine = BacktestEngine(initial_capital=100000)

    result = engine.run(
        data=sample_data,
        signals=buy_signals,
        stop_loss_pct=2.0,
        target_pct=4.0
    )

    # Verify complete result
    assert isinstance(result, BacktestResult)
    assert len(result.trades) > 0
    assert len(result.equity_curve) == len(sample_data)
    assert result.metrics['total_trades'] == len(result.trades)

    # Final equity should be reasonable
    final_equity = result.equity_curve.iloc[-1]
    assert final_equity > 0

    print(f"Backtest completed: {result.metrics['total_trades']} trades")
    print(f"Total Return: {result.metrics['total_return_pct']:.2f}%")
    print(f"Win Rate: {result.metrics['win_rate']:.2f}%")
    print(f"Sharpe Ratio: {result.metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {result.metrics['max_drawdown']:.2f}%")
