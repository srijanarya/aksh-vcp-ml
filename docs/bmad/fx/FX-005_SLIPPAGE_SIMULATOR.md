# FX-005: Slippage Simulator

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-4 (Realistic Cost Modeling - Slippage Component)
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Specification

---

## Table of Contents

1. [Overview](#overview)
2. [User Story](#user-story)
3. [Acceptance Criteria](#acceptance-criteria)
4. [Slippage Factors](#slippage-factors)
5. [Technical Specification](#technical-specification)
6. [Business Rules](#business-rules)
7. [Test Cases](#test-cases)
8. [Calibration Data](#calibration-data)

---

## Overview

### What is Slippage?

**Slippage**: The difference between expected execution price and actual fill price.

**Example**:
- Signal generated at: ₹2,500
- Order placed (market order)
- Actual fill: ₹2,503
- **Slippage: ₹3 (0.12%)**

### Why Slippage Matters

**Unrealistic Backtest**:
- Entry: ₹2,500 (signal price)
- Exit: ₹2,625 (signal price)
- Profit: ₹125 per share

**Realistic Backtest**:
- Entry: ₹2,503 (with slippage)
- Exit: ₹2,622 (with slippage)
- Profit: ₹119 per share
- **₹6 less per share** (4.8% of profit)

**Over 100 trades**:
- Unrealistic: ₹12,500 profit
- Realistic: ₹11,900 profit
- **₹600 difference** (4.8%)

Combined with transaction costs, this can completely erase profitability.

---

## User Story

**As** the Portfolio Manager
**I want** slippage calculated realistically
**So that** backtest results match live trading

### Requirements

1. Slippage depends on liquidity (high for small-caps, low for Nifty 50)
2. Slippage depends on order size (higher for large orders)
3. Slippage depends on volatility (higher during volatile periods)
4. Slippage depends on time of day (higher at market open)
5. Slippage different for market vs limit orders

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Calculate slippage based on stock liquidity (avg daily volume)
✅ **AC-2**: Calculate slippage based on order size (% of ADV)
✅ **AC-3**: Calculate slippage based on volatility (VIX, ATR)
✅ **AC-4**: Calculate slippage based on time of day
✅ **AC-5**: Different slippage for market vs limit orders
✅ **AC-6**: Calibrate against real trade data (10+ real trades)
✅ **AC-7**: Apply slippage to both entry and exit

### Should Have

⭕ **AC-8**: Bid-ask spread integration
⭕ **AC-9**: Impact cost for large orders
⭕ **AC-10**: Slippage distribution (not just average)

---

## Slippage Factors

### Factor 1: Stock Liquidity

**Measure**: Average Daily Volume (ADV) in last 20 days

| Liquidity Tier | ADV (shares) | Base Slippage |
|----------------|--------------|---------------|
| Very High | > 10M | 0.01% |
| High | 1M - 10M | 0.02% |
| Medium | 100K - 1M | 0.05% |
| Low | 10K - 100K | 0.10% |
| Very Low | < 10K | 0.30% |

**Examples**:
- Reliance (ADV: 15M) → 0.01%
- Nifty 50 stocks → 0.01-0.02%
- Mid-caps → 0.05-0.10%
- Small-caps → 0.10-0.30%

---

### Factor 2: Order Size

**Measure**: Order value as % of Average Daily Turnover (ADT)

| Order Size | % of ADT | Slippage Multiplier |
|------------|----------|---------------------|
| Tiny | < 0.1% | 1.0× |
| Small | 0.1% - 0.5% | 1.2× |
| Medium | 0.5% - 1.0% | 1.5× |
| Large | 1.0% - 2.0% | 2.0× |
| Very Large | > 2.0% | 3.0× |

**Example**:
- Stock ADT: ₹50 Crore
- Order: ₹10 Lakh (0.2% of ADT)
- Multiplier: 1.2×
- If base slippage = 0.02%, final = 0.02% × 1.2 = 0.024%

---

### Factor 3: Volatility

**Measure**: VIX (Nifty volatility index) or stock ATR

| Volatility Level | VIX Range | Slippage Multiplier |
|------------------|-----------|---------------------|
| Low | < 12 | 1.0× |
| Normal | 12 - 18 | 1.2× |
| Elevated | 18 - 25 | 1.5× |
| High | 25 - 35 | 2.0× |
| Extreme | > 35 | 3.0× |

**Example**:
- VIX = 22 (Elevated)
- Base slippage = 0.02%
- Final = 0.02% × 1.5 = 0.03%

---

### Factor 4: Time of Day

**Measure**: Time of order placement

| Time Period | Description | Slippage Multiplier |
|-------------|-------------|---------------------|
| 9:15 - 9:30 | Market open (volatile) | 2.0× |
| 9:30 - 10:00 | Early morning | 1.5× |
| 10:00 - 15:00 | Mid-day (stable) | 1.0× |
| 15:00 - 15:30 | Close (volatile) | 1.5× |

**Example**:
- Order at 9:20 AM
- Base slippage = 0.02%
- Final = 0.02% × 2.0 = 0.04%

---

### Factor 5: Order Type

| Order Type | Slippage |
|------------|----------|
| Market Order | Full slippage (as calculated) |
| Limit Order | 0% slippage (by definition) |
| Stop-Loss Market | 1.5× slippage (executes in unfavorable conditions) |

---

## Combined Slippage Formula

```
Final Slippage = Base Slippage (liquidity)
                 × Size Multiplier
                 × Volatility Multiplier
                 × Time Multiplier
                 × Order Type Multiplier
```

### Example Calculation

**Stock**: Mid-cap (ADV: 500K shares)
**Order**: ₹20 Lakh (0.8% of ADT)
**VIX**: 20 (Elevated)
**Time**: 9:25 AM (Market open)
**Order Type**: Market

**Calculation**:
1. Base slippage (Medium liquidity): 0.05%
2. Size multiplier (0.8% of ADT): 1.5×
3. Volatility multiplier (VIX 20): 1.5×
4. Time multiplier (9:25 AM): 2.0×
5. Order type multiplier (Market): 1.0×

**Final Slippage**:
```
0.05% × 1.5 × 1.5 × 2.0 × 1.0 = 0.225%
```

**Impact**:
- Order value: ₹20,00,000
- Slippage: ₹20,00,000 × 0.00225 = **₹4,500**

---

## Technical Specification

### Class: `SlippageSimulator`

```python
# execution/slippage_simulator.py
from dataclasses import dataclass
from datetime import time
from typing import Literal
import logging
import yfinance as yf

@dataclass
class SlippageResult:
    """Slippage calculation result"""
    base_slippage_pct: float
    size_multiplier: float
    volatility_multiplier: float
    time_multiplier: float
    order_type_multiplier: float
    final_slippage_pct: float
    slippage_amount: float  # In rupees
    adjusted_price: float  # After slippage

class SlippageSimulator:
    """
    Simulate realistic slippage for Indian markets

    Factors:
    - Stock liquidity (ADV)
    - Order size (% of ADT)
    - Volatility (VIX)
    - Time of day
    - Order type (market/limit)
    """

    def __init__(self, calibration_data: dict = None):
        """
        Initialize slippage simulator

        Args:
            calibration_data: Optional dict of empirical slippage data
        """
        self.logger = logging.getLogger(__name__)
        self.calibration_data = calibration_data or {}

        # Liquidity tiers (ADV in shares)
        self.liquidity_tiers = {
            "very_high": (10_000_000, float('inf'), 0.0001),  # 0.01%
            "high": (1_000_000, 10_000_000, 0.0002),  # 0.02%
            "medium": (100_000, 1_000_000, 0.0005),  # 0.05%
            "low": (10_000, 100_000, 0.001),  # 0.10%
            "very_low": (0, 10_000, 0.003),  # 0.30%
        }

        # Order size multipliers (% of ADT)
        self.size_multipliers = [
            (0, 0.001, 1.0),  # < 0.1% of ADT
            (0.001, 0.005, 1.2),  # 0.1-0.5%
            (0.005, 0.010, 1.5),  # 0.5-1.0%
            (0.010, 0.020, 2.0),  # 1.0-2.0%
            (0.020, float('inf'), 3.0),  # > 2.0%
        ]

        # Volatility multipliers (VIX)
        self.volatility_multipliers = [
            (0, 12, 1.0),  # Low
            (12, 18, 1.2),  # Normal
            (18, 25, 1.5),  # Elevated
            (25, 35, 2.0),  # High
            (35, float('inf'), 3.0),  # Extreme
        ]

        # Time of day multipliers
        self.time_multipliers = [
            (time(9, 15), time(9, 30), 2.0),  # Market open
            (time(9, 30), time(10, 0), 1.5),  # Early morning
            (time(10, 0), time(15, 0), 1.0),  # Mid-day
            (time(15, 0), time(15, 30), 1.5),  # Close
        ]

        # Order type multipliers
        self.order_type_multipliers = {
            "MARKET": 1.0,
            "LIMIT": 0.0,  # No slippage for limit orders
            "STOP_LOSS_MARKET": 1.5,
        }

    def calculate_slippage(
        self,
        symbol: str,
        side: Literal["BUY", "SELL"],
        order_value: float,
        signal_price: float,
        order_type: str = "MARKET",
        order_time: time = None,
        vix: float = None,
    ) -> SlippageResult:
        """
        Calculate slippage for an order

        Args:
            symbol: Stock symbol (e.g., "RELIANCE.NS")
            side: 'BUY' or 'SELL'
            order_value: Order value in ₹
            signal_price: Expected price (from signal)
            order_type: 'MARKET', 'LIMIT', 'STOP_LOSS_MARKET'
            order_time: Time of order (default: 10 AM)
            vix: Current VIX (default: fetch from market)

        Returns:
            SlippageResult object
        """
        # Step 1: Get base slippage from liquidity
        base_slippage_pct = self._get_base_slippage(symbol)

        # Step 2: Get size multiplier
        size_multiplier = self._get_size_multiplier(symbol, order_value)

        # Step 3: Get volatility multiplier
        if vix is None:
            vix = self._get_current_vix()
        volatility_multiplier = self._get_volatility_multiplier(vix)

        # Step 4: Get time multiplier
        if order_time is None:
            order_time = time(10, 0)  # Default: 10 AM
        time_multiplier = self._get_time_multiplier(order_time)

        # Step 5: Get order type multiplier
        order_type_multiplier = self.order_type_multipliers.get(
            order_type, 1.0
        )

        # Step 6: Calculate final slippage
        final_slippage_pct = (
            base_slippage_pct *
            size_multiplier *
            volatility_multiplier *
            time_multiplier *
            order_type_multiplier
        )

        # Step 7: Calculate slippage amount and adjusted price
        slippage_amount = order_value * final_slippage_pct

        if side == "BUY":
            # Buy at higher price
            adjusted_price = signal_price * (1 + final_slippage_pct)
        else:
            # Sell at lower price
            adjusted_price = signal_price * (1 - final_slippage_pct)

        self.logger.info(
            f"{symbol} {side} slippage: {final_slippage_pct*100:.4f}% "
            f"(₹{slippage_amount:.2f})"
        )

        return SlippageResult(
            base_slippage_pct=base_slippage_pct,
            size_multiplier=size_multiplier,
            volatility_multiplier=volatility_multiplier,
            time_multiplier=time_multiplier,
            order_type_multiplier=order_type_multiplier,
            final_slippage_pct=final_slippage_pct,
            slippage_amount=slippage_amount,
            adjusted_price=adjusted_price,
        )

    def _get_base_slippage(self, symbol: str) -> float:
        """Get base slippage from liquidity tier"""
        # Check if we have calibration data for this symbol
        if symbol in self.calibration_data:
            return self.calibration_data[symbol]["base_slippage"]

        # Otherwise, calculate from ADV
        adv = self._get_average_daily_volume(symbol)

        for tier_name, (min_adv, max_adv, slippage) in self.liquidity_tiers.items():
            if min_adv <= adv < max_adv:
                self.logger.debug(
                    f"{symbol} ADV: {adv:,.0f}, Tier: {tier_name}, "
                    f"Base slippage: {slippage*100:.2f}%"
                )
                return slippage

        # Default: Very low liquidity
        return 0.003

    def _get_size_multiplier(self, symbol: str, order_value: float) -> float:
        """Get multiplier based on order size vs ADT"""
        adt = self._get_average_daily_turnover(symbol)

        if adt == 0:
            return 1.0  # Can't calculate, use default

        order_pct_of_adt = order_value / adt

        for min_pct, max_pct, multiplier in self.size_multipliers:
            if min_pct <= order_pct_of_adt < max_pct:
                self.logger.debug(
                    f"Order {order_pct_of_adt*100:.2f}% of ADT, "
                    f"Size multiplier: {multiplier}×"
                )
                return multiplier

        # Very large order
        return 3.0

    def _get_volatility_multiplier(self, vix: float) -> float:
        """Get multiplier based on VIX"""
        for min_vix, max_vix, multiplier in self.volatility_multipliers:
            if min_vix <= vix < max_vix:
                self.logger.debug(
                    f"VIX: {vix:.1f}, Volatility multiplier: {multiplier}×"
                )
                return multiplier

        # Extreme volatility
        return 3.0

    def _get_time_multiplier(self, order_time: time) -> float:
        """Get multiplier based on time of day"""
        for start_time, end_time, multiplier in self.time_multipliers:
            if start_time <= order_time < end_time:
                self.logger.debug(
                    f"Time: {order_time}, Time multiplier: {multiplier}×"
                )
                return multiplier

        # Default (mid-day)
        return 1.0

    def _get_average_daily_volume(self, symbol: str) -> float:
        """Get average daily volume (20 days)"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            adv = hist['Volume'].tail(20).mean()
            return adv
        except Exception as e:
            self.logger.error(f"Error fetching ADV for {symbol}: {e}")
            return 100_000  # Conservative default

    def _get_average_daily_turnover(self, symbol: str) -> float:
        """Get average daily turnover (volume × price)"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            hist['Turnover'] = hist['Volume'] * hist['Close']
            adt = hist['Turnover'].tail(20).mean()
            return adt
        except Exception as e:
            self.logger.error(f"Error fetching ADT for {symbol}: {e}")
            return 10_000_000  # Conservative default (₹1 Cr)

    def _get_current_vix(self) -> float:
        """Get current VIX (India VIX)"""
        try:
            # Fetch India VIX
            vix_ticker = yf.Ticker("^INDIAVIX")
            vix = vix_ticker.history(period="1d")['Close'].iloc[-1]
            return vix
        except Exception as e:
            self.logger.error(f"Error fetching VIX: {e}")
            return 15.0  # Default: Normal volatility
```

---

## Business Rules

### BR-1: Slippage Direction

**BUY**: Slippage increases execution price (buy at higher price)
**SELL**: Slippage decreases execution price (sell at lower price)

**Implementation**:
```python
if side == "BUY":
    adjusted_price = signal_price * (1 + slippage_pct)
else:
    adjusted_price = signal_price * (1 - slippage_pct)
```

### BR-2: Limit Orders

**Rule**: Limit orders have ZERO slippage (by definition)

**Rationale**: Limit orders only execute at specified price or better

**Exception**: May not get filled (not modeled in simulator)

### BR-3: Stop-Loss Slippage

**Rule**: Stop-loss market orders have 1.5× slippage

**Rationale**: Execute during unfavorable conditions (price moving against you)

### BR-4: Maximum Slippage Cap

**Rule**: Cap slippage at 1% (safety)

**Rationale**: If slippage > 1%, likely a data error or extreme event

**Implementation**:
```python
final_slippage_pct = min(final_slippage_pct, 0.01)
```

---

## Test Cases

### TC-001: High Liquidity Stock (Reliance)

```python
def test_reliance_low_slippage():
    simulator = SlippageSimulator()

    result = simulator.calculate_slippage(
        symbol="RELIANCE.NS",
        side="BUY",
        order_value=100000,
        signal_price=2500,
        order_type="MARKET",
        order_time=time(11, 0),  # Mid-day
        vix=15,  # Normal volatility
    )

    # Reliance is very liquid → Low base slippage
    assert result.base_slippage_pct <= 0.0002  # ≤ 0.02%

    # Small order, normal conditions
    assert result.final_slippage_pct <= 0.0005  # ≤ 0.05%

    # Adjusted price should be slightly higher (BUY)
    assert 2500 < result.adjusted_price < 2502
```

### TC-002: Mid-Cap Stock, Volatile Market

```python
def test_midcap_high_slippage():
    simulator = SlippageSimulator()

    result = simulator.calculate_slippage(
        symbol="MIDCAP.NS",  # Assume medium liquidity
        side="SELL",
        order_value=500000,  # Larger order
        signal_price=1000,
        order_type="MARKET",
        order_time=time(9, 20),  # Market open
        vix=28,  # High volatility
    )

    # Medium liquidity → Higher base slippage
    assert result.base_slippage_pct >= 0.0005  # ≥ 0.05%

    # High volatility + market open → High multipliers
    assert result.volatility_multiplier >= 2.0
    assert result.time_multiplier >= 2.0

    # Final slippage should be significant
    assert result.final_slippage_pct >= 0.002  # ≥ 0.2%
```

### TC-003: Limit Order (Zero Slippage)

```python
def test_limit_order_zero_slippage():
    simulator = SlippageSimulator()

    result = simulator.calculate_slippage(
        symbol="RELIANCE.NS",
        side="BUY",
        order_value=100000,
        signal_price=2500,
        order_type="LIMIT",
    )

    # Limit order → Zero slippage
    assert result.final_slippage_pct == 0.0
    assert result.adjusted_price == 2500  # No change
```

### TC-004: Stop-Loss Order (High Slippage)

```python
def test_stop_loss_high_slippage():
    simulator = SlippageSimulator()

    result = simulator.calculate_slippage(
        symbol="RELIANCE.NS",
        side="SELL",
        order_value=100000,
        signal_price=2400,  # Stop-loss hit
        order_type="STOP_LOSS_MARKET",
        vix=20,
    )

    # Stop-loss → 1.5× multiplier
    assert result.order_type_multiplier == 1.5

    # Should have higher slippage than regular market order
    assert result.final_slippage_pct > 0.0002
```

### TC-005: Large Order (Impact Cost)

```python
def test_large_order_impact():
    simulator = SlippageSimulator()

    # Order = 2% of ADT (very large)
    result = simulator.calculate_slippage(
        symbol="SMALLCAP.NS",
        side="BUY",
        order_value=10000000,  # ₹1 Cr order
        signal_price=500,
    )

    # Large order → High size multiplier
    assert result.size_multiplier >= 2.0

    # Total slippage should be significant
    assert result.final_slippage_pct >= 0.005  # ≥ 0.5%
```

---

## Calibration Data

### Real Trade Examples

Use these to calibrate the simulator:

```python
calibration_data = {
    "RELIANCE.NS": {
        "base_slippage": 0.00015,  # 0.015% (empirical)
        "avg_slippage_market_open": 0.0004,  # 0.04%
        "avg_slippage_midday": 0.0002,  # 0.02%
    },
    "TCS.NS": {
        "base_slippage": 0.00012,
        "avg_slippage_market_open": 0.0003,
        "avg_slippage_midday": 0.00015,
    },
    # Add more as you collect real trade data
}

simulator = SlippageSimulator(calibration_data=calibration_data)
```

### Validation Process

1. **Collect 10+ real trades** with actual fill prices
2. **Compare simulator predictions to actual slippage**
3. **Adjust base slippage rates if needed**
4. **Re-validate on new trades**

**Target Accuracy**: Predicted slippage within ±20% of actual

---

## Integration with Backtest

```python
# backtesting/backtest_engine.py
from execution.slippage_simulator import SlippageSimulator

class BacktestEngine:
    def __init__(self):
        self.slippage_simulator = SlippageSimulator()

    def execute_trade(self, signal):
        """Execute trade with realistic slippage"""

        # Calculate slippage
        slippage_result = self.slippage_simulator.calculate_slippage(
            symbol=signal["symbol"],
            side=signal["side"],
            order_value=signal["position_value"],
            signal_price=signal["entry_price"],
            order_type="MARKET",
            order_time=signal["timestamp"].time(),
        )

        # Use adjusted price (with slippage)
        actual_entry_price = slippage_result.adjusted_price

        # Record trade
        trade = {
            "symbol": signal["symbol"],
            "entry_price": actual_entry_price,  # After slippage
            "slippage": slippage_result.slippage_amount,
            # ...
        }

        return trade
```

---

## Performance Requirements

### PR-1: Calculation Speed

**Requirement**: < 50ms per calculation (includes API calls)

**Test**:
```python
def test_slippage_calculation_speed():
    simulator = SlippageSimulator()

    start = time.time()
    result = simulator.calculate_slippage(
        symbol="RELIANCE.NS",
        side="BUY",
        order_value=100000,
        signal_price=2500,
    )
    end = time.time()

    latency = (end - start) * 1000  # ms
    assert latency < 50  # < 50ms
```

---

## Implementation Checklist

- [ ] Create `execution/slippage_simulator.py`
- [ ] Write 10 unit tests
- [ ] Collect 10+ real trade fill prices
- [ ] Calibrate base slippage rates
- [ ] Validate predictions vs actual (±20%)
- [ ] Integrate with backtest engine
- [ ] Integrate with paper trading
- [ ] Document calibration process
- [ ] Add logging for debugging
- [ ] Performance test (<50ms)

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: FX-007 (Regime Detector)
