# SHORTS Index - Granular Implementation Tasks

**Project**: BMAD Portfolio Management System
**Created**: November 19, 2025
**Purpose**: Break down FX and STORY documents into small, testable implementation tasks

---

## Overview

SHORTS are granular, test-first implementation tasks extracted from FX and STORY documents.

**SHORT Task Structure**:
- **Estimated effort**: 2-8 hours
- **Test coverage**: ≥95%
- **Acceptance criteria**: Clear, testable
- **Dependencies**: Explicit
- **Implementation checklist**: Step-by-step

**TDD Approach**:
1. Write tests FIRST (based on acceptance criteria)
2. Run tests (they should FAIL)
3. Implement minimum code to pass tests
4. Refactor
5. Verify all tests pass
6. Document

---

## SHORTS Breakdown by FX

### FX-001: Data Ingestion (15 tasks)

- **SHORT-001**: Angel One Authentication & Token Management
- **SHORT-002**: Angel One OHLCV Data Fetcher
- **SHORT-003**: Yahoo Finance Historical Data Fetcher
- **SHORT-004**: OHLCV Data Validator
- **SHORT-005**: Corporate Action Handler (Splits, Bonuses)
- **SHORT-006**: SQLite Data Cache Implementation
- **SHORT-007**: Data Source Fallback Mechanism
- **SHORT-008**: Rate Limiter for API Calls
- **SHORT-009**: Symbol Token Lookup Service
- **SHORT-010**: Multi-Timeframe Data Fetcher
- SHORT-011: Data Gap Detection & Filling
- SHORT-012: Real-Time WebSocket Data Stream
- SHORT-013: Batch Symbol Data Loader
- SHORT-014: Data Quality Metrics Dashboard
- SHORT-015: Historical Data Backfill Utility

### FX-002: Kelly Position Sizing (8 tasks)

- SHORT-016: Strategy Performance Tracker
- SHORT-017: Kelly Fraction Calculator
- SHORT-018: Half-Kelly Implementation
- SHORT-019: Profit-Based Kelly Scaling
- SHORT-020: Position Cap Enforcer (20% equity, 4% F&O)
- SHORT-021: Total Risk Constraint Validator
- SHORT-022: Weekly Kelly Fraction Updater
- SHORT-023: Sentiment-Based Kelly Adjuster

### FX-003: Signal Generation (10 tasks)

- SHORT-024: ADX Calculator (14-period)
- SHORT-025: EMA Calculator (20-period)
- SHORT-026: DMA Calculator (Displacement %)
- SHORT-027: ATR Calculator (for stop-loss)
- SHORT-028: Signal Filter (ADX + DMA thresholds)
- SHORT-029: Signal Strength Scorer
- SHORT-030: Volume Confirmation Checker
- SHORT-031: Support/Resistance Detector
- SHORT-032: Stop-Loss Calculator (ATR-based)
- SHORT-033: Target Calculator (2:1 R:R)

### FX-004: Cost Calculator (3 tasks)

- SHORT-034: Equity Delivery Cost Calculator
- SHORT-035: Intraday Cost Calculator
- SHORT-036: F&O Cost Calculator

### FX-005: Slippage Simulator (3 tasks)

- SHORT-037: Spread-Based Slippage Model
- SHORT-038: Liquidity-Based Slippage Model
- SHORT-039: Slippage Aggregator

### FX-006: Backtesting Engine (12 tasks)

- SHORT-040: Historical Data Loader
- SHORT-041: Daily Simulator Loop
- SHORT-042: Point-in-Time Signal Generator
- SHORT-043: Virtual Order Executor
- SHORT-044: Portfolio Simulator (Track Positions)
- SHORT-045: Stop-Loss/Target Exit Checker
- SHORT-046: Equity Curve Tracker
- SHORT-047: Performance Metrics Calculator
- SHORT-048: Sharpe Ratio Calculator
- SHORT-049: Max Drawdown Calculator
- SHORT-050: Trade Log Exporter
- SHORT-051: Backtest Results Visualizer

### FX-007: Regime Detection (4 tasks)

- SHORT-052: Volatility Calculator
- SHORT-053: Trend Detector (ADX-based)
- SHORT-054: Market Regime Classifier
- SHORT-055: Regime-Based Strategy Selector

### FX-008: Sentiment Analyzer (3 tasks)

- SHORT-056: News Fetcher (MoneyControl, ET)
- SHORT-057: Sentiment Scoring (LLM-based)
- SHORT-058: Sentiment Aggregator

### FX-009: Paper Trading (8 tasks)

- SHORT-059: Virtual Account Manager
- SHORT-060: Real-Time Data Feed Connector
- SHORT-061: Virtual Order Executor
- SHORT-062: Position Monitor (Live)
- SHORT-063: Daily Reconciliation
- SHORT-064: Telegram Notifier
- SHORT-065: Paper Trading Report Generator
- SHORT-066: 30-Day Validation Checker

### FX-010: Order Executor (7 tasks)

