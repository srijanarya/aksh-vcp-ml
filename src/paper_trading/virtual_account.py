"""
Paper Trading System (SHORT-059 to SHORT-066)

Virtual account for paper trading with real-time simulation.
"""

from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class VirtualPosition:
    """Virtual trading position"""
    symbol: str
    quantity: int
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0

    @property
    def current_value(self) -> float:
        """Current position value"""
        return self.quantity * self.current_price

    @property
    def pnl(self) -> float:
        """Position P&L"""
        return (self.current_price - self.entry_price) * self.quantity

    @property
    def pnl_pct(self) -> float:
        """Position P&L percentage"""
        return (self.current_price - self.entry_price) / self.entry_price * 100


class VirtualAccount:
    """Virtual trading account for paper trading"""

    def __init__(self, initial_capital: float = 100000):
        """
        Initialize virtual account

        Args:
            initial_capital: Starting capital
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, VirtualPosition] = {}
        self.trade_history: List[Dict] = []

    def buy(
        self,
        symbol: str,
        quantity: int,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Execute virtual buy order

        Args:
            symbol: Stock symbol
            quantity: Quantity to buy
            price: Buy price
            timestamp: Order timestamp

        Returns:
            True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()

        cost = quantity * price

        if cost > self.cash:
            return False  # Insufficient funds

        self.cash -= cost

        position = VirtualPosition(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            entry_time=timestamp,
            current_price=price
        )

        self.positions[symbol] = position

        self.trade_history.append({
            'action': 'BUY',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'timestamp': timestamp
        })

        return True

    def sell(
        self,
        symbol: str,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Execute virtual sell order

        Args:
            symbol: Stock symbol
            price: Sell price
            timestamp: Order timestamp

        Returns:
            True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()

        if symbol not in self.positions:
            return False  # No position to sell

        position = self.positions[symbol]
        proceeds = position.quantity * price

        self.cash += proceeds
        del self.positions[symbol]

        self.trade_history.append({
            'action': 'SELL',
            'symbol': symbol,
            'quantity': position.quantity,
            'price': price,
            'pnl': position.pnl,
            'timestamp': timestamp
        })

        return True

    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for positions

        Args:
            prices: Dict mapping symbol to current price
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]

    def get_equity(self) -> float:
        """
        Get total account equity

        Returns:
            Total equity (cash + positions)
        """
        equity = self.cash

        for position in self.positions.values():
            equity += position.current_value

        return equity

    def get_performance(self) -> Dict:
        """
        Get account performance metrics

        Returns:
            Dict with performance metrics
        """
        equity = self.get_equity()
        total_pnl = equity - self.initial_capital
        total_return_pct = (total_pnl / self.initial_capital) * 100

        return {
            'initial_capital': self.initial_capital,
            'current_equity': equity,
            'cash': self.cash,
            'positions_value': equity - self.cash,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'open_positions': len(self.positions),
            'total_trades': len(self.trade_history)
        }
