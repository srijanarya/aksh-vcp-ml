# FX-002: Kelly Criterion Position Sizing

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-2 (Kelly Criterion Position Sizing)
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Specification

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

The Kelly Criterion Position Sizer calculates mathematically optimal position sizes to maximize long-term capital growth while respecting risk constraints.

### Background

**Kelly Criterion Formula**:
```
Kelly Fraction = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
```

**Why Kelly?**
- Maximizes geometric mean of capital growth
- Prevents over-betting (bankruptcy risk)
- Adjusts to strategy performance automatically

**Why Half-Kelly?**
- Full Kelly can be aggressive
- Half-Kelly reduces volatility
- Still captures ~75% of full Kelly growth

### Scope

**In Scope**:
- Kelly fraction calculation per strategy
- Half-Kelly conservative sizing
- Dynamic profit-based scaling
- 20% per-stock position cap
- 4% F&O position cap
- 2% total risk enforcement
- Multi-strategy allocation
- Strategy performance tracking

**Out of Scope**:
- Portfolio optimization (Markowitz, mean-variance)
- Options Greeks-based sizing
- Pair trading position sizing
- Sector exposure limits (future version)

---

## User Story

**As** the Portfolio Manager
**I want** position sizes optimized by Kelly Criterion
**So that** I maximize long-term capital growth while respecting risk limits

### Scenarios

#### Scenario 1: Standard Kelly Sizing

**Given**:
- Capital: ₹1,00,000
- Strategy: ADX+DMA
- Win Rate: 55%
- Avg Win: 5%
- Avg Loss: 3%

**When**: Calculate position size for RELIANCE signal

**Then**:
1. Kelly = (0.55 × 0.05 - 0.45 × 0.03) / 0.05 = 0.28
2. Half-Kelly = 0.28 / 2 = 0.14
3. Position size = ₹1,00,000 × 0.14 = ₹14,000
4. Cap check: ₹14,000 < ₹20,000 (20% limit) ✅
5. Final position: ₹14,000

#### Scenario 2: Profit Scaling

**Given**:
- Capital: ₹1,10,000 (up 10% from ₹1L)
- Same strategy (Kelly = 0.14)
- Profit level: +10% → Scale factor: 1.5×

**When**: Calculate position size

**Then**:
1. Base Kelly: 0.14
2. Scaled Kelly: 0.14 × 1.5 = 0.21
3. Position size: ₹1,10,000 × 0.21 = ₹23,100
4. Cap check: ₹23,100 > ₹22,000 (20% of ₹1.1L) ❌
5. Final position: ₹22,000 (capped)

#### Scenario 3: F&O Position

**Given**:
- Capital: ₹1,00,000
- Instrument: Nifty Future
- Kelly suggests: ₹8,000

**When**: Calculate F&O position

**Then**:
1. F&O cap: ₹1,00,000 × 0.04 = ₹4,000
2. Kelly suggestion: ₹8,000
3. Final position: ₹4,000 (F&O cap enforced)

#### Scenario 4: Total Risk Enforcement

**Given**:
- Peak capital: ₹1,10,000
- Current capital: ₹1,08,000
- Open positions: ₹15,000 (stop loss risk: ₹1,500)
- New signal: Position size would be ₹18,000 (risk: ₹900)

**When**: Check total risk constraint

**Then**:
1. Max total risk: ₹1,10,000 × 0.02 = ₹2,200
2. Current risk: ₹1,500
3. New trade risk: ₹900
4. Total risk: ₹1,500 + ₹900 = ₹2,400 > ₹2,200 ❌
5. Action: Reduce new position size or skip trade

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Calculate Kelly fraction for each strategy based on historical performance
✅ **AC-2**: Use Half-Kelly (divide by 2) for safety
✅ **AC-3**: Cap position at 20% of current capital (equity)
✅ **AC-4**: Cap position at 4% of current capital (F&O)
✅ **AC-5**: Scale Kelly based on profit level:
  - At ₹1L: 1.0× Kelly
  - At +5%: 1.2× Kelly
  - At +10%: 1.5× Kelly
  - At +20%: 2.0× Kelly

✅ **AC-6**: Enforce 2% total risk constraint (all positions combined)
✅ **AC-7**: Track strategy performance (win rate, avg win/loss) continuously
✅ **AC-8**: Update Kelly fractions weekly based on last 100 trades
✅ **AC-9**: Require minimum 30 trades before using strategy-specific Kelly (use conservative default before)

### Should Have

⭕ **AC-10**: Adjust Kelly for signal strength (strong signal → higher allocation)
⭕ **AC-11**: Adjust Kelly for sentiment (positive sentiment → +10%, negative → -10%)
⭕ **AC-12**: Support multi-strategy allocation (allocate capital across strategies)
⭕ **AC-13**: Log all position sizing decisions for audit trail

### Nice to Have

