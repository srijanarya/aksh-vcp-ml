"""Tests for Strategy Performance Tracker (SHORT-016)"""

import pytest
from datetime import datetime, timedelta


class TestStrategyPerformanceTracker:
    """Test strategy performance tracking"""

    def test_track_trade_outcomes(self):
        """TC-1: Track individual trade outcomes"""
        from src.kelly.strategy_performance_tracker import StrategyPerformanceTracker

        tracker = StrategyPerformanceTracker()

        # Record trades
        tracker.record_trade(profit=100, timestamp=datetime.now())
        tracker.record_trade(profit=-50, timestamp=datetime.now())
        tracker.record_trade(profit=75, timestamp=datetime.now())

        stats = tracker.get_stats()
        assert stats['total_trades'] == 3
        assert stats['wins'] == 2
        assert stats['losses'] == 1

    def test_calculate_win_rate(self):
        """TC-2: Calculate win rate"""
        from src.kelly.strategy_performance_tracker import StrategyPerformanceTracker

        tracker = StrategyPerformanceTracker()

        # 7 wins, 3 losses
        for _ in range(7):
            tracker.record_trade(profit=100)
        for _ in range(3):
            tracker.record_trade(profit=-50)

        stats = tracker.get_stats()
        assert stats['win_rate'] == pytest.approx(70.0, abs=0.1)

    def test_calculate_profit_loss_averages(self):
        """TC-3: Calculate average profit and loss"""
        from src.kelly.strategy_performance_tracker import StrategyPerformanceTracker

        tracker = StrategyPerformanceTracker()

        # Winning trades: 100, 150, 200 (avg = 150)
        tracker.record_trade(profit=100)
        tracker.record_trade(profit=150)
        tracker.record_trade(profit=200)

        # Losing trades: -50, -100 (avg = -75)
        tracker.record_trade(profit=-50)
        tracker.record_trade(profit=-100)

        stats = tracker.get_stats()
        assert stats['avg_profit'] == pytest.approx(150.0, abs=0.1)
        assert stats['avg_loss'] == pytest.approx(-75.0, abs=0.1)

    def test_track_consecutive_results(self):
        """TC-4: Track consecutive wins/losses"""
        from src.kelly.strategy_performance_tracker import StrategyPerformanceTracker

        tracker = StrategyPerformanceTracker()

        # 3 consecutive wins
        tracker.record_trade(profit=100)
        tracker.record_trade(profit=50)
        tracker.record_trade(profit=75)

        # 2 consecutive losses
        tracker.record_trade(profit=-50)
        tracker.record_trade(profit=-25)

        # 1 win
        tracker.record_trade(profit=100)

        stats = tracker.get_stats()
        assert stats['max_consecutive_wins'] >= 3
        assert stats['max_consecutive_losses'] >= 2
        assert stats['current_streak'] == 1  # 1 win currently

    def test_rolling_window_calculation(self):
        """Test calculations over rolling window"""
        from src.kelly.strategy_performance_tracker import StrategyPerformanceTracker

        tracker = StrategyPerformanceTracker()

        # Old trades (outside window)
        old_time = datetime.now() - timedelta(days=100)
        for _ in range(10):
            tracker.record_trade(profit=-100, timestamp=old_time)

        # Recent trades (inside window)
        recent_time = datetime.now() - timedelta(days=5)
        for _ in range(7):
            tracker.record_trade(profit=100, timestamp=recent_time)

        # Get stats for last 30 days
        stats = tracker.get_stats(window_days=30)
        assert stats['win_rate'] > 50  # Only recent wins count

    def test_persist_performance_history(self, tmp_path):
        """Test persisting performance history"""
        from src.kelly.strategy_performance_tracker import StrategyPerformanceTracker

        db_path = tmp_path / "performance.db"
        tracker = StrategyPerformanceTracker(db_path=str(db_path))

        tracker.record_trade(profit=100)
        tracker.save()

        # Load in new instance
        tracker2 = StrategyPerformanceTracker(db_path=str(db_path))
        tracker2.load()

        stats = tracker2.get_stats()
        assert stats['total_trades'] == 1

    def test_zero_trades(self):
        """Test stats with no trades"""
        from src.kelly.strategy_performance_tracker import StrategyPerformanceTracker

        tracker = StrategyPerformanceTracker()
        stats = tracker.get_stats()

        assert stats['total_trades'] == 0
        assert stats['win_rate'] == 0
        assert stats['avg_profit'] == 0
        assert stats['avg_loss'] == 0
