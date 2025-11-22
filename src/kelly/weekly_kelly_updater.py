"""Weekly Kelly Fraction Updater (SHORT-022)"""

from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class KellyUpdate:
    """Record of Kelly fraction update"""
    timestamp: datetime
    old_kelly: float
    new_kelly: float
    win_rate: float
    avg_win_loss_ratio: float
    num_trades: int


class WeeklyKellyUpdater:
    """Update Kelly fraction weekly based on recent performance"""

    def __init__(
        self,
        lookback_trades: int = 20,
        min_trades: int = 10
    ):
        """
        Initialize updater

        Args:
            lookback_trades: Number of recent trades to analyze
            min_trades: Minimum trades required before updating
        """
        self.lookback_trades = lookback_trades
        self.min_trades = min_trades
        self.update_history: List[KellyUpdate] = []

    def should_update(self, num_trades: int) -> bool:
        """
        Check if Kelly should be updated

        Args:
            num_trades: Total number of trades

        Returns:
            True if enough trades for update
        """
        return num_trades >= self.min_trades

    def calculate_new_kelly(
        self,
        trades: List[Dict],
        current_kelly: float
    ) -> Optional[KellyUpdate]:
        """
        Calculate new Kelly fraction from recent trades

        Args:
            trades: List of trade dictionaries with 'pnl' and 'size'
            current_kelly: Current Kelly fraction

        Returns:
            KellyUpdate if successful, None if insufficient data
        """
        if len(trades) < self.min_trades:
            return None

        # Use most recent trades
        recent_trades = trades[-self.lookback_trades:]

        # Calculate win rate
        wins = [t for t in recent_trades if t.get('pnl', 0) > 0]
        losses = [t for t in recent_trades if t.get('pnl', 0) < 0]

        num_trades = len(recent_trades)
        num_wins = len(wins)

        if num_trades == 0:
            return None

        win_rate = num_wins / num_trades

        # Calculate average win/loss ratio
        if len(wins) == 0 or len(losses) == 0:
            # Not enough data for reliable Kelly
            avg_ratio = 1.0
        else:
            avg_win = sum(abs(t['pnl']) for t in wins) / len(wins)
            avg_loss = sum(abs(t['pnl']) for t in losses) / len(losses)

            if avg_loss == 0:
                avg_ratio = 2.0  # Default conservative ratio
            else:
                avg_ratio = avg_win / avg_loss

        # Kelly formula: f = (p * b - q) / b
        # Where: p = win rate, q = loss rate, b = win/loss ratio
        p = win_rate
        q = 1 - win_rate
        b = avg_ratio

        if b == 0:
            new_kelly = 0.0
        else:
            new_kelly = (p * b - q) / b

        # Ensure non-negative
        new_kelly = max(0.0, new_kelly)

        # Create update record
        update = KellyUpdate(
            timestamp=datetime.now(),
            old_kelly=current_kelly,
            new_kelly=new_kelly,
            win_rate=win_rate,
            avg_win_loss_ratio=avg_ratio,
            num_trades=num_trades
        )

        self.update_history.append(update)

        return update

    def get_latest_kelly(self) -> Optional[float]:
        """
        Get most recent Kelly fraction

        Returns:
            Latest Kelly fraction or None if no updates
        """
        if not self.update_history:
            return None

        return self.update_history[-1].new_kelly

    def get_update_history(self) -> List[KellyUpdate]:
        """
        Get full Kelly update history

        Returns:
            List of Kelly updates
        """
        return self.update_history.copy()