🔵 **AC-14**: Visualize Kelly fraction evolution over time
🔵 **AC-15**: Alert if Kelly suggests position > 30% (indicates overfitting)
🔵 **AC-16**: Compare Kelly vs fixed-size backtests

---

## Functional Design

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   KellyPositionSizer                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  StrategyPerformanceTracker                           │ │
│  │  - Track wins/losses per strategy                     │ │
│  │  - Calculate win rate, avg win/loss                   │ │
│  │  - Update after each trade                            │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  KellyCalculator                                      │ │
│  │  - Calculate Kelly fraction                           │ │
│  │  - Apply Half-Kelly                                   │ │
│  │  - Apply profit scaling                               │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  PositionSizeCalculator                               │ │
│  │  - Convert Kelly % to rupee amount                    │ │
│  │  - Apply 20% equity cap                               │ │
│  │  - Apply 4% F&O cap                                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  RiskConstraintValidator                              │ │
│  │  - Check total risk < 2% of peak                      │ │
│  │  - Adjust position if needed                          │ │
│  │  - Reject if can't satisfy constraints                │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Input: Signal
  ├─ Symbol: "RELIANCE"
  ├─ Strategy: "ADX+DMA"
  ├─ Side: "BUY"
  ├─ Entry Price: ₹2,500
  ├─ Stop Loss: ₹2,425 (3% risk)
  └─ Signal Strength: 85/100

Step 1: Get Strategy Performance
  ├─ Query trades.db for last 100 ADX+DMA trades
  ├─ Calculate: Win Rate = 55%, Avg Win = 5%, Avg Loss = 3%
  └─ Output: StrategyStats object

Step 2: Calculate Base Kelly
  ├─ Formula: (0.55 × 0.05 - 0.45 × 0.03) / 0.05
  ├─ Result: Kelly = 0.28
  └─ Half-Kelly: 0.14

Step 3: Apply Profit Scaling
  ├─ Current Capital: ₹1,10,000
  ├─ Initial Capital: ₹1,00,000
  ├─ Profit: +10% → Scale: 1.5×
  └─ Scaled Kelly: 0.14 × 1.5 = 0.21

Step 4: Adjust for Signal Strength
  ├─ Signal Strength: 85/100
  ├─ Adjustment: 0.85 (scale down for weaker signals)
  └─ Adjusted Kelly: 0.21 × 0.85 = 0.1785

Step 5: Calculate Position Size
  ├─ Position: ₹1,10,000 × 0.1785 = ₹19,635
  └─ Round to: ₹19,600

Step 6: Apply Caps
  ├─ 20% cap: ₹1,10,000 × 0.20 = ₹22,000
  ├─ ₹19,600 < ₹22,000 ✅
  └─ Position passes cap check

Step 7: Calculate Shares
  ├─ Price: ₹2,500
  ├─ Shares: ₹19,600 / ₹2,500 = 7.84
  └─ Rounded: 7 shares (₹17,500)

Step 8: Calculate Risk
  ├─ Entry: ₹2,500
  ├─ Stop: ₹2,425
  ├─ Risk per share: ₹75
  └─ Total risk: 7 × ₹75 = ₹525

Step 9: Check Total Risk Constraint
  ├─ Peak capital: ₹1,10,000
  ├─ Max total risk: ₹1,10,000 × 0.02 = ₹2,200
  ├─ Open positions risk: ₹1,200
  ├─ New trade risk: ₹525
  ├─ Total: ₹1,200 + ₹525 = ₹1,725 < ₹2,200 ✅
  └─ Position approved

Output: Position
  ├─ Symbol: "RELIANCE"
  ├─ Shares: 7
  ├─ Position Value: ₹17,500
  ├─ Risk: ₹525
  ├─ Kelly Fraction Used: 0.1785
  └─ Constraints: All satisfied
```

---

## Technical Specification

### Class: `KellyPositionSizer`

```python
# position_sizing/kelly_sizer.py
from dataclasses import dataclass
from typing import Optional
import logging

@dataclass
class StrategyStats:
    """Strategy performance statistics"""
    strategy_name: str
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    last_updated: str

@dataclass
class PositionSize:
    """Position sizing result"""
    symbol: str
    shares: int
    position_value: float
    kelly_fraction: float
    risk_amount: float
    constraints_applied: list[str]
    approved: bool
    rejection_reason: Optional[str] = None

