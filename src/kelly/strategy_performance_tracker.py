"""
Strategy Performance Tracker (SHORT-016)

Track strategy performance for Kelly fraction calculation.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import sqlite3
import json


@dataclass
class Trade:
    """Trade record"""
    profit: float
    timestamp: datetime


class StrategyPerformanceTracker:
    """Track strategy performance metrics"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize performance tracker

        Args:
            db_path: Optional path to SQLite database for persistence
        """
        self.db_path = db_path
        self.trades: List[Trade] = []

    def record_trade(
        self,
        profit: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Record a trade outcome

        Args:
            profit: Profit/loss amount (positive = profit, negative = loss)
            timestamp: Trade timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.trades.append(Trade(profit=profit, timestamp=timestamp))

    def get_stats(self, window_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Get performance statistics

        Args:
            window_days: Optional rolling window in days

        Returns:
            Dict with performance metrics
        """
        trades = self.trades

        # Filter by window if specified
        if window_days is not None:
            cutoff = datetime.now() - timedelta(days=window_days)
            trades = [t for t in trades if t.timestamp >= cutoff]

        if not trades:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'current_streak': 0
            }

        wins = [t for t in trades if t.profit > 0]
        losses = [t for t in trades if t.profit < 0]

        win_rate = (len(wins) / len(trades) * 100) if trades else 0
        avg_profit = sum(t.profit for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.profit for t in losses) / len(losses) if losses else 0

        # Calculate consecutive streaks
        max_cons_wins = 0
        max_cons_losses = 0
        current_cons_wins = 0
        current_cons_losses = 0
        current_streak = 0

        for trade in trades:
            if trade.profit > 0:
                current_cons_wins += 1
                current_cons_losses = 0
                current_streak = current_cons_wins
                max_cons_wins = max(max_cons_wins, current_cons_wins)
            elif trade.profit < 0:
                current_cons_losses += 1
                current_cons_wins = 0
                current_streak = -current_cons_losses
                max_cons_losses = max(max_cons_losses, current_cons_losses)

        return {
            'total_trades': len(trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(win_rate, 2),
            'avg_profit': round(avg_profit, 2),
            'avg_loss': round(avg_loss, 2),
            'max_consecutive_wins': max_cons_wins,
            'max_consecutive_losses': max_cons_losses,
            'current_streak': current_streak
        }

    def save(self):
        """Save trades to database"""
        if not self.db_path:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profit REAL,
                timestamp TEXT
            )
        ''')

        for trade in self.trades:
            cursor.execute(
                'INSERT INTO trades (profit, timestamp) VALUES (?, ?)',
                (trade.profit, trade.timestamp.isoformat())
            )

        conn.commit()
        conn.close()

    def load(self):
        """Load trades from database"""
        if not self.db_path:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profit REAL,
                timestamp TEXT
            )
        ''')

        cursor.execute('SELECT profit, timestamp FROM trades')
        rows = cursor.fetchall()

        self.trades = [
            Trade(
                profit=row[0],
                timestamp=datetime.fromisoformat(row[1])
            )
            for row in rows
        ]

        conn.close()
