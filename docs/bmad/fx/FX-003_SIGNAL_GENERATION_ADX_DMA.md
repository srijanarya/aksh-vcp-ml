# FX-003: ADX + DMA Signal Generation

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-3 (ADX + Displacement Moving Average Scanner)
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

The ADX + DMA Signal Generator identifies high-probability trading opportunities by combining trend strength (ADX) with momentum breakouts (Displacement Moving Average).

### Background

**Strategy Components**:

1. **ADX (Average Directional Index)**:
   - Measures trend strength (0-100)
   - ADX > 25: Strong trend
   - ADX < 20: Weak/choppy market

2. **DMA (Displacement Moving Average)**:
   - Price displacement from 20-day EMA
   - DMA > +5%: Bullish momentum
   - DMA < -5%: Bearish momentum

3. **Combined Signal**:
   - BUY: ADX > 25 AND DMA > +5% AND price > 20 EMA
   - SELL: ADX > 25 AND DMA < -5% AND price < 20 EMA

**Why This Combination?**
- ADX filters out choppy markets (reduces whipsaws)
- DMA identifies momentum breakouts
- Together: High-probability entries with strong directional bias

### Scope

**In Scope**:
- Calculate ADX (14-period default)
- Calculate DMA (20-period EMA displacement)
- Generate BUY/SELL signals
- Signal strength scoring (0-100)
- Volume confirmation
- Support/resistance analysis
- Multi-timeframe confluence

**Out of Scope**:
- Machine learning signal enhancement (future version)
- Options strategies
- Pair trading signals
- Sector rotation signals

---

## User Story

**As** the Trading System
**I want** ADX + DMA signals generated daily at 9:30 AM
**So that** I can identify high-probability trade setups

### Scenarios

#### Scenario 1: Strong Bullish Signal

**Given**:
- Symbol: "RELIANCE"
- Date: 2025-11-19
- ADX: 32 (strong trend)
- 20 EMA: ₹2,450
- Current Price: ₹2,520
- DMA: +2.86% ((2520 - 2450) / 2450)

**When**: Calculate signal

**Then**:
1. ADX Check: 32 > 25 ✅
2. Price Check: 2520 > 2450 (above EMA) ✅
3. DMA Check: +2.86% (approaching +5% threshold)
4. Signal: WEAK_BUY (DMA not yet > 5%)
5. Wait for stronger confirmation

#### Scenario 2: Perfect BUY Signal

**Given**:
- Symbol: "TCS"
- ADX: 35
- 20 EMA: ₹3,500
- Current Price: ₹3,700
- DMA: +5.71% ((3700 - 3500) / 3500)
- Volume: 2.5x average

**When**: Calculate signal

**Then**:
1. ADX Check: 35 > 25 ✅
2. Price Check: 3700 > 3500 ✅
3. DMA Check: +5.71% > +5% ✅
4. Volume Check: 2.5x > 1.5x ✅
5. Signal: STRONG_BUY
6. Signal Strength: 95/100

#### Scenario 3: Bearish Signal (SELL)

**Given**:
- Symbol: "INFY"
- ADX: 28
- 20 EMA: ₹1,500
- Current Price: ₹1,420
- DMA: -5.33% ((1420 - 1500) / 1500)

**When**: Calculate signal

**Then**:
1. ADX Check: 28 > 25 ✅
2. Price Check: 1420 < 1500 (below EMA) ✅
3. DMA Check: -5.33% < -5% ✅
4. Signal: SELL
5. Strategy: SHORT or AVOID (cash-only portfolio)

#### Scenario 4: Choppy Market (No Signal)

**Given**:
- Symbol: "HDFC"
- ADX: 18 (weak trend)
- DMA: +3%

**When**: Calculate signal