class KellyPositionSizer:
    """
    Kelly Criterion position sizing with safety constraints

    Responsibilities:
    - Calculate Kelly fraction per strategy
    - Apply Half-Kelly for safety
    - Scale based on profit level
    - Enforce position caps (20% equity, 4% F&O)
    - Enforce total risk constraint (2% of peak)
    """

    def __init__(
        self,
        db_path: str,
        initial_capital: float,
        use_half_kelly: bool = True,
        equity_position_cap: float = 0.20,
        fno_position_cap: float = 0.04,
        max_total_risk_pct: float = 0.02,
    ):
        """
        Initialize Kelly Position Sizer

        Args:
            db_path: Path to trades.db (for strategy performance)
            initial_capital: Starting capital (for profit scaling)
            use_half_kelly: Use Half-Kelly (default: True)
            equity_position_cap: Max % in single equity (default: 20%)
            fno_position_cap: Max % in F&O (default: 4%)
            max_total_risk_pct: Max total risk as % of peak (default: 2%)
        """
        self.db_path = db_path
        self.initial_capital = initial_capital
        self.use_half_kelly = use_half_kelly
        self.equity_position_cap = equity_position_cap
        self.fno_position_cap = fno_position_cap
        self.max_total_risk_pct = max_total_risk_pct

        self.logger = logging.getLogger(__name__)

        # Performance tracker
        self.performance_tracker = StrategyPerformanceTracker(db_path)

        # Risk manager (for total risk check)
        self.risk_manager = None  # Injected later

    def calculate_position_size(
        self,
        signal: dict,
        current_capital: float,
        peak_capital: float,
        instrument_type: str = "EQUITY",
        signal_strength: float = 1.0,
        sentiment_score: float = 0.0,
    ) -> PositionSize:
        """
        Calculate optimal position size

        Args:
            signal: Trading signal dict with:
                - symbol: str
                - strategy: str
                - side: 'BUY' or 'SELL'
                - entry_price: float
                - stop_loss: float
            current_capital: Current portfolio value
            peak_capital: Peak portfolio value (for risk calc)
            instrument_type: 'EQUITY' or 'FNO'
            signal_strength: 0-1 (1.0 = strongest)
            sentiment_score: -1 to +1 (0 = neutral)

        Returns:
            PositionSize object with shares and risk details
        """
        symbol = signal["symbol"]
        strategy = signal["strategy"]
        entry_price = signal["entry_price"]
        stop_loss = signal["stop_loss"]

        constraints_applied = []

        # Step 1: Get strategy performance
        stats = self.performance_tracker.get_strategy_stats(strategy)

        if stats.total_trades < 30:
            # Not enough data, use conservative default
            self.logger.warning(
                f"{strategy} has only {stats.total_trades} trades. "
                f"Using conservative default Kelly."
            )
            kelly_fraction = 0.10  # Conservative default
            constraints_applied.append("INSUFFICIENT_HISTORY")
        else:
            # Step 2: Calculate base Kelly
            kelly_fraction = self._calculate_kelly_fraction(stats)

        # Step 3: Apply Half-Kelly
        if self.use_half_kelly:
            kelly_fraction = kelly_fraction / 2
            constraints_applied.append("HALF_KELLY")

        # Step 4: Apply profit scaling
        kelly_fraction = self._apply_profit_scaling(
            kelly_fraction, current_capital, self.initial_capital
        )

        # Step 5: Adjust for signal strength
        kelly_fraction = kelly_fraction * signal_strength

        # Step 6: Adjust for sentiment
        kelly_fraction = self._apply_sentiment_adjustment(
            kelly_fraction, sentiment_score
        )

        # Step 7: Calculate position value
        position_value = current_capital * kelly_fraction

        # Step 8: Apply position caps
        position_cap = self._get_position_cap(
            current_capital, instrument_type
        )

        if position_value > position_cap:
            position_value = position_cap
            cap_type = "EQUITY_20PCT" if instrument_type == "EQUITY" else "FNO_4PCT"
            constraints_applied.append(cap_type)

        # Step 9: Calculate shares
        shares = int(position_value / entry_price)
        actual_position_value = shares * entry_price

        # Step 10: Calculate risk
        risk_per_share = abs(entry_price - stop_loss)
        risk_amount = shares * risk_per_share

        # Step 11: Check total risk constraint
        total_risk_approved = self._check_total_risk_constraint(
            risk_amount, peak_capital
        )

        if not total_risk_approved:
            # Reject or reduce position
            max_allowed_risk = peak_capital * self.max_total_risk_pct
            current_open_risk = self.risk_manager.get_total_open_risk()
            available_risk = max_allowed_risk - current_open_risk

            if available_risk <= 0:
                return PositionSize(
                    symbol=symbol,
                    shares=0,
                    position_value=0,
                    kelly_fraction=kelly_fraction,
                    risk_amount=0,
                    constraints_applied=constraints_applied,
                    approved=False,
                    rejection_reason="TOTAL_RISK_EXCEEDED",
                )

            # Reduce shares to fit risk budget
            max_shares = int(available_risk / risk_per_share)
            shares = min(shares, max_shares)
            actual_position_value = shares * entry_price
            risk_amount = shares * risk_per_share
            constraints_applied.append("TOTAL_RISK_CAP")

        # Step 12: Return result
        return PositionSize(
            symbol=symbol,
            shares=shares,
            position_value=actual_position_value,
            kelly_fraction=kelly_fraction,
            risk_amount=risk_amount,
            constraints_applied=constraints_applied,
            approved=shares > 0,
        )

    def _calculate_kelly_fraction(self, stats: StrategyStats) -> float:
        """
        Calculate Kelly fraction

        Formula: Kelly = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
        """
        win_rate = stats.win_rate
        loss_rate = 1 - win_rate
        avg_win = stats.avg_win_pct
        avg_loss = stats.avg_loss_pct

        # Validate inputs
        if avg_win <= 0:
            self.logger.error("Average win must be positive")
            return 0.0

        kelly = (win_rate * avg_win - loss_rate * avg_loss) / avg_win

        # Kelly should be between 0 and 1
        # Negative Kelly = losing strategy, return 0
        if kelly < 0:
            self.logger.warning(
                f"Strategy has negative expectancy. Kelly = {kelly:.4f}"
            )
            return 0.0

        # Kelly > 1 is unusual (very high edge), cap at 0.50
        if kelly > 0.50:
            self.logger.warning(
                f"Kelly fraction very high: {kelly:.4f}. "
                f"Possible overfitting. Capping at 0.50."
            )
            return 0.50

        return kelly

    def _apply_profit_scaling(
        self, kelly: float, current_capital: float, initial_capital: float
    ) -> float:
        """
        Scale Kelly based on profit level

        Scaling:
        - At ₹1L: 1.0× Kelly
        - At +5%: 1.2× Kelly
        - At +10%: 1.5× Kelly
        - At +20%: 2.0× Kelly
        - Below ₹1L (loss): 0.8× Kelly (more conservative)
        """
        profit_pct = (current_capital - initial_capital) / initial_capital

        if profit_pct >= 0.20:
            scale = 2.0
        elif profit_pct >= 0.10:
            scale = 1.5
        elif profit_pct >= 0.05:
            scale = 1.2
        elif profit_pct >= 0:
            scale = 1.0
        else:
            # In drawdown, be more conservative
            scale = 0.8

        scaled_kelly = kelly * scale

        self.logger.info(
            f"Profit: {profit_pct*100:.1f}%, Scale: {scale}×, "
            f"Kelly: {kelly:.4f} → {scaled_kelly:.4f}"
        )

        return scaled_kelly

    def _apply_sentiment_adjustment(
        self, kelly: float, sentiment_score: float
    ) -> float:
        """
        Adjust Kelly based on sentiment

        Adjustment:
        - Positive sentiment (+0.5): Increase by 10%
        - Negative sentiment (-0.5): Decrease by 10%
        - Neutral (0): No change
        """
        # Sentiment score is -1 to +1
        # Map to adjustment: -10% to +10%
        adjustment = sentiment_score * 0.10

        adjusted_kelly = kelly * (1 + adjustment)

        self.logger.info(
            f"Sentiment: {sentiment_score:+.2f}, "
            f"Adjustment: {adjustment*100:+.1f}%, "
            f"Kelly: {kelly:.4f} → {adjusted_kelly:.4f}"
        )

        return adjusted_kelly

    def _get_position_cap(
        self, current_capital: float, instrument_type: str
    ) -> float:
        """Get position cap based on instrument type"""
        if instrument_type == "FNO":
            return current_capital * self.fno_position_cap
        else:
            return current_capital * self.equity_position_cap

    def _check_total_risk_constraint(
        self, new_trade_risk: float, peak_capital: float
    ) -> bool:
        """Check if adding this trade exceeds total risk limit"""
        max_total_risk = peak_capital * self.max_total_risk_pct
        current_open_risk = self.risk_manager.get_total_open_risk()
        total_risk = current_open_risk + new_trade_risk

        if total_risk > max_total_risk:
            self.logger.warning(
                f"Total risk would exceed limit: "
                f"₹{total_risk:,.0f} > ₹{max_total_risk:,.0f}"
            )
            return False

        return True
