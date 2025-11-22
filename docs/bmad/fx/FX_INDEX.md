# FX Document Index

**Project**: BMAD Portfolio Management System
**Purpose**: Functional Specifications for all components
**Created**: November 19, 2025

---

## Completed FX Documents

### ✅ FX-002: Kelly Criterion Position Sizing
**File**: [FX-002_KELLY_POSITION_SIZING.md](FX-002_KELLY_POSITION_SIZING.md)
**Priority**: CRITICAL
**Lines**: 1,800+
**Status**: Complete

**Covers**:
- Kelly fraction calculation
- Half-Kelly safety
- Profit-based scaling (1.0× to 2.0×)
- 20% equity cap, 4% F&O cap
- 2% total risk enforcement
- Strategy performance tracking
- Complete test cases

---

### ✅ FX-004: Indian Market Cost Calculator
**File**: [FX-004_INDIAN_MARKET_COSTS.md](FX-004_INDIAN_MARKET_COSTS.md)
**Priority**: CRITICAL
**Lines**: 1,400+
**Status**: Complete

**Covers**:
- All 6 cost components (brokerage, STT, GST, stamp duty, exchange, SEBI)
- Equity delivery vs intraday
- F&O costs
- Round-trip calculations
- Validation against real statements
- Complete test cases

---

### ✅ FX-005: Slippage Simulator
**File**: [FX-005_SLIPPAGE_SIMULATOR.md](FX-005_SLIPPAGE_SIMULATOR.md)
**Priority**: CRITICAL
**Lines**: 1,200+
**Status**: Complete

**Covers**:
- Liquidity-based slippage (ADV tiers)
- Order size impact (% of ADT)
- Volatility adjustment (VIX)
- Time-of-day multipliers
- Market vs limit order handling
- Calibration process
- Complete test cases

---

### ✅ FX-007: Regime Detection System
**File**: [FX-007_REGIME_DETECTION.md](FX-007_REGIME_DETECTION.md)
**Priority**: HIGH
**Lines**: 1,400+
**Status**: Complete

**Covers**:
- 5 regime types (expansion, contraction, trending, choppy, volatile)
- 7 morning features (gap, volume, VIX, ADX, sentiment, global cues, ATR)
- ML model (Random Forest/XGBoost)
- Training process (label historical days)
- Strategy mapping per regime
- Weekly retraining
- Complete test cases

---

### ✅ FX-008: Sentiment Analyzer
**File**: [FX-008_SENTIMENT_ANALYZER.md](FX-008_SENTIMENT_ANALYZER.md)
**Priority**: MEDIUM
**Lines**: 1,100+
**Status**: Complete

**Covers**:
- Trium Finance API integration
- LLM sentiment scoring (GPT-4/Claude)
- Recency weighting (exponential decay)
- Source credibility weighting
- Position adjustment (±10%)
- Caching (1-hour TTL)
- Complete test cases

---

## Pending FX Documents

### ⏳ FX-001: Data Ingestion Layer
**Priority**: HIGH
**Components**:
- Angel One API client
- Yahoo Finance fallback
- Data validation
- Cache management

---

### ⏳ FX-003: Signal Generation (ADX+DMA)
**Priority**: HIGH
**Components**:
- ADX calculation
- 3-DMA calculation
- Entry/exit conditions
- Signal strength scoring

---

### ⏳ FX-006: Backtesting Engine
**Priority**: CRITICAL
**Components**:
- Historical data replay
- Realistic execution (costs + slippage)
- Performance metrics
- Trade logging

---

### ⏳ FX-009: Paper Trading Engine
**Priority**: CRITICAL
**Components**:
- Virtual execution
- Real-time signal generation
- PnL tracking
- Validation criteria (30-day)

---

### ⏳ FX-010: Order Executor (Angel One)
**Priority**: CRITICAL
**Components**:
- Angel One SmartAPI integration
- Order placement
- Position tracking
- Error handling

---

## Total Documentation

**Completed**: 5 FX documents (~6,900 lines)
**Pending**: 5 FX documents (estimated ~7,000 lines)
**Total**: 10 FX documents (~14,000 lines when complete)

---

## Next Steps

1. ✅ Complete FX documents (5/10 done)
2. ⏳ Create STORY documents (User Stories)
3. ⏳ Create SHORT tasks (Granular implementation)
4. ⏳ Initialize test suite structure
5. ⏳ Begin TDD implementation

---

**Last Updated**: November 19, 2025
**Status**: In Progress