**Then**:
1. ADX Check: 18 < 25 ❌
2. Signal: NONE
3. Reason: "Choppy market, ADX too low"
4. Action: Skip trade

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Calculate ADX (14-period) for all watchlist symbols
✅ **AC-2**: Calculate DMA (displacement from 20 EMA) for all symbols
✅ **AC-3**: Generate BUY signal when ADX > 25 AND DMA > +5% AND price > 20 EMA
✅ **AC-4**: Generate SELL signal when ADX > 25 AND DMA < -5% AND price < 20 EMA
✅ **AC-5**: Calculate signal strength score (0-100) based on:
  - ADX value (higher = stronger)
  - DMA magnitude (larger = stronger)
  - Volume confirmation (higher = stronger)
✅ **AC-6**: Filter signals by volume (must be > 1.5x 20-day average)
✅ **AC-7**: Include support/resistance levels in signal
✅ **AC-8**: Generate signals daily at 9:30 AM IST
✅ **AC-9**: Output signals in standardized format (JSON/DataFrame)

### Should Have

⭕ **AC-10**: Multi-timeframe confirmation (daily + 60min alignment)
⭕ **AC-11**: ATR-based stop-loss calculation
⭕ **AC-12**: Target calculation (2:1 reward:risk minimum)
⭕ **AC-13**: Filter by market regime (trending vs choppy)

### Nice to Have

🔵 **AC-14**: Backtest signal performance (win rate, avg return)
🔵 **AC-15**: Signal quality ranking (A, B, C grades)
🔵 **AC-16**: Alert notification via Telegram

---

## Functional Design

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ADXDMASignalGenerator                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  TechnicalIndicatorCalculator                         │ │
│  │  - Calculate ADX (14-period)                          │ │
│  │  - Calculate 20 EMA                                   │ │
│  │  - Calculate DMA (displacement %)                     │ │
│  │  - Calculate ATR (for stop-loss)                      │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  SignalFilter                                         │ │
│  │  - Check ADX > 25                                     │ │
│  │  - Check DMA thresholds                               │ │
│  │  - Check price position vs EMA                        │ │
│  │  - Check volume confirmation                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  SignalScorer                                         │ │
│  │  - Calculate signal strength (0-100)                  │ │
│  │  - Incorporate volume, ADX, DMA magnitude             │ │
│  │  - Multi-timeframe bonus                              │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  SupportResistanceDetector                            │ │
│  │  - Find recent swing highs/lows                       │ │
│  │  - Calculate stop-loss levels                         │ │
│  │  - Calculate target levels                            │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  SignalOutputFormatter                                │ │
│  │  - Format signals as JSON/DataFrame                   │ │
│  │  - Include all metadata                               │ │
│  │  - Ready for position sizing                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Signal Generation Flow

```
Input: Watchlist [RELIANCE, TCS, INFY, HDFC, ...]

Step 1: Fetch Data
  ├─ For each symbol in watchlist
  ├─ Fetch last 100 days OHLCV (for ADX/EMA calculation)
  └─ Store in DataFrame

Step 2: Calculate Technical Indicators
  ├─ ADX (14-period)
  │  ├─ Calculate +DI and -DI
  │  ├─ Calculate DX
  │  └─ Smooth DX to get ADX
  │
  ├─ 20 EMA
  │  └─ Exponential moving average of close prices
  │
  ├─ DMA (Displacement %)
  │  └─ ((Current Price - 20 EMA) / 20 EMA) × 100
  │
  └─ ATR (14-period)
     └─ For stop-loss calculation

Step 3: Apply Signal Filters
  ├─ ADX Filter: ADX > 25?
  ├─ DMA Filter: DMA > +5% (BUY) or < -5% (SELL)?
  ├─ Price Filter: Price > EMA (BUY) or < EMA (SELL)?
  └─ Volume Filter: Volume > 1.5x avg?

Step 4: Generate Signals
  ├─ If all filters pass → Create signal
  ├─ If some filters fail → No signal
  └─ Signal includes: symbol, side, entry, stop, target

Step 5: Calculate Signal Strength
  ├─ Base score: 50
  ├─ ADX bonus: (ADX - 25) × 2 (max +30)
  ├─ DMA bonus: abs(DMA - 5) × 4 (max +20)
  ├─ Volume bonus: (volume_ratio - 1.5) × 20 (max +10)
  ├─ Multi-timeframe bonus: +10 if 60min confirms
  └─ Total: 0-100

Step 6: Calculate Stop-Loss and Target
  ├─ Stop-Loss: Current Price - (2 × ATR)
  ├─ Risk per share: Current Price - Stop-Loss
  ├─ Target: Current Price + (2 × Risk) [2:1 R:R]
  └─ Validate: Target is reasonable (< 20% from entry)

Step 7: Format Output
  └─ Output: [
      {
        symbol: "TCS",
        side: "BUY",
        entry_price: 3700,
        stop_loss: 3600,
        target: 3900,
        signal_strength: 95,
        adx: 35,
        dma: 5.71,
        volume_ratio: 2.5,
        timestamp: "2025-11-19 09:30:00"
      },
      ...
    ]
```