```

### Class: `StrategyPerformanceTracker`

```python
# position_sizing/strategy_tracker.py
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class StrategyStats:
    strategy_name: str
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    last_updated: str

class StrategyPerformanceTracker:
    """Track strategy performance for Kelly calculation"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_strategy_stats(
        self, strategy_name: str, lookback_trades: int = 100
    ) -> StrategyStats:
        """
        Get strategy statistics from last N trades

        Args:
            strategy_name: Strategy identifier
            lookback_trades: Number of recent trades to analyze

        Returns:
            StrategyStats object
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get last N closed trades for this strategy
        query = """
        SELECT
            exit_date,
            (exit_price - entry_price) / entry_price AS return_pct
        FROM trades
        WHERE strategy = ?
          AND exit_date IS NOT NULL
        ORDER BY exit_date DESC
        LIMIT ?
        """

        cursor.execute(query, (strategy_name, lookback_trades))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            # No trade history, return conservative defaults
            return StrategyStats(
                strategy_name=strategy_name,
                total_trades=0,
                wins=0,
                losses=0,
                win_rate=0.50,  # Neutral
                avg_win_pct=0.03,  # Conservative 3%
                avg_loss_pct=0.02,  # Conservative 2%
                last_updated=datetime.now().isoformat(),
            )

        # Calculate statistics
        total_trades = len(rows)
        wins = [r[1] for r in rows if r[1] > 0]
        losses = [abs(r[1]) for r in rows if r[1] <= 0]

        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / total_trades if total_trades > 0 else 0

        avg_win_pct = sum(wins) / len(wins) if wins else 0.03
        avg_loss_pct = sum(losses) / len(losses) if losses else 0.02

        return StrategyStats(
            strategy_name=strategy_name,
            total_trades=total_trades,
            wins=win_count,
            losses=loss_count,
            win_rate=win_rate,
            avg_win_pct=avg_win_pct,
            avg_loss_pct=avg_loss_pct,
            last_updated=datetime.now().isoformat(),
        )

    def update_after_trade(
        self, strategy_name: str, return_pct: float
    ) -> None:
        """
        Update strategy stats after trade closes

        Args:
            strategy_name: Strategy identifier
            return_pct: Trade return (e.g., 0.05 for +5%)
        """
        # Trade is already recorded in trades.db
        # This method can trigger recalculation or caching
        pass  # Stats are calculated on-demand from DB