- SHORT-067: Angel One Login & Auth
- SHORT-068: Order Validator
- SHORT-069: Order Placer (LIMIT orders)
- SHORT-070: Order Status Tracker
- SHORT-071: Order Canceller
- SHORT-072: Kill Switch Implementation
- SHORT-073: Audit Logger

---

## SHORTS Breakdown by STORY

### STORY-001: Backtest Validation (5 tasks)

- SHORT-074: Backtest Configuration
- SHORT-075: Run 1-Year Backtest
- SHORT-076: Validate Performance Metrics
- SHORT-077: Compare to Benchmark
- SHORT-078: Generate Backtest Report

### STORY-002: Paper Trading (5 tasks)

- SHORT-079: Initialize Paper Account
- SHORT-080: Run Daily Trading Cycle
- SHORT-081: Monitor Positions Real-Time
- SHORT-082: Track 30-Day Performance
- SHORT-083: Validate vs Backtest

### STORY-003: Soft Launch (5 tasks)

- SHORT-084: Fund Angel One with ₹25K
- SHORT-085: Configure System for ₹25K
- SHORT-086: Place First Live Order
- SHORT-087: Monitor 1-Week Performance
- SHORT-088: Go/No-Go Decision

### STORY-004: Full Launch (4 tasks)

- SHORT-089: Fund Account with ₹1L
- SHORT-090: Configure System for ₹1L
- SHORT-091: Run Production Trading
- SHORT-092: Generate Monthly Reports

### STORY-005: Kelly Implementation (3 tasks)

- SHORT-093: Implement Kelly Calculator
- SHORT-094: Implement Profit Scaling
- SHORT-095: Implement Weekly Kelly Update

### STORY-006: Drawdown Protection (4 tasks)

- SHORT-096: Implement Peak Capital Tracker
- SHORT-097: Implement Drawdown Calculator
- SHORT-098: Implement Trading Halt at 2%
- SHORT-099: Implement Recovery Mode

---

## SHORT Task Template

Each SHORT task follows this structure:

```markdown
# SHORT-XXX: Task Name

**Parent**: FX-YYY or STORY-ZZZ
**Estimated Effort**: X hours
**Priority**: HIGH/MEDIUM/LOW

## Objective

[What this task accomplishes]

## Acceptance Criteria

- [ ] AC-1: [Specific, testable criterion]
- [ ] AC-2: [Specific, testable criterion]
- [ ] AC-3: [Specific, testable criterion]

## Test Cases (Write FIRST)

### TC-1: [Test name]
```python
def test_xxx():
    # Given
    # When
    # Then
    assert ...
```

## Implementation Checklist

- [ ] Write all test cases
- [ ] Run tests (should FAIL)
- [ ] Implement code
- [ ] Run tests (should PASS)
- [ ] Refactor
- [ ] Code coverage ≥ 95%
- [ ] Documentation
- [ ] Code review

## Dependencies

- SHORT-AAA (must complete first)
- SHORT-BBB (optional)

## Definition of Done

- [ ] All tests passing
- [ ] Code coverage ≥ 95%
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Integrated with system
```

---

## Total SHORTS Summary

| Category | Count |
|----------|-------|
| FX-001 (Data) | 15 |
| FX-002 (Kelly) | 8 |
| FX-003 (Signals) | 10 |
| FX-004 (Costs) | 3 |
| FX-005 (Slippage) | 3 |
| FX-006 (Backtest) | 12 |
| FX-007 (Regime) | 4 |
| FX-008 (Sentiment) | 3 |
| FX-009 (Paper) | 8 |
| FX-010 (Executor) | 7 |
| STORY-001 | 5 |
| STORY-002 | 5 |
| STORY-003 | 5 |
| STORY-004 | 4 |
| STORY-005 | 3 |
| STORY-006 | 4 |
| **TOTAL** | **99 tasks** |

---

## Implementation Priority

### Phase 1: Foundation (25 tasks)
1. SHORT-001 to SHORT-010 (Data ingestion)
2. SHORT-024 to SHORT-033 (Signal generation)
3. SHORT-034 to SHORT-039 (Costs & slippage)

### Phase 2: Validation (20 tasks)
1. SHORT-040 to SHORT-051 (Backtesting)
2. SHORT-074 to SHORT-078 (Backtest validation)
3. SHORT-016 to SHORT-023 (Kelly sizing)

### Phase 3: Paper Trading (15 tasks)
1. SHORT-059 to SHORT-066 (Paper trading engine)
2. SHORT-079 to SHORT-083 (Paper validation)

### Phase 4: Live Trading (15 tasks)
1. SHORT-067 to SHORT-073 (Order executor)
2. SHORT-084 to SHORT-088 (Soft launch)
3. SHORT-089 to SHORT-092 (Full launch)

### Phase 5: Enhancements (24 tasks)
1. SHORT-052 to SHORT-058 (Regime & sentiment)
2. SHORT-093 to SHORT-099 (Kelly & drawdown)

---

## Progress Tracking

- **Total tasks**: 99
- **Completed**: 0
- **In progress**: 0
- **Not started**: 99

---

**Document Status**: ✅ Complete
**Last Updated**: November 19, 2025
**Next**: Begin SHORT-001 implementation