---

## Technical Specification

### Class: `ADXDMASignalGenerator`

```python
# signals/adx_dma_generator.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import pandas as pd
import numpy as np
import logging

@dataclass
class TradingSignal:
    """Trading signal output"""
    symbol: str
    side: str  # 'BUY' or 'SELL'
    strategy: str
    entry_price: float
    stop_loss: float
    target: float
    signal_strength: float  # 0-100
    adx: float
    dma: float
    volume_ratio: float
    timestamp: datetime
    metadata: dict

class ADXDMASignalGenerator:
    """
    Generate trading signals using ADX + DMA strategy

    Responsibilities:
    - Calculate ADX and DMA indicators
    - Filter signals by criteria
    - Score signal strength
    - Calculate stop-loss and targets
    """

    def __init__(
        self,
        adx_period: int = 14,
        ema_period: int = 20,
        dma_buy_threshold: float = 5.0,
        dma_sell_threshold: float = -5.0,
        adx_threshold: float = 25.0,
        volume_threshold: float = 1.5,
    ):
        """
        Initialize ADX+DMA Signal Generator

        Args:
            adx_period: ADX calculation period (default: 14)
            ema_period: EMA period for DMA (default: 20)
            dma_buy_threshold: DMA % for BUY signal (default: +5%)
            dma_sell_threshold: DMA % for SELL signal (default: -5%)
            adx_threshold: Minimum ADX for signals (default: 25)
            volume_threshold: Volume vs avg multiplier (default: 1.5x)
        """
        self.adx_period = adx_period
        self.ema_period = ema_period
        self.dma_buy_threshold = dma_buy_threshold
        self.dma_sell_threshold = dma_sell_threshold
        self.adx_threshold = adx_threshold
        self.volume_threshold = volume_threshold

        self.logger = logging.getLogger(__name__)

        # Components
        self.indicator_calculator = TechnicalIndicatorCalculator()
        self.support_resistance = SupportResistanceDetector()

    def generate_signals(
        self,
        watchlist: List[str],
        data_source,
        timestamp: Optional[datetime] = None,
    ) -> List[TradingSignal]:
        """
        Generate signals for watchlist

        Args:
            watchlist: List of stock symbols
            data_source: DataIngestionManager instance
            timestamp: Signal generation timestamp (default: now)

        Returns:
            List of TradingSignal objects
        """
        if timestamp is None:
            timestamp = datetime.now()

        signals = []

        for symbol in watchlist:
            try:
                # Fetch data (100 days for ADX calculation)
                result = data_source.fetch_ohlcv(
                    symbol=symbol,
                    timeframe="1day",
                    start_date=timestamp - timedelta(days=100),
                    end_date=timestamp,
                )

                if not result.success:
                    self.logger.warning(
                        f"Failed to fetch data for {symbol}: {result.error}"
                    )
                    continue

                df = result.data

                # Calculate indicators
                df = self._calculate_indicators(df)

                # Generate signal
                signal = self._generate_signal_for_symbol(
                    symbol, df, timestamp
                )

                if signal:
                    signals.append(signal)

            except Exception as e:
                self.logger.error(
                    f"Error generating signal for {symbol}: {e}"
                )

        self.logger.info(
            f"Generated {len(signals)} signals from {len(watchlist)} symbols"
        )

        return signals

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""

        # ADX
        df = self.indicator_calculator.calculate_adx(
            df, period=self.adx_period
        )

        # EMA
        df = self.indicator_calculator.calculate_ema(
            df, period=self.ema_period, column="close"
        )

        # DMA (Displacement %)
        df["dma"] = (
            (df["close"] - df[f"ema_{self.ema_period}"]) /
            df[f"ema_{self.ema_period}"]
        ) * 100

        # ATR (for stop-loss)
        df = self.indicator_calculator.calculate_atr(
            df, period=14
        )

        # Volume average
        df["volume_avg_20"] = df["volume"].rolling(20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_avg_20"]

        return df

    def _generate_signal_for_symbol(
        self,
        symbol: str,
        df: pd.DataFrame,
        timestamp: datetime,
    ) -> Optional[TradingSignal]:
        """Generate signal for a single symbol"""

        # Get latest values
        latest = df.iloc[-1]

        adx = latest["adx"]
        dma = latest["dma"]
        price = latest["close"]
        ema = latest[f"ema_{self.ema_period}"]
        volume_ratio = latest["volume_ratio"]
        atr = latest["atr"]

        # Check if we have valid data
        if pd.isna(adx) or pd.isna(dma):
            self.logger.warning(f"{symbol}: Insufficient data for indicators")
            return None

        # Apply filters
        signal_side = None

        # BUY Signal Check
        if (
            adx > self.adx_threshold and
            dma > self.dma_buy_threshold and
            price > ema and
            volume_ratio > self.volume_threshold
        ):
            signal_side = "BUY"

        # SELL Signal Check
        elif (
            adx > self.adx_threshold and
            dma < self.dma_sell_threshold and
            price < ema and
            volume_ratio > self.volume_threshold
        ):
            signal_side = "SELL"

        # No signal
        if signal_side is None:
            return None

        # Calculate signal strength
        signal_strength = self._calculate_signal_strength(
            adx, dma, volume_ratio, signal_side
        )

        # Calculate stop-loss and target
        stop_loss, target = self._calculate_stop_and_target(
            price, atr, signal_side
        )

        # Create signal
        signal = TradingSignal(
            symbol=symbol,
            side=signal_side,
            strategy="ADX+DMA",
            entry_price=price,
            stop_loss=stop_loss,
            target=target,
            signal_strength=signal_strength,
            adx=adx,
            dma=dma,
            volume_ratio=volume_ratio,
            timestamp=timestamp,
            metadata={
                "ema_20": ema,
                "atr": atr,
            },
        )

        self.logger.info(
            f"Signal: {signal_side} {symbol} @ ₹{price:.2f} "
            f"(Strength: {signal_strength:.0f}, ADX: {adx:.1f}, DMA: {dma:+.2f}%)"
        )

        return signal

    def _calculate_signal_strength(
        self,
        adx: float,
        dma: float,
        volume_ratio: float,
        side: str,
    ) -> float:
        """
        Calculate signal strength score (0-100)

        Components:
        - Base: 50
        - ADX bonus: (ADX - 25) × 2 (max +30)
        - DMA bonus: abs(DMA - threshold) × 4 (max +20)
        - Volume bonus: (volume_ratio - 1.5) × 20 (max +10)
        - Total: 0-100
        """
        score = 50  # Base score

        # ADX bonus (higher ADX = stronger trend)
        adx_bonus = min((adx - self.adx_threshold) * 2, 30)
        score += adx_bonus

        # DMA bonus (further from threshold = stronger momentum)
        if side == "BUY":
            dma_bonus = min((dma - self.dma_buy_threshold) * 4, 20)
        else:
            dma_bonus = min((abs(dma) - abs(self.dma_sell_threshold)) * 4, 20)

        score += dma_bonus

        # Volume bonus
        volume_bonus = min((volume_ratio - self.volume_threshold) * 20, 10)
        score += volume_bonus

        # Clamp to [0, 100]
        score = max(0, min(score, 100))

        return score

    def _calculate_stop_and_target(
        self,
        entry_price: float,
        atr: float,
        side: str,
    ) -> tuple[float, float]:
        """
        Calculate stop-loss and target

        Stop-Loss: 2 × ATR from entry
        Target: 2:1 reward:risk ratio

        Args:
            entry_price: Entry price
            atr: Average True Range
            side: 'BUY' or 'SELL'

        Returns:
            (stop_loss, target)
        """
        # Stop-loss at 2 ATR
        if side == "BUY":
            stop_loss = entry_price - (2 * atr)
            risk = entry_price - stop_loss
            target = entry_price + (2 * risk)  # 2:1 R:R
        else:
            stop_loss = entry_price + (2 * atr)
            risk = stop_loss - entry_price
            target = entry_price - (2 * risk)  # 2:1 R:R

        return stop_loss, target
```