```

---

## API Contracts

### Input: Trading Signal

```python
signal = {
    "symbol": "RELIANCE",
    "strategy": "ADX+DMA",
    "side": "BUY",
    "entry_price": 2500.0,
    "stop_loss": 2425.0,
    "target": 2625.0,
    "signal_strength": 0.85,  # 0-1
    "timestamp": "2025-11-19T09:30:00",
}
```

### Output: Position Size

```python
position = PositionSize(
    symbol="RELIANCE",
    shares=7,
    position_value=17500.0,
    kelly_fraction=0.1785,
    risk_amount=525.0,
    constraints_applied=["HALF_KELLY", "SIGNAL_STRENGTH_ADJUSTED"],
    approved=True,
    rejection_reason=None,
)
```

### Integration with Signal Generator

```python
# signals/signal_generator.py
from position_sizing.kelly_sizer import KellyPositionSizer

def generate_order(signal: dict) -> dict:
    """Convert signal to order with position sizing"""

    # Get current portfolio state
    current_capital = portfolio.get_current_value()
    peak_capital = portfolio.get_peak_value()

    # Calculate position size
    sizer = KellyPositionSizer(db_path="trades.db", initial_capital=100000)
    position = sizer.calculate_position_size(
        signal=signal,
        current_capital=current_capital,
        peak_capital=peak_capital,
        instrument_type="EQUITY",
        signal_strength=signal["signal_strength"],
        sentiment_score=0.0,  # From sentiment analyzer
    )

    if not position.approved:
        logger.warning(f"Position rejected: {position.rejection_reason}")
        return None

    # Create order
    order = {
        "symbol": position.symbol,
        "side": signal["side"],
        "quantity": position.shares,
        "price": signal["entry_price"],
        "order_type": "LIMIT",
        "stop_loss": signal["stop_loss"],
        "kelly_fraction": position.kelly_fraction,
        "position_value": position.position_value,
        "risk": position.risk_amount,
    }

    return order
```

---

## Data Models

### Database: `trades.db`

#### Table: `trades`

```sql
CREATE TABLE trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    side TEXT CHECK(side IN ('BUY', 'SELL')),
    entry_date DATE NOT NULL,
    entry_price REAL NOT NULL,
    shares INTEGER NOT NULL,
    stop_loss REAL NOT NULL,
    target REAL,
    exit_date DATE,
    exit_price REAL,
    exit_reason TEXT,
    gross_pnl REAL,
    costs REAL,
    net_pnl REAL,
    return_pct REAL,
    kelly_fraction REAL,  -- Kelly used for this trade
    position_value REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategy_exit ON trades(strategy, exit_date);
```

#### Table: `strategy_performance` (Cache)

```sql
CREATE TABLE strategy_performance (
    strategy_name TEXT PRIMARY KEY,
    total_trades INTEGER,
    wins INTEGER,
    losses INTEGER,
    win_rate REAL,
    avg_win_pct REAL,
    avg_loss_pct REAL,
    kelly_fraction REAL,
    last_updated TIMESTAMP
);
```

---

## Business Rules

### BR-1: Kelly Calculation

**Rule**: Kelly = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win

**Implementation**:
```python
def calculate_kelly(win_rate, avg_win, avg_loss):
    loss_rate = 1 - win_rate
    kelly = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
    return max(0, min(kelly, 0.50))  # Clamp to [0, 0.50]
