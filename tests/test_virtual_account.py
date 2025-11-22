"""
Tests for Virtual Account (SHORT-074 to SHORT-083)
"""

import pytest
from datetime import datetime, timedelta

from src.paper_trading.virtual_account import (
    VirtualAccount,
    VirtualPosition
)


@pytest.fixture
def account():
    """Create virtual account"""
    return VirtualAccount(initial_capital=100000)


class TestVirtualPosition:
    """Test VirtualPosition dataclass (SHORT-075)"""

    def test_position_creation(self):
        """Test position creation"""
        position = VirtualPosition(
            symbol="RELIANCE",
            quantity=10,
            entry_price=2500.0,
            entry_time=datetime.now(),
            current_price=2500.0
        )

        assert position.symbol == "RELIANCE"
        assert position.quantity == 10
        assert position.entry_price == 2500.0

    def test_current_value_calculation(self):
        """Test current value property"""
        position = VirtualPosition(
            symbol="RELIANCE",
            quantity=10,
            entry_price=2500.0,
            entry_time=datetime.now(),
            current_price=2600.0
        )

        assert position.current_value == 26000.0  # 10 * 2600

    def test_pnl_calculation(self):
        """Test P&L calculation"""
        position = VirtualPosition(
            symbol="RELIANCE",
            quantity=10,
            entry_price=2500.0,
            entry_time=datetime.now(),
            current_price=2600.0
        )

        assert position.pnl == 1000.0  # (2600 - 2500) * 10

    def test_pnl_pct_calculation(self):
        """Test P&L percentage calculation"""
        position = VirtualPosition(
            symbol="RELIANCE",
            quantity=10,
            entry_price=2500.0,
            entry_time=datetime.now(),
            current_price=2600.0
        )

        assert position.pnl_pct == 4.0  # (2600 - 2500) / 2500 * 100

    def test_negative_pnl(self):
        """Test negative P&L"""
        position = VirtualPosition(
            symbol="RELIANCE",
            quantity=10,
            entry_price=2500.0,
            entry_time=datetime.now(),
            current_price=2400.0
        )

        assert position.pnl == -1000.0
        assert position.pnl_pct == -4.0


class TestVirtualAccountCore:
    """Test VirtualAccount core (SHORT-074)"""

    def test_account_initialization(self):
        """Test account initialization"""
        account = VirtualAccount(initial_capital=100000)

        assert account.initial_capital == 100000
        assert account.cash == 100000
        assert len(account.positions) == 0
        assert len(account.trade_history) == 0

    def test_default_capital(self):
        """Test default initial capital"""
        account = VirtualAccount()

        assert account.initial_capital == 100000


class TestVirtualBuyOrder:
    """Test virtual buy order execution (SHORT-076, SHORT-082)"""

    def test_successful_buy(self, account):
        """Test successful buy order"""
        success = account.buy(
            symbol="RELIANCE",
            quantity=10,
            price=2500.0
        )

        assert success is True
        assert "RELIANCE" in account.positions
        assert account.cash == 75000  # 100000 - 25000

    def test_buy_with_custom_timestamp(self, account):
        """Test buy with custom timestamp (SHORT-083)"""
        timestamp = datetime(2024, 1, 1, 9, 15)

        success = account.buy(
            symbol="RELIANCE",
            quantity=10,
            price=2500.0,
            timestamp=timestamp
        )

        assert success is True
        position = account.positions["RELIANCE"]
        assert position.entry_time == timestamp

    def test_buy_with_auto_timestamp(self, account):
        """Test buy with auto-generated timestamp (SHORT-083)"""
        before = datetime.now()
        success = account.buy("RELIANCE", 10, 2500.0)
        after = datetime.now()

        assert success is True
        position = account.positions["RELIANCE"]
        assert before <= position.entry_time <= after

    def test_buy_insufficient_funds(self, account):
        """Test buy rejection due to insufficient funds (SHORT-082)"""
        success = account.buy(
            symbol="RELIANCE",
            quantity=100,  # Requires 250,000
            price=2500.0
        )

        assert success is False
        assert len(account.positions) == 0
        assert account.cash == 100000  # Unchanged

    def test_multiple_positions(self, account):
        """Test buying multiple different positions"""
        account.buy("RELIANCE", 10, 2500.0)
        account.buy("TCS", 5, 3500.0)

        assert len(account.positions) == 2
        assert "RELIANCE" in account.positions
        assert "TCS" in account.positions


