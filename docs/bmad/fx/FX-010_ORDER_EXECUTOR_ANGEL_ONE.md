# FX-010: Order Executor (Angel One Integration)

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-10 (Live Order Execution via Angel One API)
**Priority**: CRITICAL - HANDLE WITH EXTREME CARE
**Created**: November 19, 2025
**Status**: Specification

---

## ⚠️ CRITICAL WARNING

**THIS MODULE PLACES REAL ORDERS WITH REAL MONEY**

- A bug here = REAL FINANCIAL LOSS
- Triple-check ALL logic
- Comprehensive testing REQUIRED
- Manual approval before first live order
- Kill switch MUST be implemented
- Audit trail for EVERY action

---

## Table of Contents

1. [Overview](#overview)
2. [User Story](#user-story)
3. [Acceptance Criteria](#acceptance-criteria)
4. [Functional Design](#functional-design)
5. [Technical Specification](#technical-specification)
6. [API Contracts](#api-contracts)
7. [Data Models](#data-models)
8. [Business Rules](#business-rules)
9. [Test Cases](#test-cases)
10. [Edge Cases](#edge-cases)
11. [Performance Requirements](#performance-requirements)
12. [Dependencies](#dependencies)

---

## Overview

### Purpose

The Angel One Order Executor places LIVE orders on the Angel One brokerage platform after all validations pass. This is the FINAL step before real money is at risk.

### Background

**Angel One SmartAPI**:
- REST API for order management
- WebSocket for real-time updates
- 2FA authentication (TOTP)
- Rate limits: 10 orders/second
- Order types: MARKET, LIMIT, SL, SL-M

**Safety Philosophy**:
1. **Defense in depth**: Multiple validation layers
2. **Fail safe**: Reject orders on any doubt
3. **Audit everything**: Log every API call
4. **Human in the loop**: Critical decisions need approval
5. **Kill switch**: Emergency stop mechanism

### Scope

**In Scope**:
- Angel One authentication (JWT + TOTP)
- Place LIMIT orders for equity delivery
- Modify pending orders
- Cancel orders
- Query order status
- Handle order rejections
- Rate limiting (10/sec max)
- Comprehensive error handling
- Audit logging

**Out of Scope**:
- MARKET orders (too risky without careful design)
- F&O trading (future phase)
- Basket orders
- GTT (Good Till Trigger) orders

---

## User Story

**As** the Trading System
**I want** to place validated orders on Angel One
**So that** I can execute live trades with real capital after validation

### Scenarios

#### Scenario 1: Successful Order Placement

**Given**:
- Signal: BUY RELIANCE @ ₹2,500
- Position size: 10 shares
- All validations passed
- Kill switch: OFF

**When**: Place order

**Then**:
1. Authenticate with Angel One (if needed)
2. Validate order parameters
3. Check rate limits
4. Prepare order request
5. Call Angel One API: placeOrder()
6. Receive order ID: "241119000012345"
7. Log order details
8. Send Telegram alert: "✅ Order placed: BUY 10 RELIANCE @ ₹2,500"
9. Return order ID to caller

#### Scenario 2: Order Rejection

**Given**:
- Signal: BUY TCS @ ₹3,700
- Insufficient margin in Angel One account

**When**: Place order

**Then**:
1. Attempt to place order
2. Receive API error: "RMS:Margin Exceeded"
3. Log error with full context
4. Send Telegram alert: "❌ Order REJECTED: Insufficient margin"
5. Return error to caller
6. DO NOT retry automatically

#### Scenario 3: Rate Limit Exceeded

**Given**:
- 10 orders placed in last 1 second
- New order request arrives

**When**: Attempt to place order

**Then**:
1. Check rate limiter: 10/10 slots used
2. Wait 100ms for slot to free up
3. Retry order placement
4. Log: "Rate limit: Delayed order by 100ms"

#### Scenario 4: Kill Switch Activated

**Given**:
- Kill switch manually activated
- New order signal arrives

**When**: Attempt to place order

**Then**:
1. Check kill switch status: ACTIVE
2. Reject order immediately
3. Log: "KILL SWITCH ACTIVE: Order blocked"
4. Send Telegram alert: "🛑 Kill switch active. Trading halted."
5. Return error to caller

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Authenticate with Angel One using API key, client ID, password, TOTP
✅ **AC-2**: Place LIMIT orders for equity delivery
✅ **AC-3**: Validate all order parameters before API call:
  - Symbol exists
  - Price > 0
  - Quantity > 0
  - Side = BUY or SELL
  - Order type = LIMIT
  - Product type = DELIVERY

✅ **AC-4**: Implement rate limiting (max 10 orders/second)
✅ **AC-5**: Handle API errors gracefully:
  - Network errors
  - Authentication failures
  - Order rejections
  - Rate limit errors

✅ **AC-6**: Log ALL API calls with:
  - Timestamp
  - Request parameters
  - Response data
  - Success/failure status
  - Latency

✅ **AC-7**: Send Telegram notifications for:
  - Order placed
  - Order rejected
  - Order filled
  - Order cancelled
  - Authentication failures

✅ **AC-8**: Implement kill switch (manual trading halt)
✅ **AC-9**: Query order status by order ID
✅ **AC-10**: Cancel pending orders

### Should Have

⭕ **AC-11**: Modify pending orders (price/quantity)
⭕ **AC-12**: Retry failed orders (with exponential backoff)
⭕ **AC-13**: Validate against duplicate orders
⭕ **AC-14**: Check available margin before placing order

### Nice to Have

🔵 **AC-15**: Web UI to view order history
🔵 **AC-16**: Export order logs to CSV
🔵 **AC-17**: Integration with portfolio tracker

---

## Functional Design

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AngelOneExecutor                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  AuthenticationManager                                │ │
│  │  - Login with API key + TOTP                          │ │
│  │  - Refresh JWT token                                  │ │
│  │  - Handle session expiry                              │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  OrderValidator                                       │ │
│  │  - Validate order parameters                          │ │
│  │  - Check kill switch                                  │ │
│  │  - Verify symbol exists                               │ │
│  │  - Validate price/quantity limits                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  RateLimiter                                          │ │
│  │  - Track orders per second                            │ │
│  │  - Enforce 10/sec limit                               │ │
│  │  - Queue excess orders                                │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  OrderPlacer                                          │ │
│  │  - Prepare API request                                │ │
│  │  - Call Angel One placeOrder()                        │ │
│  │  - Parse response                                     │ │
│  │  - Handle errors                                      │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  OrderTracker                                         │ │
│  │  - Store order ID mapping                             │ │
│  │  - Query order status                                 │ │
│  │  - Track fills/rejections                             │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  AuditLogger                                          │ │
│  │  - Log all API calls                                  │ │
│  │  - Log all responses                                  │ │
│  │  - Create audit trail                                 │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Order Placement Flow

```
Input: Order Request
  ├─ Symbol: "RELIANCE-EQ"
  ├─ Side: "BUY"
  ├─ Quantity: 10
  ├─ Price: ₹2,500
  └─ Order Type: "LIMIT"

Step 1: Check Kill Switch
  ├─ Query: kill_switch.is_active()
  ├─ Status: False (trading allowed)
  └─ Proceed ✅

Step 2: Validate Order
  ├─ Symbol validation: RELIANCE-EQ exists ✅
  ├─ Price validation: 2500 > 0 ✅
  ├─ Quantity validation: 10 > 0 ✅
  ├─ Side validation: "BUY" in ["BUY", "SELL"] ✅
  ├─ Order type: "LIMIT" ✅
  └─ All validations pass ✅

Step 3: Check Rate Limit
  ├─ Current rate: 3/10 orders in last second
  ├─ Limit check: 3 < 10 ✅
  └─ Proceed immediately

Step 4: Authenticate (if needed)
  ├─ Check: is_authenticated = True
  ├─ Token expiry: Valid for 4 hours
  └─ Skip re-login

Step 5: Prepare API Request
  └─ Request body: {
      "variety": "NORMAL",
      "tradingsymbol": "RELIANCE-EQ",
      "symboltoken": "2885",
      "transactiontype": "BUY",
      "exchange": "NSE",
      "ordertype": "LIMIT",
      "producttype": "DELIVERY",
      "duration": "DAY",
      "price": "2500.00",
      "quantity": "10"
    }

Step 6: Call Angel One API
  ├─ Endpoint: POST /rest/secure/angelbroking/order/v1/placeOrder
  ├─ Headers: {
  │    "Authorization": "Bearer {jwt_token}",
  │    "Content-Type": "application/json",
  │    "X-ClientLocalIP": "{client_ip}",
  │    "X-ClientPublicIP": "{public_ip}",
  │    "X-MACAddress": "{mac_address}",
  │    "X-PrivateKey": "{api_key}"
  │  }
  └─ Latency: 245ms

Step 7: Parse Response
  └─ Response: {
      "status": true,
      "message": "SUCCESS",
      "errorcode": "",
      "data": {
        "orderid": "241119000012345",
        "uniqueorderid": "abcd1234"
      }
    }

Step 8: Log Transaction
  └─ Audit log entry: {
      "timestamp": "2025-11-19T09:45:23.456Z",
      "action": "PLACE_ORDER",
      "symbol": "RELIANCE-EQ",
      "side": "BUY",
      "quantity": 10,
      "price": 2500.00,
      "order_id": "241119000012345",
      "status": "SUCCESS",
      "latency_ms": 245
    }

Step 9: Send Telegram Notification
  └─ Message: "✅ Order Placed
               📊 RELIANCE-EQ
               🔢 BUY 10 shares
               💰 Price: ₹2,500
               🆔 Order ID: 241119000012345"

Step 10: Return to Caller
  └─ Output: {
      "success": true,
      "order_id": "241119000012345",
      "message": "Order placed successfully"
    }
```

---

## Technical Specification

### Class: `AngelOneExecutor`

```python
# execution/angel_one_executor.py
from SmartApi import SmartConnect
import pyotp
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
import time
from collections import deque

class OrderValidationError(Exception):
    """Raised when order validation fails"""
    pass

class RateLimitExceededError(Exception):
    """Raised when rate limit exceeded"""
    pass

class KillSwitchActiveError(Exception):
    """Raised when kill switch is active"""
    pass

class AngelOneExecutor:
    """
    Execute orders on Angel One platform

    CRITICAL: This class places REAL orders with REAL money.
    Handle with extreme care.

    Responsibilities:
    - Authenticate with Angel One
    - Place LIMIT orders
    - Validate all parameters
    - Enforce rate limits
    - Log all actions
    - Handle errors safely
    """

    def __init__(
        self,
        api_key: str,
        client_id: str,
        password: str,
        totp_secret: str,
        telegram_bot,
        max_orders_per_second: int = 10,
    ):
        """
        Initialize Angel One Executor

        Args:
            api_key: Angel One API key
            client_id: Client ID (login ID)
            password: Account password
            totp_secret: TOTP secret for 2FA
            telegram_bot: TelegramBot instance
            max_orders_per_second: Rate limit (default: 10)
        """
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret
        self.telegram_bot = telegram_bot
        self.max_orders_per_second = max_orders_per_second

        self.logger = logging.getLogger(__name__)

        # SmartAPI client
        self.smart_api = SmartConnect(api_key=api_key)

        # Authentication state
        self.jwt_token = None
        self.refresh_token = None
        self.feed_token = None
        self.token_expiry = None
        self.is_authenticated = False

        # Rate limiting
        self.order_timestamps = deque(maxlen=max_orders_per_second)

        # Kill switch
        self.kill_switch_active = False

        # Order tracking
        self.orders = {}  # order_id -> order details

    def login(self):
        """
        Authenticate with Angel One

        Raises:
            Exception: If authentication fails
        """
        self.logger.info("Authenticating with Angel One...")

        try:
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_secret).now()

            # Login
            session = self.smart_api.generateSession(
                clientCode=self.client_id,
                password=self.password,
                totp=totp,
            )

            if not session["status"]:
                raise Exception(f"Login failed: {session}")

            # Store tokens
            self.jwt_token = session["data"]["jwtToken"]
            self.refresh_token = session["data"]["refreshToken"]
            self.feed_token = session["data"]["feedToken"]

            # Token valid for 24 hours (conservative: 23 hours)
            self.token_expiry = datetime.now() + timedelta(hours=23)

            self.is_authenticated = True

            self.logger.info("Angel One login successful")

            # Send notification
            self.telegram_bot.send_message(
                "✅ Angel One Authentication Successful\n"
                f"🕐 Token valid until: {self.token_expiry.strftime('%Y-%m-%d %H:%M')}"
            )

        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")

            # Send alert
            self.telegram_bot.send_message(
                f"❌ Angel One Authentication FAILED\n"
                f"Error: {str(e)}"
            )

            raise

    def _check_authentication(self):
        """Check if authenticated and token is valid"""

        if not self.is_authenticated:
            self.login()
            return

        # Check token expiry
        if datetime.now() >= self.token_expiry:
            self.logger.warning("Token expired. Re-authenticating...")
            self.login()

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        order_type: str = "LIMIT",
        product_type: str = "DELIVERY",
    ) -> Dict:
        """
        Place order on Angel One

        Args:
            symbol: Stock symbol (e.g., "RELIANCE-EQ")
            side: "BUY" or "SELL"
            quantity: Number of shares
            price: Order price
            order_type: "LIMIT" (default), "MARKET" (not recommended)
            product_type: "DELIVERY" (default), "INTRADAY"

        Returns:
            Dict with order details:
            {
                "success": True,
                "order_id": "241119000012345",
                "message": "Order placed successfully"
            }

        Raises:
            KillSwitchActiveError: If kill switch is active
            OrderValidationError: If order validation fails
            RateLimitExceededError: If rate limit exceeded
            Exception: For other errors
        """
        # Step 1: Check kill switch
        if self.kill_switch_active:
            error_msg = "KILL SWITCH ACTIVE: Trading halted"
            self.logger.error(error_msg)
            self.telegram_bot.send_message(f"🛑 {error_msg}")
            raise KillSwitchActiveError(error_msg)

        # Step 2: Validate order
        self._validate_order(symbol, side, quantity, price, order_type)

        # Step 3: Check authentication
        self._check_authentication()

        # Step 4: Check rate limit
        self._check_rate_limit()

        # Step 5: Get symbol token
        symbol_token = self._get_symbol_token(symbol)

        # Step 6: Prepare order parameters
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": symbol_token,
            "transactiontype": side,
            "exchange": "NSE",
            "ordertype": order_type,
            "producttype": product_type,
            "duration": "DAY",
            "price": f"{price:.2f}",
            "quantity": str(quantity),
        }

        # Step 7: Place order
        try:
            start_time = time.time()

            response = self.smart_api.placeOrder(order_params)

            latency_ms = (time.time() - start_time) * 1000

            # Step 8: Parse response
            if response["status"]:
                order_id = response["data"]["orderid"]

                # Store order
                self.orders[order_id] = {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "order_type": order_type,
                    "timestamp": datetime.now(),
                    "status": "PENDING",
                }

                # Log
                self._log_order(
                    action="PLACE_ORDER",
                    order_params=order_params,
                    response=response,
                    latency_ms=latency_ms,
                    success=True,
                )

                # Notify
                self.telegram_bot.send_message(
                    f"✅ Order Placed\n"
                    f"📊 {symbol}\n"
                    f"🔢 {side} {quantity} shares\n"
                    f"💰 Price: ₹{price:,.2f}\n"
                    f"🆔 Order ID: {order_id}"
                )

                self.logger.info(
                    f"Order placed: {side} {quantity} × {symbol} @ ₹{price} "
                    f"(Order ID: {order_id}, Latency: {latency_ms:.0f}ms)"
                )

                return {
                    "success": True,
                    "order_id": order_id,
                    "message": "Order placed successfully",
                }

            else:
                # Order rejected
                error_msg = response.get("message", "Unknown error")

                # Log
                self._log_order(
                    action="PLACE_ORDER",
                    order_params=order_params,
                    response=response,
                    latency_ms=latency_ms,
                    success=False,
                    error=error_msg,
                )

                # Notify
                self.telegram_bot.send_message(
                    f"❌ Order REJECTED\n"
                    f"📊 {symbol}\n"
                    f"🔢 {side} {quantity} shares\n"
                    f"💰 Price: ₹{price:,.2f}\n"
                    f"⚠️ Error: {error_msg}"
                )

                self.logger.error(f"Order rejected: {error_msg}")

                return {
                    "success": False,
                    "order_id": None,
                    "message": error_msg,
                }

        except Exception as e:
            self.logger.error(f"Order placement failed: {e}")

            # Notify
            self.telegram_bot.send_message(
                f"❌ Order Placement FAILED\n"
                f"📊 {symbol}\n"
                f"Error: {str(e)}"
            )

            raise

    def _validate_order(
        self, symbol: str, side: str, quantity: int, price: float, order_type: str
    ):
        """
        Validate order parameters

        Raises:
            OrderValidationError: If validation fails
        """
        errors = []

        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            errors.append("Invalid symbol")

        # Validate side
        if side not in ["BUY", "SELL"]:
            errors.append(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")

        # Validate quantity
        if quantity <= 0:
            errors.append(f"Invalid quantity: {quantity}. Must be > 0")

        # Validate price
        if price <= 0:
            errors.append(f"Invalid price: {price}. Must be > 0")

        # Validate order type
        if order_type not in ["LIMIT", "MARKET"]:
            errors.append(f"Invalid order type: {order_type}")

        # MARKET orders require special approval (too risky)
        if order_type == "MARKET":
            self.logger.warning("MARKET order requested. This is HIGH RISK.")
            # Optionally reject MARKET orders
            # errors.append("MARKET orders not allowed")

        if errors:
            error_msg = "; ".join(errors)
            self.logger.error(f"Order validation failed: {error_msg}")
            raise OrderValidationError(error_msg)

    def _check_rate_limit(self):
        """
        Check and enforce rate limit

        Raises:
            RateLimitExceededError: If rate limit exceeded
        """
        now = time.time()

        # Remove timestamps older than 1 second
        while self.order_timestamps and now - self.order_timestamps[0] > 1.0:
            self.order_timestamps.popleft()

        # Check limit
        if len(self.order_timestamps) >= self.max_orders_per_second:
            # Wait for oldest timestamp to age out
            wait_time = 1.0 - (now - self.order_timestamps[0])

            if wait_time > 0:
                self.logger.warning(
                    f"Rate limit: {len(self.order_timestamps)}/{self.max_orders_per_second}. "
                    f"Waiting {wait_time:.3f}s"
                )
                time.sleep(wait_time)

        # Record this order
        self.order_timestamps.append(time.time())

    def _get_symbol_token(self, symbol: str) -> str:
        """
        Get Angel One symbol token for a symbol

        Note: In production, this should query Angel One's master symbol list.
        For now, return placeholder.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE-EQ")

        Returns:
            Symbol token (e.g., "2885")
        """
        # TODO: Implement actual symbol token lookup
        # This requires downloading and parsing Angel One's symbol master file

        # Placeholder mapping (for testing only)
        symbol_tokens = {
            "RELIANCE-EQ": "2885",
            "TCS-EQ": "11536",
            "INFY-EQ": "1594",
            "HDFCBANK-EQ": "1333",
        }

        token = symbol_tokens.get(symbol)

        if not token:
            self.logger.warning(
                f"Symbol token not found for {symbol}. Using placeholder."
            )
            return "0"  # Placeholder

        return token

    def _log_order(
        self,
        action: str,
        order_params: dict,
        response: dict,
        latency_ms: float,
        success: bool,
        error: Optional[str] = None,
    ):
        """Log order transaction to audit trail"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "order_params": order_params,
            "response": response,
            "latency_ms": latency_ms,
            "success": success,
            "error": error,
        }

        # Log to file (or database)
        self.logger.info(f"AUDIT: {log_entry}")

        # TODO: Store in database for long-term audit trail

    def activate_kill_switch(self, reason: str):
        """Activate kill switch to halt all trading"""

        self.kill_switch_active = True

        self.logger.critical(f"🛑 KILL SWITCH ACTIVATED: {reason}")

        self.telegram_bot.send_message(
            f"🛑 KILL SWITCH ACTIVATED\n"
            f"Reason: {reason}\n"
            f"All trading HALTED"
        )

    def deactivate_kill_switch(self):
        """Deactivate kill switch"""

        self.kill_switch_active = False

        self.logger.info("✅ Kill switch deactivated. Trading resumed.")

        self.telegram_bot.send_message(
            "✅ Kill switch deactivated\n"
            "Trading resumed"
        )

    def get_order_status(self, order_id: str) -> Dict:
        """
        Query order status from Angel One

        Args:
            order_id: Order ID

        Returns:
            Order status dict
        """
        self._check_authentication()

        order_status = self.smart_api.orderBook()

        # Find order in order book
        if order_status["status"]:
            for order in order_status["data"]:
                if order["orderid"] == order_id:
                    return order

        return {}

    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel pending order

        Args:
            order_id: Order ID to cancel

        Returns:
            Cancellation result
        """
        self._check_authentication()

        cancel_params = {
            "variety": "NORMAL",
            "orderid": order_id,
        }

        response = self.smart_api.cancelOrder(cancel_params)

        self.logger.info(f"Order cancelled: {order_id}")

        return response
```

---

## API Contracts

### Input: Place Order

```python
executor = AngelOneExecutor(
    api_key="your_api_key",
    client_id="your_client_id",
    password="your_password",
    totp_secret="your_totp_secret",
    telegram_bot=telegram,
)

result = executor.place_order(
    symbol="RELIANCE-EQ",
    side="BUY",
    quantity=10,
    price=2500.00,
    order_type="LIMIT",
    product_type="DELIVERY",
)
```

### Output: Order Result

```python
{
    "success": True,
    "order_id": "241119000012345",
    "message": "Order placed successfully"
}
```

---

## Business Rules

### BR-1: Kill Switch

**Rule**: Manual override to halt ALL trading

**Trigger**:
- Manual activation by operator
- System error detected
- Unexpected behavior
- Max drawdown breached

**Implementation**:
```python
if kill_switch_active:
    raise KillSwitchActiveError("Trading halted")
```

### BR-2: Order Validation

**Rule**: Validate ALL parameters before API call

**Checks**:
1. Symbol exists
2. Price > 0
3. Quantity > 0
4. Side in [BUY, SELL]
5. Order type in [LIMIT, MARKET]

### BR-3: Rate Limiting

**Rule**: Max 10 orders per second

**Implementation**: Token bucket algorithm

### BR-4: Audit Trail

**Rule**: Log EVERY API call

**Data logged**:
- Timestamp
- Action
- Parameters
- Response
- Latency
- Success/failure

### BR-5: Authentication

**Rule**: Re-authenticate if token expired

**Token lifetime**: 24 hours

---

## Test Cases

### TC-001: Successful Order Placement

**Test Code**:
```python
def test_place_order_success(mocker):
    executor = AngelOneExecutor(...)

    # Mock API response
    mocker.patch.object(
        executor.smart_api,
        "placeOrder",
        return_value={
            "status": True,
            "data": {"orderid": "123456"},
        },
    )

    result = executor.place_order(
        symbol="RELIANCE-EQ",
        side="BUY",
        quantity=10,
        price=2500,
    )

    assert result["success"] is True
    assert result["order_id"] == "123456"
```

### TC-002: Order Validation Failure

**Test Code**:
```python
def test_order_validation_fails():
    executor = AngelOneExecutor(...)

    with pytest.raises(OrderValidationError):
        executor.place_order(
            symbol="RELIANCE-EQ",
            side="INVALID",  # Invalid side
            quantity=10,
            price=2500,
        )
```

### TC-003: Kill Switch Active

**Test Code**:
```python
def test_kill_switch_active():
    executor = AngelOneExecutor(...)

    executor.activate_kill_switch("Test")

    with pytest.raises(KillSwitchActiveError):
        executor.place_order(
            symbol="RELIANCE-EQ",
            side="BUY",
            quantity=10,
            price=2500,
        )
```

### TC-004: Rate Limiting

**Test Code**:
```python
def test_rate_limiting():
    executor = AngelOneExecutor(max_orders_per_second=2)

    # Place 3 orders (should delay 3rd)
    start = time.time()

    for i in range(3):
        executor.place_order(...)

    elapsed = time.time() - start

    # Should take > 1 second (due to rate limit)
    assert elapsed >= 1.0
```

---

## Edge Cases

### Edge Case 1: Network Failure

**Scenario**: API call times out

**Expected**:
- Log error
- Retry with exponential backoff (3 attempts)
- Alert via Telegram
- Return error to caller

### Edge Case 2: Token Expiry Mid-Session

**Scenario**: Token expires between orders

**Expected**:
- Detect 401 Unauthorized
- Re-authenticate automatically
- Retry original request

### Edge Case 3: Duplicate Order

**Scenario**: Same order submitted twice

**Expected**:
- Detect duplicate (symbol + side + price + quantity)
- Reject 2nd order
- Alert operator

---

## Performance Requirements

### PR-1: Order Latency

**Requirement**: Place order in < 500ms (95th percentile)

**Implementation**: Optimize API calls, use persistent connections

### PR-2: Authentication Latency

**Requirement**: Login in < 2 seconds

---

## Dependencies

### Internal Dependencies

- **Telegram Bot**: For notifications
- **Audit Logger**: For logging

### External Dependencies

- **SmartAPI Python SDK**: Angel One client library
- **pyotp**: TOTP generation

### Environment Variables

```bash
ANGEL_ONE_API_KEY=your_api_key
ANGEL_ONE_CLIENT_ID=your_client_id
ANGEL_ONE_PASSWORD=your_password
ANGEL_ONE_TOTP_SECRET=your_totp_secret
```

---

## Implementation Checklist

- [ ] Create `execution/angel_one_executor.py`
- [ ] Implement authentication
- [ ] Implement order placement
- [ ] Implement order validation
- [ ] Implement rate limiting
- [ ] Implement kill switch
- [ ] Implement audit logging
- [ ] Write 15 unit tests
- [ ] Write 5 integration tests (use testnet)
- [ ] Manual testing with₹1 test orders
- [ ] Security review
- [ ] Code review (2 reviewers minimum)
- [ ] Documentation

---

## ⚠️ PRE-LAUNCH CHECKLIST

Before placing FIRST live order:

- [ ] All tests passing (100% coverage)
- [ ] Kill switch tested and working
- [ ] Rate limiter tested
- [ ] Order validation tested
- [ ] Audit logging verified
- [ ] Telegram notifications working
- [ ] Manual test with ₹1 order successful
- [ ] Code reviewed by 2+ people
- [ ] User approval obtained
- [ ] Backup plan documented
- [ ] Emergency contacts ready

---

**Document Status**: ✅ Complete
**Review Status**: CRITICAL - Requires Multiple Approvals
**Next**: STORY-003 (Soft Launch with ₹25K)