```

**Validation**:
- Win rate must be 0-1
- Avg win must be > 0
- Avg loss must be >= 0
- Negative Kelly → return 0 (losing strategy)
- Kelly > 0.50 → cap at 0.50 (prevent overfitting)

### BR-2: Half-Kelly

**Rule**: Divide Kelly by 2 for safety

**Rationale**:
- Full Kelly can be aggressive
- Half-Kelly captures ~75% of growth with 50% less volatility

**Implementation**:
```python
if use_half_kelly:
    kelly = kelly / 2
```

### BR-3: Profit Scaling

**Rule**: Scale Kelly based on profit from initial capital

| Profit Level | Scale Factor |
|--------------|--------------|
| Below ₹1L (loss) | 0.8× |
| ₹1L - ₹1.05L (0-5%) | 1.0× |
| ₹1.05L - ₹1.10L (5-10%) | 1.2× |
| ₹1.10L - ₹1.20L (10-20%) | 1.5× |
| Above ₹1.20L (>20%) | 2.0× |

**Implementation**:
```python
profit_pct = (current - initial) / initial
if profit_pct >= 0.20:
    scale = 2.0
elif profit_pct >= 0.10:
    scale = 1.5
# ... etc
kelly_scaled = kelly * scale
```

### BR-4: Position Caps

**Rule**:
- Equity: Max 20% of capital per stock
- F&O: Max 4% of capital

**Implementation**:
```python
equity_cap = current_capital * 0.20
fno_cap = current_capital * 0.04

if instrument_type == "FNO":
    position_value = min(position_value, fno_cap)
else:
    position_value = min(position_value, equity_cap)
```

### BR-5: Total Risk Constraint

**Rule**: Total risk across all positions must not exceed 2% of peak capital

**Calculation**:
```python
max_total_risk = peak_capital * 0.02

# Risk per position
position_risk = shares * abs(entry_price - stop_loss)

# Total risk
total_risk = sum(open_position_risks) + position_risk

if total_risk > max_total_risk:
    # Reject or reduce position
```

### BR-6: Minimum Trade History

**Rule**: Require 30+ trades before using strategy-specific Kelly

**Implementation**:
```python
if total_trades < 30:
    # Use conservative default
    kelly = 0.10
    avg_win = 0.03
    avg_loss = 0.02
else:
    # Use actual stats
    kelly = calculate_kelly(win_rate, avg_win, avg_loss)
```

### BR-7: Weekly Recalculation

**Rule**: Recalculate Kelly fractions every Monday

**Implementation**:
```python
# Scheduled task (cron or similar)
# Every Monday at 8:00 AM
def recalculate_kelly_fractions():
    for strategy in strategies:
        stats = tracker.get_strategy_stats(strategy)
        kelly = calculate_kelly(stats)
        cache_kelly(strategy, kelly)
```

---

## Test Cases

### TC-001: Basic Kelly Calculation

**Given**:
- Win Rate: 55%
- Avg Win: 5%
- Avg Loss: 3%

**When**: Calculate Kelly

**Then**:
- Kelly = (0.55 × 0.05 - 0.45 × 0.03) / 0.05 = 0.28
- Half-Kelly = 0.14

**Test Code**:
```python
def test_basic_kelly_calculation():
    sizer = KellyPositionSizer(db_path=":memory:", initial_capital=100000)
    stats = StrategyStats(
        strategy_name="ADX+DMA",
        total_trades=100,
        wins=55,
        losses=45,
        win_rate=0.55,
        avg_win_pct=0.05,
        avg_loss_pct=0.03,
        last_updated="2025-11-19",
    )

    kelly = sizer._calculate_kelly_fraction(stats)
    assert kelly == pytest.approx(0.28, abs=0.01)

    half_kelly = kelly / 2
    assert half_kelly == pytest.approx(0.14, abs=0.01)
```

### TC-002: Profit Scaling at +10%

**Given**:
- Initial capital: ₹1,00,000
- Current capital: ₹1,10,000 (+10%)
- Base Kelly: 0.14

**When**: Apply profit scaling

**Then**:
- Scale factor: 1.5×
- Scaled Kelly: 0.14 × 1.5 = 0.21

**Test Code**:
```python
def test_profit_scaling_10pct():
    sizer = KellyPositionSizer(db_path=":memory:", initial_capital=100000)

    base_kelly = 0.14
    scaled_kelly = sizer._apply_profit_scaling(
        kelly=base_kelly,
        current_capital=110000,
        initial_capital=100000,
    )

    assert scaled_kelly == pytest.approx(0.21, abs=0.01)