### Class: `TechnicalIndicatorCalculator`

```python
# signals/technical_indicators.py
import pandas as pd
import numpy as np

class TechnicalIndicatorCalculator:
    """Calculate technical indicators"""

    def calculate_adx(
        self, df: pd.DataFrame, period: int = 14
    ) -> pd.DataFrame:
        """
        Calculate ADX (Average Directional Index)

        Steps:
        1. Calculate +DM and -DM (Directional Movement)
        2. Calculate +DI and -DI (Directional Indicators)
        3. Calculate DX (Directional Index)
        4. Smooth DX to get ADX

        Args:
            df: DataFrame with OHLC data
            period: ADX period (default: 14)

        Returns:
            DataFrame with ADX column
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Calculate True Range
        df["tr"] = self._calculate_true_range(df)

        # Calculate Directional Movement
        df["plus_dm"] = np.where(
            (high - high.shift(1)) > (low.shift(1) - low),
            np.maximum(high - high.shift(1), 0),
            0,
        )

        df["minus_dm"] = np.where(
            (low.shift(1) - low) > (high - high.shift(1)),
            np.maximum(low.shift(1) - low, 0),
            0,
        )

        # Smooth TR, +DM, -DM
        df["atr"] = df["tr"].rolling(period).mean()
        df["plus_dm_smooth"] = df["plus_dm"].rolling(period).mean()
        df["minus_dm_smooth"] = df["minus_dm"].rolling(period).mean()

        # Calculate Directional Indicators
        df["plus_di"] = 100 * (df["plus_dm_smooth"] / df["atr"])
        df["minus_di"] = 100 * (df["minus_dm_smooth"] / df["atr"])

        # Calculate DX
        df["dx"] = 100 * (
            abs(df["plus_di"] - df["minus_di"]) /
            (df["plus_di"] + df["minus_di"])
        )

        # Calculate ADX (smoothed DX)
        df["adx"] = df["dx"].rolling(period).mean()

        return df

    def _calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range"""
        high = df["high"]
        low = df["low"]
        close_prev = df["close"].shift(1)

        tr1 = high - low
        tr2 = abs(high - close_prev)
        tr3 = abs(low - close_prev)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        return tr

    def calculate_ema(
        self,
        df: pd.DataFrame,
        period: int,
        column: str = "close",
    ) -> pd.DataFrame:
        """Calculate Exponential Moving Average"""
        ema_col = f"ema_{period}"
        df[ema_col] = df[column].ewm(span=period, adjust=False).mean()
        return df

    def calculate_atr(
        self, df: pd.DataFrame, period: int = 14
    ) -> pd.DataFrame:
        """Calculate Average True Range"""
        if "tr" not in df.columns:
            df["tr"] = self._calculate_true_range(df)

        df["atr"] = df["tr"].rolling(period).mean()

        return df
```

