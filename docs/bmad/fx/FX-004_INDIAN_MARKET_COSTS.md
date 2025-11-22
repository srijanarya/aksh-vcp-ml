# FX-004: Indian Market Cost Calculator

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-4 (Realistic Cost Modeling)
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Specification

---

## Table of Contents

1. [Overview](#overview)
2. [User Story](#user-story)
3. [Acceptance Criteria](#acceptance-criteria)
4. [Cost Components](#cost-components)
5. [Technical Specification](#technical-specification)
6. [API Contracts](#api-contracts)
7. [Business Rules](#business-rules)
8. [Test Cases](#test-cases)
9. [Edge Cases](#edge-cases)
10. [Performance Requirements](#performance-requirements)

---

## Overview

### Purpose

Calculate ALL transaction costs for Indian equity and F&O trades with 100% accuracy. Unrealistic backtesting is the #1 reason trading systems fail in production.

### User Requirement

**User said**: *"Our paper testing system and our back testing system should be robust enough to be able to calculate all the brokerage and slippages accurately."*

This is NON-NEGOTIABLE. Every rupee of cost must be accounted for.

### Why This Matters

**Example: ₹1,00,000 Trade**

**Optimistic Backtest** (No costs):
- Entry: ₹1,00,000
- Exit: ₹1,05,000 (+5%)
- Profit: ₹5,000 ✅

**Realistic Backtest** (All costs):
- Entry: ₹1,00,000
- Buy costs: ₹42
- Exit: ₹1,05,000
- Sell costs: ₹128
- **Net Profit: ₹4,830** (₹170 less)

**Over 100 trades**:
- Optimistic: ₹5,00,000 profit
- Realistic: ₹4,83,000 profit
- **Difference: ₹17,000** (3.4% of total)

This can mean the difference between a profitable system and a losing one.

---

## User Story

**As** the Portfolio Manager
**I want** all transaction costs calculated accurately
**So that** backtesting matches real trading results

### Success Criteria

1. Backtest PnL matches paper trading PnL (±2%)
2. Paper trading PnL matches live trading PnL (±2%)
3. All 6 cost components accounted for
4. Costs calculated identically in backtest, paper, and live
5. Zero hidden costs discovered post-launch

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Calculate brokerage (min of ₹20 or 0.03%)
✅ **AC-2**: Calculate STT (0.1% on sell side for equity)
✅ **AC-3**: Calculate GST (18% on brokerage)
✅ **AC-4**: Calculate stamp duty (0.015% on buy side)
✅ **AC-5**: Calculate exchange charges (~0.00325% for NSE)
✅ **AC-6**: Calculate SEBI turnover fees (0.0001%)
✅ **AC-7**: Different costs for equity vs F&O
✅ **AC-8**: Round-trip cost calculation (BUY + SELL)
✅ **AC-9**: Cost as percentage of order value
✅ **AC-10**: Validate against real brokerage statements

### Should Have

⭕ **AC-11**: DP charges for delivery trades (₹15.93 per sell)
⭕ **AC-12**: Intraday vs delivery cost differences
⭕ **AC-13**: Cost breakdown export (CSV)

### Nice to Have

🔵 **AC-14**: Visual cost breakdown chart
🔵 **AC-15**: Compare costs across brokers

---

## Cost Components

### 1. Brokerage

**Formula**: `min(₹20 per order, 0.03% of order value)`

**Example**:
- Order: ₹1,00,000
- 0.03% = ₹30
- min(₹20, ₹30) = **₹20**

**Example 2**:
- Order: ₹50,000
- 0.03% = ₹15
- min(₹20, ₹15) = **₹15**

**Applies to**: Every order (BUY and SELL)

---

### 2. STT (Securities Transaction Tax)

**Formula**:
- Equity Delivery: **0.1% on SELL side only**
- Equity Intraday: 0.025% on BOTH sides
- F&O: 0.05% on SELL side (futures), 0.05% on both sides (options)

**Example (Equity Delivery)**:
- Sell: ₹1,05,000
- STT: ₹1,05,000 × 0.001 = **₹105**

**Example (Equity Intraday)**:
- Buy: ₹1,00,000 → STT = ₹1,00,000 × 0.00025 = ₹25
- Sell: ₹1,05,000 → STT = ₹1,05,000 × 0.00025 = ₹26.25
- **Total STT: ₹51.25**

**Applies to**: Mandated by government

---

### 3. GST (Goods and Services Tax)

**Formula**: **18% on (Brokerage + Exchange Charges + SEBI fees)**

**Example**:
- Brokerage: ₹20
- Exchange charges: ₹3.25
- SEBI fees: ₹0.10
- Taxable amount: ₹20 + ₹3.25 + ₹0.10 = ₹23.35
- GST: ₹23.35 × 0.18 = **₹4.20**

**Applies to**: All charges except STT and stamp duty

---

### 4. Stamp Duty

**Formula**: **0.015% on BUY side** (0.003% for sell, but most brokers charge on buy only)

**Example**:
- Buy: ₹1,00,000
- Stamp duty: ₹1,00,000 × 0.00015 = **₹15**

**Applies to**: Buy orders only (state government tax)

---

### 5. Exchange Charges

**Formula**:
- NSE Equity: **0.00325%** of turnover
- BSE Equity: 0.00275% of turnover
- F&O: Varies by instrument

**Example (NSE)**:
- Order: ₹1,00,000
- Exchange charges: ₹1,00,000 × 0.0000325 = **₹3.25**

**Applies to**: Every trade

---

### 6. SEBI Turnover Fees

**Formula**: **0.0001%** of turnover (₹10 per crore)

**Example**:
- Order: ₹1,00,000
- SEBI fees: ₹1,00,000 × 0.000001 = **₹0.10**

**Applies to**: Every trade

---

## Total Cost Examples

### Example 1: ₹1,00,000 Equity Delivery BUY

| Component | Calculation | Amount |
|-----------|-------------|--------|
| Brokerage | min(₹20, 0.03% of 100k) | ₹20.00 |
| STT | ₹0 (buy side) | ₹0.00 |
| Exchange | 0.00325% of 100k | ₹3.25 |
| SEBI fees | 0.0001% of 100k | ₹0.10 |
| Stamp duty | 0.015% of 100k | ₹15.00 |
| GST | 18% of (20 + 3.25 + 0.10) | ₹4.20 |
| **TOTAL** | | **₹42.55** |

**As % of order**: 0.043%

---

### Example 2: ₹1,05,000 Equity Delivery SELL

| Component | Calculation | Amount |
|-----------|-------------|--------|
| Brokerage | min(₹20, 0.03% of 105k) | ₹20.00 |
| STT | 0.1% of 105k | ₹105.00 |
| Exchange | 0.00325% of 105k | ₹3.41 |
| SEBI fees | 0.0001% of 105k | ₹0.11 |
| Stamp duty | ₹0 (sell side) | ₹0.00 |
| GST | 18% of (20 + 3.41 + 0.11) | ₹4.23 |
| **TOTAL** | | **₹132.75** |

**As % of order**: 0.126%

---

### Example 3: Round-Trip (BUY ₹1L + SELL ₹1.05L)

| Side | Cost |
|------|------|
| BUY (₹1,00,000) | ₹42.55 |
| SELL (₹1,05,000) | ₹132.75 |
| **TOTAL COST** | **₹175.30** |

**Gross Profit**: ₹5,000
**Net Profit**: ₹5,000 - ₹175.30 = **₹4,824.70**
**Cost as % of profit**: 3.5%

---

## Technical Specification

### Class: `CostCalculator`

```python
# execution/cost_calculator.py
from dataclasses import dataclass
from typing import Literal
import logging

@dataclass
class CostBreakdown:
    """Detailed cost breakdown"""
    brokerage: float
    stt: float
    exchange_charges: float
    sebi_fees: float
    stamp_duty: float
    gst: float
    dp_charges: float = 0.0  # Demat charges

    @property
    def total(self) -> float:
        """Total cost"""
        return (
            self.brokerage +
            self.stt +
            self.exchange_charges +
            self.sebi_fees +
            self.stamp_duty +
            self.gst +
            self.dp_charges
        )

    def as_percentage(self, order_value: float) -> float:
        """Cost as percentage of order value"""
        return (self.total / order_value) * 100


class CostCalculator:
    """
    Calculate all Indian market transaction costs

    Supports:
    - Equity delivery
    - Equity intraday
    - Futures
    - Options

    All rates as of November 2025
    """

    def __init__(self, broker: str = "zerodha"):
        """
        Initialize cost calculator

        Args:
            broker: Broker name for broker-specific rates
        """
        self.broker = broker
        self.logger = logging.getLogger(__name__)

        # Brokerage rates
        self.brokerage_flat = 20  # ₹20 per order
        self.brokerage_pct = 0.0003  # 0.03%

        # STT rates
        self.stt_equity_delivery_sell = 0.001  # 0.1% on sell
        self.stt_equity_intraday = 0.00025  # 0.025% both sides
        self.stt_futures_sell = 0.0005  # 0.05% on sell
        self.stt_options = 0.0005  # 0.05% on sell (premium)

        # Other charges
        self.gst_rate = 0.18  # 18%
        self.stamp_duty_buy = 0.00015  # 0.015% on buy
        self.stamp_duty_sell = 0.00003  # 0.003% on sell (usually not charged)
        self.nse_exchange_rate = 0.0000325  # 0.00325%
        self.bse_exchange_rate = 0.0000275  # 0.00275%
        self.sebi_rate = 0.000001  # 0.0001%
        self.dp_charges = 15.93  # DP charges per sell (delivery)

    def calculate_equity_delivery_costs(
        self,
        side: Literal["BUY", "SELL"],
        order_value: float,
        exchange: Literal["NSE", "BSE"] = "NSE",
    ) -> CostBreakdown:
        """
        Calculate costs for equity delivery trade

        Args:
            side: 'BUY' or 'SELL'
            order_value: Total order value in ₹
            exchange: 'NSE' or 'BSE'

        Returns:
            CostBreakdown object
        """
        # 1. Brokerage (lower of flat or percentage)
        brokerage_pct_amount = order_value * self.brokerage_pct
        brokerage = min(self.brokerage_flat, brokerage_pct_amount)

        # 2. STT (only on sell)
        if side == "SELL":
            stt = order_value * self.stt_equity_delivery_sell
        else:
            stt = 0.0

        # 3. Exchange charges
        exchange_rate = (
            self.nse_exchange_rate if exchange == "NSE"
            else self.bse_exchange_rate
        )
        exchange_charges = order_value * exchange_rate

        # 4. SEBI fees
        sebi_fees = order_value * self.sebi_rate

        # 5. Stamp duty (only on buy)
        if side == "BUY":
            stamp_duty = order_value * self.stamp_duty_buy
        else:
            stamp_duty = 0.0

        # 6. DP charges (only on sell for delivery)
        dp_charges = self.dp_charges if side == "SELL" else 0.0

        # 7. GST (on brokerage + exchange + SEBI)
        taxable_amount = brokerage + exchange_charges + sebi_fees
        gst = taxable_amount * self.gst_rate

        return CostBreakdown(
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            sebi_fees=sebi_fees,
            stamp_duty=stamp_duty,
            gst=gst,
            dp_charges=dp_charges,
        )

    def calculate_equity_intraday_costs(
        self,
        side: Literal["BUY", "SELL"],
        order_value: float,
        exchange: Literal["NSE", "BSE"] = "NSE",
    ) -> CostBreakdown:
        """
        Calculate costs for equity intraday trade

        Difference from delivery:
        - STT on both sides (0.025%)
        - No DP charges
        """
        # Same as delivery except STT
        breakdown = self.calculate_equity_delivery_costs(side, order_value, exchange)

        # Overwrite STT (both sides for intraday)
        breakdown.stt = order_value * self.stt_equity_intraday

        # No DP charges for intraday
        breakdown.dp_charges = 0.0

        return breakdown

    def calculate_futures_costs(
        self,
        side: Literal["BUY", "SELL"],
        order_value: float,
    ) -> CostBreakdown:
        """
        Calculate costs for futures trade

        Brokerage: ₹20 per order (flat, not percentage)
        STT: 0.05% on sell side only
        """
        # Brokerage (flat ₹20 for F&O)
        brokerage = self.brokerage_flat

        # STT (only on sell)
        if side == "SELL":
            stt = order_value * self.stt_futures_sell
        else:
            stt = 0.0

        # Exchange charges (futures have different rates, approx 0.0019%)
        exchange_charges = order_value * 0.000019

        # SEBI fees
        sebi_fees = order_value * self.sebi_rate

        # Stamp duty (0.002% on buy for futures)
        if side == "BUY":
            stamp_duty = order_value * 0.00002
        else:
            stamp_duty = 0.0

        # GST
        taxable_amount = brokerage + exchange_charges + sebi_fees
        gst = taxable_amount * self.gst_rate

        return CostBreakdown(
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            sebi_fees=sebi_fees,
            stamp_duty=stamp_duty,
            gst=gst,
            dp_charges=0.0,
        )

    def calculate_options_costs(
        self,
        side: Literal["BUY", "SELL"],
        premium_value: float,
    ) -> CostBreakdown:
        """
        Calculate costs for options trade

        STT: 0.05% on sell side (on premium)
        Brokerage: ₹20 per order
        """
        # Similar to futures
        brokerage = self.brokerage_flat

        # STT (on premium value, sell side only)
        if side == "SELL":
            stt = premium_value * self.stt_options
        else:
            stt = 0.0

        # Exchange charges (options)
        exchange_charges = premium_value * 0.00053  # ~0.053%

        # SEBI fees
        sebi_fees = premium_value * self.sebi_rate

        # Stamp duty (0.003% on buy)
        if side == "BUY":
            stamp_duty = premium_value * 0.00003
        else:
            stamp_duty = 0.0

        # GST
        taxable_amount = brokerage + exchange_charges + sebi_fees
        gst = taxable_amount * self.gst_rate

        return CostBreakdown(
            brokerage=brokerage,
            stt=stt,
            exchange_charges=exchange_charges,
            sebi_fees=sebi_fees,
            stamp_duty=stamp_duty,
            gst=gst,
            dp_charges=0.0,
        )

    def calculate_round_trip_cost(
        self,
        instrument_type: Literal["EQUITY_DELIVERY", "EQUITY_INTRADAY", "FUTURES", "OPTIONS"],
        buy_value: float,
        sell_value: float,
        exchange: Literal["NSE", "BSE"] = "NSE",
    ) -> dict:
        """
        Calculate total cost for round-trip (BUY + SELL)

        Returns:
            {
                'buy_costs': CostBreakdown,
                'sell_costs': CostBreakdown,
                'total_cost': float,
                'cost_percentage': float,
            }
        """
        if instrument_type == "EQUITY_DELIVERY":
            buy_costs = self.calculate_equity_delivery_costs("BUY", buy_value, exchange)
            sell_costs = self.calculate_equity_delivery_costs("SELL", sell_value, exchange)
        elif instrument_type == "EQUITY_INTRADAY":
            buy_costs = self.calculate_equity_intraday_costs("BUY", buy_value, exchange)
            sell_costs = self.calculate_equity_intraday_costs("SELL", sell_value, exchange)
        elif instrument_type == "FUTURES":
            buy_costs = self.calculate_futures_costs("BUY", buy_value)
            sell_costs = self.calculate_futures_costs("SELL", sell_value)
        elif instrument_type == "OPTIONS":
            buy_costs = self.calculate_options_costs("BUY", buy_value)
            sell_costs = self.calculate_options_costs("SELL", sell_value)
        else:
            raise ValueError(f"Unknown instrument type: {instrument_type}")

        total_cost = buy_costs.total + sell_costs.total
        total_turnover = buy_value + sell_value
        cost_percentage = (total_cost / total_turnover) * 100

        return {
            "buy_costs": buy_costs,
            "sell_costs": sell_costs,
            "total_cost": total_cost,
            "cost_percentage": cost_percentage,
        }
```

---

## API Contracts

### Input: Trade Details

```python
trade = {
    "instrument_type": "EQUITY_DELIVERY",  # or EQUITY_INTRADAY, FUTURES, OPTIONS
    "side": "BUY",  # or SELL
    "order_value": 100000.0,
    "exchange": "NSE",  # or BSE
}
```

### Output: Cost Breakdown

```python
costs = CostBreakdown(
    brokerage=20.00,
    stt=0.00,
    exchange_charges=3.25,
    sebi_fees=0.10,
    stamp_duty=15.00,
    gst=4.20,
    dp_charges=0.00,
)

print(costs.total)  # 42.55
print(costs.as_percentage(100000))  # 0.043%
```

---

## Business Rules

### BR-1: Brokerage Calculation

**Rule**: Brokerage = min(₹20, 0.03% of order value)

**Exception**: F&O always ₹20 flat (no percentage)

### BR-2: STT Application

**Equity Delivery**: 0.1% on SELL only
**Equity Intraday**: 0.025% on BOTH sides
**Futures**: 0.05% on SELL only
**Options**: 0.05% on SELL only (on premium)

### BR-3: GST Taxable Amount

**GST applies to**:
- Brokerage
- Exchange charges
- SEBI fees

**GST does NOT apply to**:
- STT (government tax)
- Stamp duty (government tax)
- DP charges

### BR-4: Rounding

**Rule**: Round each component to 2 decimal places

**Total**: Sum rounded components, then round to 2 decimals

### BR-5: Zero-Cost Validation

**Rule**: If calculated cost is ₹0, log warning

**Reason**: Likely a bug in calculation

---

## Test Cases

### TC-001: ₹1,00,000 Equity Delivery BUY

```python
def test_equity_delivery_buy_100k():
    calc = CostCalculator()
    costs = calc.calculate_equity_delivery_costs("BUY", 100000, "NSE")

    assert costs.brokerage == 20.00
    assert costs.stt == 0.00  # Buy side
    assert costs.exchange_charges == pytest.approx(3.25, abs=0.01)
    assert costs.sebi_fees == pytest.approx(0.10, abs=0.01)
    assert costs.stamp_duty == pytest.approx(15.00, abs=0.01)
    assert costs.gst == pytest.approx(4.20, abs=0.10)
    assert costs.dp_charges == 0.00  # Buy side

    assert 42 <= costs.total <= 43
```

### TC-002: ₹1,05,000 Equity Delivery SELL

```python
def test_equity_delivery_sell_105k():
    calc = CostCalculator()
    costs = calc.calculate_equity_delivery_costs("SELL", 105000, "NSE")

    assert costs.brokerage == 20.00
    assert costs.stt == pytest.approx(105.00, abs=0.10)  # 0.1% of 105k
    assert costs.stamp_duty == 0.00  # Sell side
    assert costs.dp_charges == pytest.approx(15.93, abs=0.01)

    assert 132 <= costs.total <= 134
```

### TC-003: Round-Trip Cost

```python
def test_round_trip_equity_delivery():
    calc = CostCalculator()
    result = calc.calculate_round_trip_cost(
        "EQUITY_DELIVERY",
        buy_value=100000,
        sell_value=105000,
    )

    buy_cost = result["buy_costs"].total
    sell_cost = result["sell_costs"].total
    total_cost = result["total_cost"]

    assert 42 <= buy_cost <= 43
    assert 132 <= sell_cost <= 134
    assert 174 <= total_cost <= 177

    # Cost percentage
    assert 0.08 <= result["cost_percentage"] <= 0.09
```

### TC-004: Intraday STT Both Sides

```python
def test_equity_intraday_stt_both_sides():
    calc = CostCalculator()

    buy_costs = calc.calculate_equity_intraday_costs("BUY", 100000)
    sell_costs = calc.calculate_equity_intraday_costs("SELL", 105000)

    # STT on both sides for intraday
    assert buy_costs.stt == pytest.approx(25.00, abs=1)  # 0.025% of 100k
    assert sell_costs.stt == pytest.approx(26.25, abs=1)  # 0.025% of 105k

    # No DP charges for intraday
    assert buy_costs.dp_charges == 0.00
    assert sell_costs.dp_charges == 0.00
```

### TC-005: Futures Flat Brokerage

```python
def test_futures_flat_brokerage():
    calc = CostCalculator()

    # Large order (₹10L)
    costs_large = calc.calculate_futures_costs("BUY", 1000000)

    # Small order (₹10k)
    costs_small = calc.calculate_futures_costs("BUY", 10000)

    # Both should have ₹20 brokerage (flat, not percentage)
    assert costs_large.brokerage == 20.00
    assert costs_small.brokerage == 20.00
```

### TC-006: Validate Against Real Statement

```python
def test_validate_against_real_brokerage_statement():
    """
    Validate against actual brokerage statement

    Real trade:
    - BUY RELIANCE @ ₹2500, 40 shares = ₹1,00,000
    - Actual total cost from statement: ₹42.50
    """
    calc = CostCalculator()
    costs = calc.calculate_equity_delivery_costs("BUY", 100000, "NSE")

    # Should match real statement within ₹1
    assert abs(costs.total - 42.50) <= 1.00
```

---

## Edge Cases

### EC-1: Very Small Order (₹1,000)

```python
def test_small_order_1000():
    calc = CostCalculator()
    costs = calc.calculate_equity_delivery_costs("BUY", 1000)

    # 0.03% of 1000 = ₹0.30
    # min(₹20, ₹0.30) = ₹0.30
    # But some brokers have min brokerage = ₹10
    # For now, we use ₹0.30

    assert costs.brokerage <= 20.00
```

### EC-2: Very Large Order (₹1 Crore)

```python
def test_large_order_1_crore():
    calc = CostCalculator()
    costs = calc.calculate_equity_delivery_costs("BUY", 10000000)

    # 0.03% of 1Cr = ₹30,000
    # min(₹20, ₹30,000) = ₹20
    assert costs.brokerage == 20.00

    # SEBI fees: 0.0001% of 1Cr = ₹100
    assert costs.sebi_fees == pytest.approx(100, abs=1)
```

### EC-3: Zero Order Value

```python
def test_zero_order_value():
    calc = CostCalculator()
    costs = calc.calculate_equity_delivery_costs("BUY", 0)

    # All costs should be zero
    assert costs.total == 0.00
```

---

## Performance Requirements

### PR-1: Calculation Speed

**Requirement**: Calculate costs in < 1ms

```python
def test_cost_calculation_performance():
    calc = CostCalculator()

    start = time.time()
    for _ in range(1000):
        calc.calculate_equity_delivery_costs("BUY", 100000)
    end = time.time()

    avg_latency = (end - start) / 1000 * 1000  # ms
    assert avg_latency < 1  # < 1ms per calculation
```

---

## Implementation Checklist

- [ ] Create `execution/cost_calculator.py`
- [ ] Write 12 unit tests
- [ ] Validate against 10 real brokerage statements
- [ ] Test all instrument types (equity, F&O)
- [ ] Test edge cases (₹0, ₹1Cr)
- [ ] Document all rates with sources
- [ ] Add logging for debugging
- [ ] Performance test (<1ms)
- [ ] Integration with backtest engine
- [ ] Integration with paper trading

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: FX-005 (Slippage Simulator)