```

### TC-003: 20% Position Cap

**Given**:
- Capital: ₹1,00,000
- Kelly suggests: 30% position (₹30,000)

**When**: Apply equity cap

**Then**:
- Capped at 20% = ₹20,000

**Test Code**:
```python
def test_equity_position_cap():
    sizer = KellyPositionSizer(
        db_path=":memory:",
        initial_capital=100000,
        equity_position_cap=0.20,
    )

    # Mock signal with very high Kelly
    # (This would happen with very high win rate or payoff ratio)
    position_value = 100000 * 0.30  # Kelly suggests 30%

    cap = sizer._get_position_cap(100000, "EQUITY")
    final_position = min(position_value, cap)

    assert final_position == 20000
```

### TC-004: F&O 4% Cap

**Given**:
- Capital: ₹1,00,000
- Kelly suggests: ₹8,000 F&O position

**When**: Apply F&O cap

**Then**:
- Capped at 4% = ₹4,000

**Test Code**:
```python
def test_fno_position_cap():
    sizer = KellyPositionSizer(
        db_path=":memory:",
        initial_capital=100000,
        fno_position_cap=0.04,
    )

    cap = sizer._get_position_cap(100000, "FNO")
    assert cap == 4000

    position_value = 8000  # Kelly suggests more
    final_position = min(position_value, cap)

    assert final_position == 4000
```

### TC-005: Total Risk Constraint

**Given**:
- Peak capital: ₹1,10,000
- Max total risk: 2% = ₹2,200
- Current open risk: ₹1,800
- New trade risk: ₹600

**When**: Check total risk

**Then**:
- Total: ₹1,800 + ₹600 = ₹2,400 > ₹2,200 ❌
- Reject or reduce position

**Test Code**:
```python
def test_total_risk_constraint_exceeded(mocker):
    sizer = KellyPositionSizer(
        db_path=":memory:",
        initial_capital=100000,
        max_total_risk_pct=0.02,
    )

    # Mock risk manager
    mock_risk_manager = mocker.Mock()
    mock_risk_manager.get_total_open_risk.return_value = 1800
    sizer.risk_manager = mock_risk_manager

    # New trade risk: ₹600
    new_trade_risk = 600
    peak_capital = 110000

    approved = sizer._check_total_risk_constraint(new_trade_risk, peak_capital)

    assert approved is False  # Total risk would be ₹2,400 > ₹2,200
```

### TC-006: Insufficient Trade History

**Given**:
- Strategy: "NEW_STRATEGY"
- Total trades: 15 (< 30 minimum)

**When**: Calculate position size

**Then**:
- Use conservative default Kelly = 0.10
- Flag constraint: "INSUFFICIENT_HISTORY"

**Test Code**:
```python
def test_insufficient_trade_history(mocker):
    sizer = KellyPositionSizer(db_path=":memory:", initial_capital=100000)

    # Mock tracker to return insufficient history
    mock_tracker = mocker.Mock()
    mock_tracker.get_strategy_stats.return_value = StrategyStats(
        strategy_name="NEW_STRATEGY",
        total_trades=15,  # < 30
        wins=8,
        losses=7,
        win_rate=0.53,
        avg_win_pct=0.04,
        avg_loss_pct=0.03,
        last_updated="2025-11-19",
    )
    sizer.performance_tracker = mock_tracker

    signal = {
        "symbol": "RELIANCE",
        "strategy": "NEW_STRATEGY",
        "side": "BUY",
        "entry_price": 2500,
        "stop_loss": 2425,
    }

    # Mock risk manager
    mock_risk_manager = mocker.Mock()
    mock_risk_manager.get_total_open_risk.return_value = 0
    sizer.risk_manager = mock_risk_manager

    position = sizer.calculate_position_size(
        signal=signal,
        current_capital=100000,
        peak_capital=100000,
    )

    assert "INSUFFICIENT_HISTORY" in position.constraints_applied
```

### TC-007: Negative Expectancy Strategy

**Given**:
- Win Rate: 40%
- Avg Win: 3%
- Avg Loss: 4%

**When**: Calculate Kelly

**Then**:
- Kelly = (0.40 × 0.03 - 0.60 × 0.04) / 0.03 = -0.40 (negative)
- Return: 0 (don't trade losing strategy)

**Test Code**:
```python
def test_negative_expectancy_strategy():
    sizer = KellyPositionSizer(db_path=":memory:", initial_capital=100000)

    stats = StrategyStats(
        strategy_name="BAD_STRATEGY",
        total_trades=100,
        wins=40,
        losses=60,
        win_rate=0.40,
        avg_win_pct=0.03,
        avg_loss_pct=0.04,
        last_updated="2025-11-19",
    )

    kelly = sizer._calculate_kelly_fraction(stats)
    assert kelly == 0.0  # Negative expectancy → 0