---

## API Contracts

### Input: Generate Signals Request

```python
watchlist = [
    "RELIANCE-EQ",
    "TCS-EQ",
    "INFY-EQ",
    "HDFC-EQ",
]

signals = generator.generate_signals(
    watchlist=watchlist,
    data_source=ingestion_manager,
    timestamp=datetime(2025, 11, 19, 9, 30),
)
```

### Output: List of TradingSignal

```python
[
    TradingSignal(
        symbol="TCS-EQ",
        side="BUY",
        strategy="ADX+DMA",
        entry_price=3700.0,
        stop_loss=3600.0,
        target=3900.0,
        signal_strength=95.0,
        adx=35.0,
        dma=5.71,
        volume_ratio=2.5,
        timestamp=datetime(2025, 11, 19, 9, 30),
        metadata={"ema_20": 3500.0, "atr": 50.0},
    ),
    # ... more signals
]
```

### Integration with Position Sizing

```python
# main.py
from signals.adx_dma_generator import ADXDMASignalGenerator
from position_sizing.kelly_sizer import KellyPositionSizer

def main():
    # Generate signals
    generator = ADXDMASignalGenerator()
    signals = generator.generate_signals(watchlist, data_source)

    # Size positions
    sizer = KellyPositionSizer(...)

    for signal in signals:
        position = sizer.calculate_position_size(
            signal=signal.__dict__,
            current_capital=100000,
            peak_capital=100000,
        )

        if position.approved:
            print(f"Trade: {signal.side} {position.shares} × {signal.symbol}")
```

