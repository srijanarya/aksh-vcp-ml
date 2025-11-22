"""Tests for Weekly Kelly Updater (SHORT-022)"""

import pytest
from datetime import datetime
from src.kelly.weekly_kelly_updater import WeeklyKellyUpdater, KellyUpdate


class TestWeeklyKellyUpdater:
    """Test suite for Weekly Kelly Updater"""

    def test_should_update_insufficient_trades(self):
        """TC-1: Should not update with insufficient trades"""
        updater = WeeklyKellyUpdater(min_trades=10)

        assert updater.should_update(5) is False
        assert updater.should_update(9) is False

    def test_should_update_sufficient_trades(self):
        """TC-2: Should update with sufficient trades"""
        updater = WeeklyKellyUpdater(min_trades=10)

        assert updater.should_update(10) is True
        assert updater.should_update(20) is True
        assert updater.should_update(100) is True

    def test_calculate_new_kelly_insufficient_data(self):
        """TC-3: Returns None with insufficient data"""
        updater = WeeklyKellyUpdater(min_trades=10)

        trades = [{'pnl': 100} for _ in range(5)]
        result = updater.calculate_new_kelly(trades, 0.20)

        assert result is None

    def test_calculate_new_kelly_all_wins(self):
        """TC-4: Calculate Kelly with all winning trades"""
        updater = WeeklyKellyUpdater(min_trades=10, lookback_trades=20)

        # 15 winning trades
        trades = [{'pnl': 100, 'size': 10000} for _ in range(15)]
        result = updater.calculate_new_kelly(trades, 0.20)

        assert result is not None
        assert result.win_rate == pytest.approx(1.0)
        assert result.num_trades == 15
        assert result.old_kelly == pytest.approx(0.20)

    def test_calculate_new_kelly_all_losses(self):
        """TC-5: Calculate Kelly with all losing trades"""
        updater = WeeklyKellyUpdater(min_trades=10, lookback_trades=20)

        # 15 losing trades
        trades = [{'pnl': -100, 'size': 10000} for _ in range(15)]
        result = updater.calculate_new_kelly(trades, 0.20)

        assert result is not None
        assert result.win_rate == pytest.approx(0.0)
        assert result.new_kelly == pytest.approx(0.0)  # Should be 0 or negative

    def test_calculate_new_kelly_mixed_trades(self):
        """TC-6: Calculate Kelly with mixed win/loss"""
        updater = WeeklyKellyUpdater(min_trades=10, lookback_trades=20)

        # 60% win rate, 2:1 R:R
        trades = []
        for _ in range(12):  # 60% wins
            trades.append({'pnl': 200, 'size': 10000})
        for _ in range(8):   # 40% losses
            trades.append({'pnl': -100, 'size': 10000})

        result = updater.calculate_new_kelly(trades, 0.20)

        assert result is not None
        assert result.win_rate == pytest.approx(0.60)
        assert result.avg_win_loss_ratio == pytest.approx(2.0)
        # Kelly = (0.60 * 2 - 0.40) / 2 = 0.40
        assert result.new_kelly == pytest.approx(0.40)

    def test_lookback_window(self):
        """TC-7: Use only recent trades in lookback window"""
        updater = WeeklyKellyUpdater(min_trades=10, lookback_trades=10)

        # 30 total trades: first 20 losses, last 10 wins
        trades = []
        for _ in range(20):
            trades.append({'pnl': -100, 'size': 10000})
        for _ in range(10):
            trades.append({'pnl': 100, 'size': 10000})

        result = updater.calculate_new_kelly(trades, 0.20)

        assert result is not None
        # Should only use last 10 trades (all wins)
        assert result.win_rate == pytest.approx(1.0)
        assert result.num_trades == 10

    def test_update_history_recorded(self):
        """TC-8: Update history is recorded"""
        updater = WeeklyKellyUpdater(min_trades=10, lookback_trades=20)

        trades = [
            {'pnl': 200 if i % 2 == 0 else -100, 'size': 10000}
            for i in range(20)
        ]

        # First update
        result1 = updater.calculate_new_kelly(trades, 0.20)
        assert result1 is not None
        assert len(updater.update_history) == 1

        # Add more trades
        trades.extend([{'pnl': 150, 'size': 10000} for _ in range(5)])

        # Second update
        result2 = updater.calculate_new_kelly(trades, result1.new_kelly)
        assert result2 is not None
        assert len(updater.update_history) == 2

        # Verify history
        history = updater.get_update_history()
        assert len(history) == 2
        assert history[0].old_kelly == pytest.approx(0.20)
        assert history[1].old_kelly == pytest.approx(result1.new_kelly)

    def test_get_latest_kelly_no_updates(self):
        """TC-9: Get latest Kelly with no updates"""
        updater = WeeklyKellyUpdater()

        assert updater.get_latest_kelly() is None

    def test_get_latest_kelly_with_updates(self):
        """TC-10: Get latest Kelly after updates"""
        updater = WeeklyKellyUpdater(min_trades=10)

        trades = [
            {'pnl': 100 if i < 12 else -100, 'size': 10000}
            for i in range(20)
        ]

        result = updater.calculate_new_kelly(trades, 0.20)
        assert result is not None

        latest = updater.get_latest_kelly()
        assert latest == pytest.approx(result.new_kelly)

    def test_custom_parameters(self):
        """TC-11: Custom lookback and min_trades parameters"""
        updater = WeeklyKellyUpdater(lookback_trades=15, min_trades=5)

        assert updater.lookback_trades == 15
        assert updater.min_trades == 5

        # Should update with 5 trades
        assert updater.should_update(5) is True

        # Should use 15 trades for calculation
        trades = [{'pnl': 100, 'size': 10000} for _ in range(30)]
        result = updater.calculate_new_kelly(trades, 0.20)

        assert result is not None
        assert result.num_trades == 15

    def test_kelly_update_dataclass(self):
        """TC-12: KellyUpdate dataclass structure"""
        update = KellyUpdate(
            timestamp=datetime.now(),
            old_kelly=0.20,
            new_kelly=0.25,
            win_rate=0.60,
            avg_win_loss_ratio=2.0,
            num_trades=20
        )

        assert update.old_kelly == pytest.approx(0.20)
        assert update.new_kelly == pytest.approx(0.25)
        assert update.win_rate == pytest.approx(0.60)
        assert update.avg_win_loss_ratio == pytest.approx(2.0)
        assert update.num_trades == 20
        assert isinstance(update.timestamp, datetime)

    def test_negative_kelly_clamped_to_zero(self):
        """TC-13: Negative Kelly is clamped to 0"""
        updater = WeeklyKellyUpdater(min_trades=10)

        # Poor strategy: 30% win rate, 0.5:1 R:R
        # Kelly = (0.30 * 0.5 - 0.70) / 0.5 = -1.1 (negative edge)
        trades = []
        for _ in range(6):
            trades.append({'pnl': 50, 'size': 10000})  # Wins
        for _ in range(14):
            trades.append({'pnl': -100, 'size': 10000})  # Losses

        result = updater.calculate_new_kelly(trades, 0.20)

        assert result is not None
        assert result.new_kelly >= 0.0  # Should be clamped to 0

    def test_realistic_trading_scenario(self):
        """TC-14: Realistic trading scenario"""
        updater = WeeklyKellyUpdater(min_trades=10, lookback_trades=20)

        # Week 1: Good performance (70% win rate, 2:1 R:R)
        week1_trades = []
        for _ in range(14):
            week1_trades.append({'pnl': 200, 'size': 10000})
        for _ in range(6):
            week1_trades.append({'pnl': -100, 'size': 10000})

        result1 = updater.calculate_new_kelly(week1_trades, 0.10)
        assert result1 is not None
        assert result1.win_rate == pytest.approx(0.70)
        # Kelly = (0.70 * 2 - 0.30) / 2 = 0.55
        assert result1.new_kelly == pytest.approx(0.55)

        # Week 2: Moderate performance (55% win rate, 1.5:1 R:R)
        all_trades = week1_trades.copy()
        week2_trades = []
        for _ in range(11):
            week2_trades.append({'pnl': 150, 'size': 10000})
        for _ in range(9):
            week2_trades.append({'pnl': -100, 'size': 10000})

        all_trades.extend(week2_trades)

        result2 = updater.calculate_new_kelly(all_trades, result1.new_kelly)
        assert result2 is not None
        # Should use last 20 trades only
        assert result2.num_trades == 20

    def test_empty_trades_list(self):
        """TC-15: Handle empty trades list"""
        updater = WeeklyKellyUpdater(min_trades=10)

        result = updater.calculate_new_kelly([], 0.20)
        assert result is None

    def test_zero_pnl_trades(self):
        """TC-16: Handle zero PnL trades"""
        updater = WeeklyKellyUpdater(min_trades=10)

        # All breakeven trades
        trades = [{'pnl': 0, 'size': 10000} for _ in range(15)]
        result = updater.calculate_new_kelly(trades, 0.20)

        assert result is not None
        assert result.win_rate == pytest.approx(0.0)  # No wins
        assert result.new_kelly >= 0.0

    def test_varying_trade_sizes(self):
        """TC-17: Trades with varying sizes"""
        updater = WeeklyKellyUpdater(min_trades=10)

        trades = []
        # Different position sizes
        for i in range(10):
            trades.append({
                'pnl': 100 if i % 2 == 0 else -50,
                'size': 5000 + i * 1000
            })

        result = updater.calculate_new_kelly(trades, 0.20)
        assert result is not None
        assert result.win_rate == pytest.approx(0.50)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.kelly.weekly_kelly_updater", "--cov-report=term-missing"])