```

### TC-008: Sentiment Adjustment

**Given**:
- Base Kelly: 0.14
- Sentiment: +0.5 (positive)

**When**: Apply sentiment adjustment

**Then**:
- Adjustment: +10%
- Adjusted Kelly: 0.14 × 1.10 = 0.154

**Test Code**:
```python
def test_sentiment_positive_adjustment():
    sizer = KellyPositionSizer(db_path=":memory:", initial_capital=100000)

    base_kelly = 0.14
    sentiment_score = 0.5  # Positive

    adjusted_kelly = sizer._apply_sentiment_adjustment(base_kelly, sentiment_score)

    assert adjusted_kelly == pytest.approx(0.154, abs=0.01)
```

---

## Edge Cases

### Edge Case 1: Zero Capital

**Scenario**: Capital becomes zero (catastrophic loss)

**Expected**:
- All position sizes return 0
- System halts trading

**Implementation**:
```python
if current_capital <= 0:
    logger.error("Capital is zero. Trading halted.")
    return PositionSize(..., shares=0, approved=False, rejection_reason="ZERO_CAPITAL")
```

### Edge Case 2: Kelly > 1.0

**Scenario**: Extremely high win rate or payoff ratio

**Expected**:
- Cap Kelly at 0.50
- Log warning (possible overfitting)

**Implementation**:
```python
if kelly > 0.50:
    logger.warning(f"Kelly={kelly:.4f} exceeds 0.50. Capping.")
    kelly = 0.50
```

### Edge Case 3: First Trade (No History)

**Scenario**: Very first trade for a strategy

**Expected**:
- Use conservative defaults
- Win rate: 50%, Avg win: 3%, Avg loss: 2%
- Kelly ≈ 0.08

**Implementation**:
```python
if total_trades == 0:
    return StrategyStats(
        ...,
        win_rate=0.50,
        avg_win_pct=0.03,
        avg_loss_pct=0.02,
    )
```

### Edge Case 4: All Wins or All Losses

**Scenario**: Strategy has 100% win rate (10/10 trades won)

**Expected**:
- Use cautious Kelly (avoid overconfidence)
- Wait for more data

**Implementation**:
```python
if total_trades < 50:
    # Not enough data to trust 100% win rate
    kelly = min(kelly, 0.15)  # Cap at conservative value
```

### Edge Case 5: Very Large Position (Illiquid Stock)

**Scenario**: Kelly suggests ₹50,000 position in small-cap stock

**Expected**:
- Check liquidity (average daily volume)
- Reduce position if > 2% of ADV
- Increase slippage estimate

**Implementation** (Future):
```python
avg_daily_volume = get_avg_daily_volume(symbol)
max_position = avg_daily_volume * avg_price * 0.02  # 2% of ADV
position_value = min(position_value, max_position)
```

---

## Performance Requirements

### PR-1: Calculation Speed

**Requirement**: Calculate position size in < 10ms

**Test**:
```python
def test_position_sizing_performance():
    sizer = KellyPositionSizer(db_path="trades.db", initial_capital=100000)

    signal = {...}

    start = time.time()
    position = sizer.calculate_position_size(signal, 100000, 100000)
    end = time.time()

    latency = (end - start) * 1000  # ms
    assert latency < 10  # < 10ms
```

### PR-2: Database Query Optimization

**Requirement**: Strategy stats query < 5ms

**Implementation**:
- Index on (strategy, exit_date)
- Limit to last 100 trades
- Cache results for 1 hour

**Test**:
```python
def test_strategy_stats_query_performance():
    tracker = StrategyPerformanceTracker("trades.db")

    start = time.time()
    stats = tracker.get_strategy_stats("ADX+DMA")
    end = time.time()

    latency = (end - start) * 1000
    assert latency < 5  # < 5ms
```

---

## Dependencies

### Internal Dependencies

- **risk_management.risk_manager**: For total risk calculation
- **data.portfolio**: For current/peak capital
- **intelligence.sentiment_analyzer**: For sentiment scores
- **execution.cost_calculator**: For cost estimation

### External Dependencies

- **SQLite3**: For trades database
- **Python**: 3.11+
- **Logging**: Standard library

### Database Schema

Requires `trades.db` with `trades` table:
```sql
CREATE TABLE trades (
    trade_id INTEGER PRIMARY KEY,
    strategy TEXT,
    entry_price REAL,
    exit_price REAL,
    entry_date DATE,
    exit_date DATE,
    ...
);
```

---

## Implementation Checklist

- [ ] Create `position_sizing/kelly_sizer.py`
- [ ] Create `position_sizing/strategy_tracker.py`
- [ ] Write 15 unit tests (tests/unit/test_kelly_sizer.py)
- [ ] Write 3 integration tests (tests/integration/test_kelly_integration.py)
- [ ] Create SQLite schema for trades.db
- [ ] Implement profit scaling logic
- [ ] Implement sentiment adjustment
- [ ] Implement total risk constraint check
- [ ] Add logging for all decisions
- [ ] Add performance monitoring (<10ms)
- [ ] Document all business rules
- [ ] Create user documentation
- [ ] Code review and refactor

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: FX-003 (Indian Market Cost Calculator)
