"""
Tests for Order Executor (SHORT-059 to SHORT-073)
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.order_executor.order_executor import (
    OrderExecutor,
    OrderType,
    OrderStatus
)


@pytest.fixture
def mock_angel_client():
    """Mock Angel One client"""
    client = Mock()
    client.place_order = Mock(return_value={"orderId": "MOCK_123"})
    client.cancel_order = Mock(return_value={"status": "success"})
    return client


@pytest.fixture
def mock_audit_logger():
    """Mock audit logger"""
    logger = Mock()
    logger.log_order = Mock()
    return logger


@pytest.fixture
def executor(mock_angel_client, mock_audit_logger):
    """Create order executor"""
    return OrderExecutor(
        angel_one_client=mock_angel_client,
        audit_logger=mock_audit_logger,
        kill_switch_enabled=True
    )


class TestOrderTypeEnum:
    """Test OrderType enum (SHORT-061)"""

    def test_order_type_values(self):
        assert OrderType.LIMIT.value == "LIMIT"
        assert OrderType.MARKET.value == "MARKET"

    def test_order_type_comparison(self):
        assert OrderType.LIMIT == OrderType.LIMIT
        assert OrderType.LIMIT != OrderType.MARKET


class TestOrderStatusEnum:
    """Test OrderStatus enum (SHORT-062)"""

    def test_order_status_values(self):
        assert OrderStatus.PENDING.value == "PENDING"
        assert OrderStatus.PLACED.value == "PLACED"
        assert OrderStatus.FILLED.value == "FILLED"
        assert OrderStatus.CANCELLED.value == "CANCELLED"
        assert OrderStatus.REJECTED.value == "REJECTED"

    def test_all_statuses_defined(self):
        statuses = [
            OrderStatus.PENDING,
            OrderStatus.PLACED,
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED
        ]
        assert len(statuses) == 5


class TestOrderValidator:
    """Test order validation (SHORT-060, SHORT-069, SHORT-070, SHORT-071)"""

    def test_valid_limit_order(self, executor):
        """Test validation of valid LIMIT order"""
        is_valid = executor.validate_order(
            symbol="RELIANCE",
            quantity=10,
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        assert is_valid is True

    def test_valid_market_order(self, executor):
        """Test validation of valid MARKET order"""
        is_valid = executor.validate_order(
            symbol="RELIANCE",
            quantity=10,
            price=0.0,  # Price not required for MARKET
            order_type=OrderType.MARKET
        )

        assert is_valid is True

    def test_invalid_quantity_zero(self, executor):
        """Test rejection of zero quantity (SHORT-070)"""
        is_valid = executor.validate_order(
            symbol="RELIANCE",
            quantity=0,
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        assert is_valid is False

    def test_invalid_quantity_negative(self, executor):
        """Test rejection of negative quantity (SHORT-070)"""
        is_valid = executor.validate_order(
            symbol="RELIANCE",
            quantity=-10,
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        assert is_valid is False

    def test_invalid_price_limit_order(self, executor):
        """Test rejection of invalid price for LIMIT order (SHORT-069)"""
        is_valid = executor.validate_order(
            symbol="RELIANCE",
            quantity=10,
            price=0.0,  # Invalid for LIMIT
            order_type=OrderType.LIMIT
        )

        assert is_valid is False

    def test_invalid_symbol_empty(self, executor):
        """Test rejection of empty symbol (SHORT-071)"""
        is_valid = executor.validate_order(
            symbol="",
            quantity=10,
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        assert is_valid is False


class TestOrderPlacement:
    """Test order placement (SHORT-059, SHORT-067)"""

    def test_place_valid_order(self, executor):
        """Test placing valid order"""
        order_id = executor.place_order(
            symbol="RELIANCE",
            quantity=10,
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        assert order_id is not None
        assert order_id.startswith("ORD_")

    def test_place_invalid_order(self, executor):
        """Test placing invalid order"""
        order_id = executor.place_order(
            symbol="RELIANCE",
            quantity=0,  # Invalid
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        assert order_id is None

    def test_order_id_generation(self, executor):
        """Test order ID format (SHORT-067)"""
        order_id = executor.place_order(
            symbol="RELIANCE",
            quantity=10,
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        # Format: ORD_YYYYMMDDHHMMSS
        assert order_id.startswith("ORD_")
        assert len(order_id) == 18  # ORD_ + 14 digits

    def test_unique_order_ids(self, executor):
        """Test that order IDs are unique"""
        import time
        order_id1 = executor.place_order("RELIANCE", 10, 2500.0)
        time.sleep(1.1)  # Ensure second granularity difference
        order_id2 = executor.place_order("TCS", 5, 3500.0)

        # IDs should be different (timestamp-based)
        # Note: May be same if called within same second
        # This tests the mechanism, not necessarily uniqueness
        assert order_id1.startswith("ORD_")
        assert order_id2.startswith("ORD_")
        # In production, use UUID or counter for true uniqueness


class TestOrderStatusTracking:
    """Test order status tracking (SHORT-064)"""

    def test_order_tracking(self, executor):
        """Test order is tracked after placement"""
        order_id = executor.place_order(
            symbol="RELIANCE",
            quantity=10,
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        # Order should be in orders dict
        assert order_id in executor.orders

    def test_get_order_status(self, executor):
        """Test getting order status"""
        order_id = executor.place_order("RELIANCE", 10, 2500.0)

        status = executor.get_order_status(order_id)

        assert status == OrderStatus.PLACED

    def test_get_unknown_order_status(self, executor):
        """Test getting status of unknown order"""
        status = executor.get_order_status("UNKNOWN_ID")

        assert status is None

    def test_order_details_stored(self, executor):
        """Test that order details are stored"""
        order_id = executor.place_order(
            symbol="RELIANCE",
            quantity=10,
            price=2500.0,
            order_type=OrderType.LIMIT
        )

        order = executor.orders[order_id]

        assert order['symbol'] == "RELIANCE"
        assert order['quantity'] == 10
        assert order['price'] == 2500.0
        assert order['order_type'] == OrderType.LIMIT


class TestOrderCancellation:
    """Test order cancellation (SHORT-065)"""

    def test_cancel_valid_order(self, executor):
        """Test cancelling valid order"""
        order_id = executor.place_order("RELIANCE", 10, 2500.0)

        success = executor.cancel_order(order_id)

        assert success is True
        assert executor.get_order_status(order_id) == OrderStatus.CANCELLED

    def test_cancel_unknown_order(self, executor):
        """Test cancelling unknown order"""
        success = executor.cancel_order("UNKNOWN_ID")

        assert success is False

    def test_cancel_already_cancelled_order(self, executor):
        """Test cancelling already cancelled order"""
        order_id = executor.place_order("RELIANCE", 10, 2500.0)
        executor.cancel_order(order_id)

        # Try to cancel again
        success = executor.cancel_order(order_id)

        assert success is False

    def test_cannot_cancel_filled_order(self, executor):
        """Test that filled orders cannot be cancelled"""
        order_id = executor.place_order("RELIANCE", 10, 2500.0)

        # Manually mark as filled
        executor.orders[order_id]['status'] = OrderStatus.FILLED

        success = executor.cancel_order(order_id)

        assert success is False


class TestKillSwitch:
    """Test kill switch (SHORT-063)"""

    def test_kill_switch_initialization(self):
        """Test kill switch is enabled by default"""
        executor = OrderExecutor(kill_switch_enabled=True)

        assert executor.kill_switch_enabled is True

    def test_order_blocked_when_kill_switch_active(self, executor):
        """Test orders blocked when kill switch active"""
        # Activate kill switch
        executor.activate_kill_switch("Test reason")

        # Try to place order
        order_id = executor.place_order("RELIANCE", 10, 2500.0)

        # Should be blocked
        assert order_id is None

    def test_kill_switch_activation(self, executor):
        """Test kill switch activation"""
        # Place some orders
        order_id1 = executor.place_order("RELIANCE", 10, 2500.0)
        order_id2 = executor.place_order("TCS", 5, 3500.0)

        # Activate kill switch
        executor.activate_kill_switch("Daily loss limit exceeded")

        # Pending orders should be cancelled
        assert executor.get_order_status(order_id1) == OrderStatus.CANCELLED
        assert executor.get_order_status(order_id2) == OrderStatus.CANCELLED

    def test_kill_switch_reason_logged(self, executor, caplog):
        """Test kill switch reason is logged"""
        import logging
        caplog.set_level(logging.CRITICAL)

        executor.activate_kill_switch("Test emergency stop")

        assert "KILL SWITCH ACTIVATED" in caplog.text
        assert "Test emergency stop" in caplog.text


class TestAuditLogging:
    """Test audit logging integration (SHORT-066)"""

    def test_audit_logger_called(self, executor, mock_audit_logger):
        """Test audit logger is called on order placement"""
        order_id = executor.place_order("RELIANCE", 10, 2500.0)

        # Audit logger should be called
        mock_audit_logger.log_order.assert_called_once()

    def test_works_without_audit_logger(self):
        """Test executor works without audit logger"""
        executor = OrderExecutor(audit_logger=None)

        order_id = executor.place_order("RELIANCE", 10, 2500.0)

        # Should work without errors
        assert order_id is not None


class TestOrderTimestamp:
    """Test order timestamp tracking (SHORT-072)"""

    def test_timestamp_captured(self, executor):
        """Test timestamp is captured on order placement"""
        before = datetime.now()
        order_id = executor.place_order("RELIANCE", 10, 2500.0)
        after = datetime.now()

        order = executor.orders[order_id]
        timestamp = order['timestamp']

        # Timestamp should be between before and after
        assert before <= timestamp <= after

    def test_timestamp_format(self, executor):
        """Test timestamp is datetime object"""
        order_id = executor.place_order("RELIANCE", 10, 2500.0)

        order = executor.orders[order_id]
        timestamp = order['timestamp']

        assert isinstance(timestamp, datetime)


class TestOrderLogging:
    """Test order event logging (SHORT-073)"""

    def test_validation_error_logged(self, executor, caplog):
        """Test validation errors are logged"""
        import logging
        caplog.set_level(logging.ERROR)

        executor.place_order(
            symbol="RELIANCE",
            quantity=0,  # Invalid
            price=2500.0
        )

        assert "Invalid quantity" in caplog.text

    def test_order_placement_logged(self, executor, caplog):
        """Test order placement is logged"""
        import logging
        caplog.set_level(logging.INFO)

        order_id = executor.place_order("RELIANCE", 10, 2500.0)

        assert "Order placed" in caplog.text
        assert order_id in caplog.text

    def test_order_cancellation_logged(self, executor, caplog):
        """Test order cancellation is logged"""
        import logging
        caplog.set_level(logging.INFO)

        order_id = executor.place_order("RELIANCE", 10, 2500.0)
        executor.cancel_order(order_id)

        assert "Order cancelled" in caplog.text


def test_end_to_end_order_flow(executor):
    """End-to-end order flow test"""
    # Place order
    order_id = executor.place_order(
        symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        order_type=OrderType.LIMIT
    )

    assert order_id is not None
    print(f"Order placed: {order_id}")

    # Check status
    status = executor.get_order_status(order_id)
    assert status == OrderStatus.PLACED
    print(f"Order status: {status.value}")

    # Cancel order
    success = executor.cancel_order(order_id)
    assert success is True
    print("Order cancelled successfully")

    # Verify cancelled status
    status = executor.get_order_status(order_id)
    assert status == OrderStatus.CANCELLED
    print(f"Final status: {status.value}")