---

## Data Models

### TradingSignal Schema

```json
{
  "symbol": "TCS-EQ",
  "side": "BUY",
  "strategy": "ADX+DMA",
  "entry_price": 3700.0,
  "stop_loss": 3600.0,
  "target": 3900.0,
  "signal_strength": 95.0,
  "adx": 35.0,
  "dma": 5.71,
  "volume_ratio": 2.5,
  "timestamp": "2025-11-19T09:30:00",
  "metadata": {
    "ema_20": 3500.0,
    "atr": 50.0,
    "risk_per_share": 100.0,
    "reward_per_share": 200.0,
    "risk_reward_ratio": 2.0
  }
}
```

---

## Business Rules

### BR-1: BUY Signal Criteria

**Rule**: BUY when all conditions met:
1. ADX > 25 (strong trend)
2. DMA > +5% (bullish momentum)
3. Price > 20 EMA (above trend)
4. Volume > 1.5× average (confirmation)

**Implementation**:
```python
if (
    adx > 25 and
    dma > 5.0 and
    price > ema_20 and
    volume_ratio > 1.5
):
    return "BUY"
```

### BR-2: SELL Signal Criteria

**Rule**: SELL when all conditions met:
1. ADX > 25
2. DMA < -5%
3. Price < 20 EMA
4. Volume > 1.5× average

**Implementation**:
```python
if (
    adx > 25 and
    dma < -5.0 and
    price < ema_20 and
    volume_ratio > 1.5
):
    return "SELL"
```

### BR-3: Signal Strength Scoring

**Rule**: Score = Base (50) + ADX bonus + DMA bonus + Volume bonus

**Formula**:
```python
score = 50  # Base
score += min((adx - 25) * 2, 30)  # ADX bonus
score += min((dma - 5) * 4, 20)   # DMA bonus (for BUY)
score += min((volume_ratio - 1.5) * 20, 10)  # Volume bonus
score = max(0, min(score, 100))  # Clamp to [0, 100]
```

### BR-4: Stop-Loss Calculation

**Rule**: Stop-loss at 2 × ATR from entry

**Rationale**: ATR-based stops adapt to volatility

