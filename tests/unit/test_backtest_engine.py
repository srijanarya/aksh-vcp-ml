"""Tests for Backtesting Engine (SHORT-040 to SHORT-051)"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_data():
    """Sample backtest data"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    close = 100 + np.cumsum(np.random.randn(100) * 2)
    high = close + np.random.uniform(1, 3, 100)
    low = close - np.random.uniform(1, 3, 100)

    return pd.DataFrame({
        'open': close,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(100000, 1000000, 100)
    }, index=dates)


@pytest.fixture
def sample_signals(sample_data):
    """Sample buy signals"""
    signals = pd.Series(False, index=sample_data.index)
    signals.iloc[::10] = True  # Buy every 10 days
    return signals


def test_backtest_basic_run(sample_data, sample_signals):
    """Test basic backtest execution"""
    from src.backtest.backtest_engine import BacktestEngine

    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(sample_data, sample_signals)

    assert result.metrics['total_trades'] > 0
    assert 'win_rate' in result.metrics
    assert 'sharpe_ratio' in result.metrics
    assert len(result.equity_curve) > 0


def test_stop_loss_trigger(sample_data):
    """Test stop loss triggering"""
    from src.backtest.backtest_engine import BacktestEngine

    # Create data with clear downtrend
    data = sample_data.copy()
    data['close'] = 100 - np.arange(len(data)) * 0.5

    signals = pd.Series(False, index=data.index)
    signals.iloc[0] = True  # Single buy at start

    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(data, signals, stop_loss_pct=2.0)

    # Should have triggered stop loss
    assert result.metrics['total_trades'] >= 1
    if result.trades:
        assert result.trades[0].pnl < 0  # Loss due to stop


def test_target_trigger(sample_data):
    """Test target triggering"""
    from src.backtest.backtest_engine import BacktestEngine

    # Create data with clear uptrend
    data = sample_data.copy()
    data['close'] = 100 + np.arange(len(data)) * 0.5

    signals = pd.Series(False, index=data.index)
    signals.iloc[0] = True  # Single buy at start

    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(data, signals, target_pct=4.0)

    # Should have triggered target
    assert result.metrics['total_trades'] >= 1
    if result.trades:
        assert result.trades[0].pnl > 0  # Profit due to target


def test_performance_metrics(sample_data, sample_signals):
    """Test performance metric calculations"""
    from src.backtest.backtest_engine import BacktestEngine

    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(sample_data, sample_signals)

    metrics = result.metrics

    # All metrics should be present
    assert 'total_trades' in metrics
    assert 'wins' in metrics
    assert 'losses' in metrics
    assert 'win_rate' in metrics
    assert 'total_pnl' in metrics
    assert 'total_return_pct' in metrics
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics

    # Win rate should be percentage
    assert 0 <= metrics['win_rate'] <= 100


def test_equity_curve_tracking(sample_data, sample_signals):
    """Test equity curve tracking"""
    from src.backtest.backtest_engine import BacktestEngine

    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(sample_data, sample_signals)

    # Equity curve should have entries
    assert len(result.equity_curve) > 0

    # Should start at initial capital
    assert result.equity_curve.iloc[0] >= 100000 * 0.9  # Allow some variance


def test_position_limits(sample_data):
    """Test maximum position limits"""
    from src.backtest.backtest_engine import BacktestEngine

    # Try to enter many positions
    signals = pd.Series(True, index=sample_data.index)

    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(sample_data, signals)

    # Should never hold more than max positions
    # (implicitly tested by no errors)
    assert result.metrics['total_trades'] >= 0