class TestVirtualSellOrder:
    """Test virtual sell order execution (SHORT-077)"""

    def test_successful_sell(self, account):
        """Test successful sell order"""
        # Buy first
        account.buy("RELIANCE", 10, 2500.0)

        # Update price
        account.positions["RELIANCE"].current_price = 2600.0

        # Sell
        success = account.sell(
            symbol="RELIANCE",
            price=2600.0
        )

        assert success is True
        assert "RELIANCE" not in account.positions
        assert account.cash == 101000  # 75000 + 26000

    def test_sell_nonexistent_position(self, account):
        """Test sell rejection for nonexistent position"""
        success = account.sell(
            symbol="RELIANCE",
            price=2600.0
        )

        assert success is False

    def test_sell_with_custom_timestamp(self, account):
        """Test sell with custom timestamp (SHORT-083)"""
        account.buy("RELIANCE", 10, 2500.0)

        timestamp = datetime(2024, 1, 15, 15, 30)
        success = account.sell(
            symbol="RELIANCE",
            price=2600.0,
            timestamp=timestamp
        )

        assert success is True
        # Check trade history timestamp
        last_trade = account.trade_history[-1]
        assert last_trade['timestamp'] == timestamp


class TestVirtualPriceUpdates:
    """Test virtual price updates (SHORT-078)"""

    def test_single_position_update(self, account):
        """Test updating single position price"""
        account.buy("RELIANCE", 10, 2500.0)

        account.update_prices({"RELIANCE": 2600.0})

        position = account.positions["RELIANCE"]
        assert position.current_price == 2600.0

    def test_multiple_position_updates(self, account):
        """Test updating multiple positions"""
        account.buy("RELIANCE", 10, 2500.0)
        account.buy("TCS", 5, 3500.0)

        account.update_prices({
            "RELIANCE": 2600.0,
            "TCS": 3600.0
        })

        assert account.positions["RELIANCE"].current_price == 2600.0
        assert account.positions["TCS"].current_price == 3600.0

    def test_update_missing_symbol(self, account):
        """Test updating with missing symbol"""
        account.buy("RELIANCE", 10, 2500.0)

        # Update only TCS (not held)
        account.update_prices({"TCS": 3600.0})

        # RELIANCE price should be unchanged
        position = account.positions["RELIANCE"]
        assert position.current_price == 2500.0  # Entry price

    def test_pnl_recalculation_after_update(self, account):
        """Test P&L recalculation after price update"""
        account.buy("RELIANCE", 10, 2500.0)

        # Update price
        account.update_prices({"RELIANCE": 2600.0})

        position = account.positions["RELIANCE"]
        assert position.pnl == 1000.0
        assert position.pnl_pct == 4.0


class TestVirtualEquityCalculation:
    """Test virtual equity calculation (SHORT-079)"""

    def test_equity_with_only_cash(self, account):
        """Test equity calculation with only cash"""
        equity = account.get_equity()

        assert equity == 100000

    def test_equity_with_positions(self, account):
        """Test equity calculation with positions"""
        account.buy("RELIANCE", 10, 2500.0)  # Cost: 25000
        account.update_prices({"RELIANCE": 2600.0})

        equity = account.get_equity()

        # 75000 (cash) + 26000 (position) = 101000
        assert equity == 101000

    def test_equity_with_multiple_positions(self, account):
        """Test equity with multiple positions"""
        account.buy("RELIANCE", 10, 2500.0)  # Cost: 25000
        account.buy("TCS", 5, 3500.0)  # Cost: 17500

        account.update_prices({
            "RELIANCE": 2600.0,  # Value: 26000
            "TCS": 3600.0  # Value: 18000
        })

        equity = account.get_equity()

        # 57500 (cash) + 26000 + 18000 = 101500
        assert equity == 101500

    def test_equity_after_sell(self, account):
        """Test equity after selling position"""
        account.buy("RELIANCE", 10, 2500.0)
        account.sell("RELIANCE", 2600.0)

        equity = account.get_equity()

        assert equity == 101000  # All cash


class TestVirtualPerformanceMetrics:
    """Test virtual performance metrics (SHORT-080)"""

    def test_performance_metrics_initial(self, account):
        """Test performance metrics at initialization"""
        perf = account.get_performance()

        assert perf['initial_capital'] == 100000
        assert perf['current_equity'] == 100000
        assert perf['cash'] == 100000
        assert perf['positions_value'] == 0
        assert perf['total_pnl'] == 0
        assert perf['total_return_pct'] == 0.0
        assert perf['open_positions'] == 0
        assert perf['total_trades'] == 0

    def test_performance_with_profit(self, account):
        """Test performance metrics with profit"""
        account.buy("RELIANCE", 10, 2500.0)
        account.update_prices({"RELIANCE": 2600.0})

        perf = account.get_performance()

        assert perf['initial_capital'] == 100000
        assert perf['current_equity'] == 101000
        assert perf['cash'] == 75000
        assert perf['positions_value'] == 26000
        assert perf['total_pnl'] == 1000
        assert perf['total_return_pct'] == 1.0
        assert perf['open_positions'] == 1
        assert perf['total_trades'] == 1

    def test_performance_with_loss(self, account):
        """Test performance metrics with loss"""
        account.buy("RELIANCE", 10, 2500.0)
        account.update_prices({"RELIANCE": 2400.0})

        perf = account.get_performance()

        assert perf['total_pnl'] == -1000
        assert perf['total_return_pct'] == -1.0

    def test_performance_after_trades(self, account):
        """Test performance after multiple trades"""
        # Buy and sell
        account.buy("RELIANCE", 10, 2500.0)
        account.sell("RELIANCE", 2600.0)

        account.buy("TCS", 5, 3500.0)

        perf = account.get_performance()

        assert perf['total_trades'] == 3  # 2 buys + 1 sell
        assert perf['open_positions'] == 1  # TCS still open