**Implementation**:
```python
stop_loss = entry_price - (2 * atr)  # For BUY
stop_loss = entry_price + (2 * atr)  # For SELL
```

### BR-5: Target Calculation

**Rule**: Target at 2:1 reward:risk ratio

**Implementation**:
```python
risk = abs(entry_price - stop_loss)
target = entry_price + (2 * risk)  # For BUY
target = entry_price - (2 * risk)  # For SELL
```

---

## Test Cases

### TC-001: Strong BUY Signal

**Test Code**:
```python
def test_strong_buy_signal():
    generator = ADXDMASignalGenerator()

    # Create mock data
    df = pd.DataFrame({
        "close": [3500] * 50 + [3700],
        "high": [3510] * 50 + [3710],
        "low": [3490] * 50 + [3690],
        "volume": [100000] * 50 + [250000],
    })

    # Calculate indicators (mocked for simplicity)
    df["adx"] = 35.0
    df["ema_20"] = 3500.0
    df["dma"] = ((3700 - 3500) / 3500) * 100  # 5.71%
    df["atr"] = 50.0
    df["volume_avg_20"] = 100000
    df["volume_ratio"] = 2.5

    signal = generator._generate_signal_for_symbol(
        symbol="TCS",
        df=df,
        timestamp=datetime.now(),
    )

    assert signal is not None
    assert signal.side == "BUY"
    assert signal.entry_price == 3700
    assert signal.signal_strength > 90
```

### TC-002: Weak ADX (No Signal)

**Test Code**:
```python
def test_weak_adx_no_signal():
    generator = ADXDMASignalGenerator()

    df = pd.DataFrame({
        "close": [2500],
        "high": [2510],
        "low": [2490],
        "volume": [150000],
        "adx": [18.0],  # Too low
        "ema_20": [2450],
        "dma": [2.04],  # Not enough
        "atr": [30],
        "volume_ratio": [2.0],
    })

    signal = generator._generate_signal_for_symbol(
        symbol="RELIANCE",
        df=df,
        timestamp=datetime.now(),
    )

    assert signal is None  # No signal due to weak ADX
```

### TC-003: Signal Strength Calculation

**Test Code**:
```python
def test_signal_strength_calculation():
    generator = ADXDMASignalGenerator()

    # Strong signal
    strength = generator._calculate_signal_strength(
        adx=35.0,
        dma=8.0,  # 3% above threshold
        volume_ratio=2.5,
        side="BUY",
    )

    # Expected:
    # Base: 50
    # ADX bonus: (35 - 25) × 2 = 20
    # DMA bonus: (8 - 5) × 4 = 12
    # Volume bonus: (2.5 - 1.5) × 20 = 20 (capped at 10)
    # Total: 50 + 20 + 12 + 10 = 92

    assert strength == pytest.approx(92, abs=1)
```

### TC-004: Stop-Loss and Target Calculation

**Test Code**:
```python
def test_stop_and_target_calculation():
    generator = ADXDMASignalGenerator()

    entry_price = 2500
    atr = 50
    side = "BUY"

    stop, target = generator._calculate_stop_and_target(
        entry_price, atr, side
    )

    # Stop: 2500 - (2 × 50) = 2400
    assert stop == 2400

    # Risk: 2500 - 2400 = 100
    # Target: 2500 + (2 × 100) = 2700
    assert target == 2700
```

### TC-005: Generate Signals for Watchlist

**Test Code**:
```python
def test_generate_signals_for_watchlist(mocker):
    generator = ADXDMASignalGenerator()

    # Mock data source
    mock_data_source = mocker.Mock()

    # Mock successful data fetch
    mock_df = pd.DataFrame({
        "close": [2500],
        "high": [2510],
        "low": [2490],
        "volume": [200000],
    })

    mock_data_source.fetch_ohlcv.return_value = DataFetchResult(
        success=True,
        data=mock_df,
        source="yahoo",
    )

    watchlist = ["RELIANCE-EQ", "TCS-EQ"]

    signals = generator.generate_signals(
        watchlist=watchlist,
        data_source=mock_data_source,
    )

    # Should attempt to fetch data for each symbol
    assert mock_data_source.fetch_ohlcv.call_count == 2

    # Signals may be 0 if conditions not met (acceptable)
    assert isinstance(signals, list)
```

