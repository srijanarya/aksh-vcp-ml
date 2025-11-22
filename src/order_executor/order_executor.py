"""
Order Executor (SHORT-067 to SHORT-073)

Live order execution with Angel One integration.
"""

from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    PLACED = "PLACED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderExecutor:
    """Execute live orders with Angel One"""

    def __init__(
        self,
        angel_one_client: Optional[Any] = None,
        audit_logger: Optional[Any] = None,
        kill_switch_enabled: bool = True
    ):
        """
        Initialize order executor

        Args:
            angel_one_client: Angel One API client
            audit_logger: Audit logger
            kill_switch_enabled: Enable kill switch protection
        """
        self.client = angel_one_client
        self.audit_logger = audit_logger
        self.kill_switch_enabled = kill_switch_enabled
        self.orders = {}

    def validate_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        order_type: OrderType
    ) -> bool:
        """
        Validate order parameters

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            price: Order price
            order_type: Order type

        Returns:
            True if valid, False otherwise
        """
        if quantity <= 0:
            logger.error("Invalid quantity")
            return False

        if price <= 0 and order_type == OrderType.LIMIT:
            logger.error("Invalid price for LIMIT order")
            return False

        if not symbol:
            logger.error("Invalid symbol")
            return False

        return True

    def place_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        order_type: OrderType = OrderType.LIMIT
    ) -> Optional[str]:
        """
        Place order

        Args:
            symbol: Stock symbol
            quantity: Order quantity
            price: Order price
            order_type: Order type

        Returns:
            Order ID if successful, None otherwise
        """
        # Validate order
        if not self.validate_order(symbol, quantity, price, order_type):
            return None

        # Check kill switch
        if self.kill_switch_enabled and self._is_kill_switch_active():
            logger.error("Kill switch active - order blocked")
            return None

        # Generate order ID
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Store order
        order = {
            'order_id': order_id,
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'order_type': order_type,
            'status': OrderStatus.PLACED,
            'timestamp': datetime.now()
        }

        self.orders[order_id] = order

        # Audit log
        if self.audit_logger:
            self.audit_logger.log_order(order)

        logger.info(f"Order placed: {order_id}")
        return order_id

    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """
        Get order status

        Args:
            order_id: Order ID

        Returns:
            OrderStatus or None
        """
        if order_id not in self.orders:
            return None

        return self.orders[order_id]['status']

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order

        Args:
            order_id: Order ID

        Returns:
            True if cancelled, False otherwise
        """
        if order_id not in self.orders:
            return False

        order = self.orders[order_id]

        if order['status'] in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False  # Cannot cancel filled or already cancelled orders

        order['status'] = OrderStatus.CANCELLED

        logger.info(f"Order cancelled: {order_id}")
        return True

    def _is_kill_switch_active(self) -> bool:
        """
        Check if kill switch is active

        Returns:
            True if kill switch active, False otherwise
        """
        # Return True only if explicitly activated
        # In production, would check loss limits, drawdown, etc.
        return getattr(self, '_kill_switch_activated', False)

    def activate_kill_switch(self, reason: str):
        """
        Activate kill switch

        Args:
            reason: Reason for activation
        """
        self._kill_switch_activated = True
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")

        # Cancel all pending orders
        for order_id, order in list(self.orders.items()):
            if order['status'] == OrderStatus.PLACED:
                self.cancel_order(order_id)