class TestVirtualTradeHistory:
    """Test virtual trade history (SHORT-081)"""

    def test_buy_recorded_in_history(self, account):
        """Test buy order recorded in history"""
        account.buy("RELIANCE", 10, 2500.0)

        assert len(account.trade_history) == 1

        trade = account.trade_history[0]
        assert trade['action'] == 'BUY'
        assert trade['symbol'] == 'RELIANCE'
        assert trade['quantity'] == 10
        assert trade['price'] == 2500.0

    def test_sell_recorded_in_history(self, account):
        """Test sell order recorded in history"""
        account.buy("RELIANCE", 10, 2500.0)
        account.sell("RELIANCE", 2600.0)

        assert len(account.trade_history) == 2

        sell_trade = account.trade_history[1]
        assert sell_trade['action'] == 'SELL'
        assert sell_trade['symbol'] == 'RELIANCE'
        assert sell_trade['price'] == 2600.0

    def test_pnl_in_sell_history(self, account):
        """Test P&L included in sell history"""
        account.buy("RELIANCE", 10, 2500.0)
        account.positions["RELIANCE"].current_price = 2600.0
        account.sell("RELIANCE", 2600.0)

        sell_trade = account.trade_history[1]
        assert 'pnl' in sell_trade
        assert sell_trade['pnl'] == 1000.0

    def test_trade_history_order(self, account):
        """Test trade history is chronological"""
        account.buy("RELIANCE", 10, 2500.0)
        account.buy("TCS", 5, 3500.0)
        account.sell("RELIANCE", 2600.0)

        assert len(account.trade_history) == 3
        assert account.trade_history[0]['symbol'] == 'RELIANCE'
        assert account.trade_history[0]['action'] == 'BUY'
        assert account.trade_history[1]['symbol'] == 'TCS'
        assert account.trade_history[2]['action'] == 'SELL'


class TestVirtualCashManagement:
    """Test virtual cash management (SHORT-082)"""

    def test_initial_cash(self, account):
        """Test initial cash equals initial capital"""
        assert account.cash == account.initial_capital

    def test_cash_deduction_on_buy(self, account):
        """Test cash deduction on buy"""
        initial_cash = account.cash
        cost = 10 * 2500.0

        account.buy("RELIANCE", 10, 2500.0)

        assert account.cash == initial_cash - cost

    def test_cash_addition_on_sell(self, account):
        """Test cash addition on sell"""
        account.buy("RELIANCE", 10, 2500.0)
        cash_after_buy = account.cash

        proceeds = 10 * 2600.0
        account.sell("RELIANCE", 2600.0)

        assert account.cash == cash_after_buy + proceeds

    def test_cash_conservation(self, account):
        """Test total value conservation"""
        initial_equity = account.get_equity()

        # Make trades at same price (no profit/loss)
        account.buy("RELIANCE", 10, 2500.0)
        account.sell("RELIANCE", 2500.0)

        final_equity = account.get_equity()

        # Equity should be approximately same (no costs in this implementation)
        assert abs(final_equity - initial_equity) < 1


def test_end_to_end_paper_trading():
    """End-to-end paper trading test"""
    account = VirtualAccount(initial_capital=100000)

    print(f"Initial Capital: {account.cash}")

    # Buy RELIANCE
    account.buy("RELIANCE", 10, 2500.0)
    print(f"After buying RELIANCE: Cash={account.cash}, Positions={len(account.positions)}")

    # Buy TCS
    account.buy("TCS", 5, 3500.0)
    print(f"After buying TCS: Cash={account.cash}, Positions={len(account.positions)}")

    # Update prices
    account.update_prices({
        "RELIANCE": 2600.0,
        "TCS": 3600.0
    })

    # Check performance
    perf = account.get_performance()
    print(f"\nPerformance:")
    print(f"  Equity: {perf['current_equity']}")
    print(f"  P&L: {perf['total_pnl']}")
    print(f"  Return: {perf['total_return_pct']:.2f}%")
    print(f"  Open Positions: {perf['open_positions']}")

    # Sell RELIANCE
    account.sell("RELIANCE", 2600.0)
    print(f"\nAfter selling RELIANCE: Cash={account.cash}")

    # Final performance
    final_perf = account.get_performance()
    print(f"\nFinal Performance:")
    print(f"  Total Trades: {final_perf['total_trades']}")
    print(f"  Total Return: {final_perf['total_return_pct']:.2f}%")

    assert len(account.trade_history) == 3
    assert final_perf['open_positions'] == 1