---

## Edge Cases

### Edge Case 1: Insufficient Data

**Scenario**: Symbol has only 20 days of data (need 100 for ADX)

**Expected**:
- Log warning: "Insufficient data for ADX calculation"
- Skip signal generation for this symbol
- Continue with other symbols

**Implementation**:
```python
if len(df) < 100:
    logger.warning(f"{symbol}: Only {len(df)} days. Need 100+ for ADX.")
    return None
```

### Edge Case 2: ADX Exactly at Threshold

**Scenario**: ADX = 25.0 (exactly at threshold)

**Expected**:
- Include signal (>= 25)

**Implementation**:
```python
if adx >= self.adx_threshold:  # Use >= not >
    # Signal valid
```

### Edge Case 3: Extreme DMA Value

**Scenario**: DMA = +15% (very strong displacement)

**Expected**:
- Signal is valid
- Signal strength capped at 100
- Log: "Exceptional DMA: +15%"

**Implementation**:
```python
if abs(dma) > 10:
    logger.info(f"{symbol}: Exceptional DMA: {dma:+.2f}%")

score = min(score, 100)  # Cap at 100
```

### Edge Case 4: Zero Volume

**Scenario**: Volume = 0 (suspended or no trades)

**Expected**:
- Skip signal
- Log: "Zero volume, skipping"

**Implementation**:
```python
if latest["volume"] == 0:
    logger.warning(f"{symbol}: Zero volume. Skipping.")
    return None
```

### Edge Case 5: NaN Indicators

**Scenario**: ADX or DMA is NaN (calculation failed)

**Expected**:
- Skip signal
- Log error with reason

**Implementation**:
```python
if pd.isna(adx) or pd.isna(dma):
    logger.error(f"{symbol}: NaN indicators. Check data quality.")
    return None
```

---

## Performance Requirements

### PR-1: Signal Generation Speed

**Requirement**: Generate signals for 50 symbols in < 5 seconds

**Test**:
```python
def test_signal_generation_performance():
    generator = ADXDMASignalGenerator()
    watchlist = ["SYMBOL_" + str(i) for i in range(50)]

    start = time.time()
    signals = generator.generate_signals(watchlist, data_source)
    end = time.time()

    elapsed = end - start
    assert elapsed < 5.0  # < 5 seconds
```

### PR-2: Indicator Calculation Efficiency

**Requirement**: Calculate ADX for 100-day dataset in < 50ms

**Implementation**:
- Use vectorized pandas operations (avoid loops)
- Pre-calculate common values
- Cache intermediate results

---

## Dependencies

### Internal Dependencies

- **FX-001**: Data Ingestion Manager
- **FX-002**: Kelly Position Sizer (downstream consumer)
- **FX-007**: Regime Detection (optional filtering)

### External Dependencies

- **pandas**: DataFrames and calculations
- **numpy**: Numerical operations
- **ta-lib** (optional): Technical analysis library

### Python Packages

```
pandas>=2.0.0
numpy>=1.24.0
# ta-lib (optional, for faster indicator calculations)
```

---

## Implementation Checklist

- [ ] Create `signals/adx_dma_generator.py`
- [ ] Create `signals/technical_indicators.py`
- [ ] Implement ADX calculation
- [ ] Implement DMA calculation
- [ ] Implement signal filtering logic
- [ ] Implement signal strength scoring
- [ ] Implement stop-loss and target calculation
- [ ] Write 12 unit tests
- [ ] Write 3 integration tests
- [ ] Performance testing (< 5s for 50 symbols)
- [ ] Documentation
- [ ] Code review

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: FX-006 (Backtesting Engine)
