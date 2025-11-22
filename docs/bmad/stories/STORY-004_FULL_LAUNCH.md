# STORY-004: Full Launch (₹1,00,000)

**Epic**: Portfolio Management System
**Story Points**: 13
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Not Started

---

## User Story

**As** the Portfolio Manager
**I want** to trade with full ₹1,00,000 capital
**So that** I can achieve target returns with proper risk management

---

## Background

**Prerequisites**:
✅ Backtest validation passed (STORY-001)
✅ Paper trading validated (STORY-002)
✅ Soft launch successful (STORY-003)

**Full Launch = Operating at Scale**:
- Full ₹1L capital deployed
- Production-grade monitoring
- 2% max drawdown strictly enforced
- Daily performance tracking
- Weekly reviews

---

## Acceptance Criteria

### AC-1: Fund Account with ₹1,00,000

**Given** soft launch successful
**When** I transfer full ₹1L to Angel One
**Then** total capital = ₹1,00,000

---

### AC-2: Configure System for ₹1L

**Configuration**:
- Initial capital: ₹1,00,000
- Max position (20%): ₹20,000
- Max F&O (4%): ₹4,000
- Max total risk (2%): ₹2,000
- Peak capital: ₹1,00,000 (updated daily)

---

### AC-3: Enforce 2% Max Drawdown

**Given** peak capital = ₹1,10,000
**When** current capital = ₹1,08,000 (-1.82%)
**Then**:
- System continues trading normally
- Monitor closely

**When** current capital = ₹1,07,800 (-2%)
**Then**:
- **HALT ALL NEW TRADES**
- Close existing positions gradually
- Activate defensive mode
- Alert user immediately

---

### AC-4: Daily Monitoring

**Every Trading Day**:
1. Pre-market health check
2. Signal generation (9:30 AM)
3. Order execution
4. Position monitoring (every 5 min)
5. End-of-day reconciliation
6. Daily report (Telegram)

---

### AC-5: Weekly Review

**Every Monday**:
1. Calculate weekly performance
2. Update Kelly fractions (based on last 100 trades)
3. Review strategy performance
4. Adjust parameters if needed
5. Generate weekly report

---

### AC-6: Monthly Performance Report

**Every Month End**:
- Total return vs target (15-20% annual)
- Max drawdown vs limit (2%)
- Sharpe ratio
- Win rate vs backtest
- Trade analysis
- Cost breakdown (actual vs estimated)
- Action items for next month

---

## Expected Performance

### Monthly Targets

| Metric | Target | Acceptable | Red Flag |
|--------|--------|------------|----------|
| Return | +1.5% | +1.0% | < 0% |
| Max DD | < 1.5% | < 2.0% | > 2.0% |
| Win Rate | 55% | 50% | < 45% |
| Sharpe | > 2.0 | > 1.5 | < 1.0 |

### Annual Targets

- Total return: 15-20%
- Max drawdown: < 2%
- Sharpe ratio: > 2.0
- Trades: 100-150
- Win rate: 55%

---

## Risk Management

### Position Sizing

**Example with ₹1L capital**:
- Signal: BUY TCS @ ₹3,700
- Kelly: 0.14 (14% of capital)
- Position value: ₹1,00,000 × 0.14 = ₹14,000
- Shares: ₹14,000 / ₹3,700 = 3.78 → 3 shares
- Actual position: 3 × ₹3,700 = ₹11,100
- Stop-loss: ₹3,600 (3% risk)
- Risk: 3 × ₹100 = ₹300
- Risk as % of capital: ₹300 / ₹1,00,000 = 0.3% ✅

### Drawdown Response

| Drawdown | Action |
|----------|--------|
| 0-1% | Normal operation |
| 1-1.5% | Monitor closely, reduce position sizes 20% |
| 1.5-2% | Reduce position sizes 50%, stop new trades if risky |
| 2%+ | **HALT trading, close positions, investigate** |

---

## Monitoring & Alerts

### Real-Time Alerts (Telegram)

**Critical**:
- Max drawdown approaching 2%
- Order execution failures
- System errors
- Kill switch activation

**Important**:
- Daily PnL summary
- Stop-loss hits
- Target hits
- Large winning/losing trades

**Informational**:
- Orders placed
- Orders filled
- Weekly performance

---

## Definition of Done

- [ ] Angel One account funded with ₹1,00,000
- [ ] System configured for ₹1L capital
- [ ] First month of trading complete
- [ ] Max drawdown < 2% maintained
- [ ] Daily reports sent every day
- [ ] Weekly reviews documented
- [ ] Monthly performance report generated
- [ ] User satisfied with results
- [ ] Ready for long-term operation

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: STORY-005 (Kelly Implementation)
