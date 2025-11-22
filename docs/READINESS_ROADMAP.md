# Portfolio Management System - Readiness Roadmap

**From Current State → Production Trading with ₹1,00,000**

**Current Status**: 10/15 Angel One auth tests passing (67%)
**Goal**: Live trading with 2% max drawdown protection
**Timeline**: 9-11 weeks to go-live

---

## 🎯 What "Ready" Means

### Financial Readiness
✅ ₹1,00,000 capital available
✅ Prepared to lose up to 2% (₹2,000) in worst case
✅ No emotional attachment to the money
✅ Understand this is high-risk

### Technical Readiness
⏳ **190+ tests passing** (100% pass rate)
⏳ **Backtest shows**: Win rate ≥40%, Calmar ≥2.0, Max DD <10%
⏳ **30-day paper trading**: Matches backtest ±10%, Max DD <2%
⏳ **Soft launch (₹25K)**: 1 week with no issues

### Mental Readiness
- ✅ Accept that losses will happen
- ✅ Trust the system (don't override it emotionally)
- ✅ Monitor but don't micromanage
- ✅ Follow the 6 validation gates strictly

---

## 📋 Phase-by-Phase Roadmap

### **PHASE 1: Fix & Complete Implementation** (Weeks 1-4)

#### Week 1: Complete SHORT-001 (Angel One Auth)
**Current**: 10/15 tests passing

**Tasks**:
1. Fix 5 failing tests (authentication mocking issues)
2. Get to 15/15 tests passing (100%)
3. Code coverage: 100% for angel_one_client.py

**How to do it**:
```bash
# Fix each failing test one by one
python3 -m pytest tests/unit/test_angel_one_auth.py::TestAngelOneAuthentication::test_authenticate_success -v --tb=short

# After fixing, verify all pass
python3 -m pytest tests/unit/test_angel_one_auth.py -v --cov=src/data/angel_one_client --cov-fail-under=100
```

**Definition of Done**:
- [ ] All 15 tests passing
- [ ] 100% code coverage
- [ ] Can authenticate with real Angel One API
- [ ] Integration test passes (manual run)

---

#### Week 2: Data Ingestion & Signal Generation (SHORT-002 to SHORT-010)

**Implement** (TDD - tests first):
1. Market data fetching (Angel One + Yahoo Finance fallback)
2. ADX calculation (Wilder's smoothing)
3. 3-DMA calculation (50/100/200 periods)
4. Signal generation (BUY when close > all DMAs + ADX >20)
5. Signal strength scoring (0-100)

**Tests Required**: ~50 tests
**Coverage Target**: 95%+

**How to do it**:
```bash
# For each component:
# 1. Write tests FIRST
vim tests/unit/test_signal_generator.py

# 2. Run (watch fail)
pytest tests/unit/test_signal_generator.py -v

# 3. Implement
vim src/signals/adx_dma_scanner.py

# 4. Run (watch pass)
pytest tests/unit/test_signal_generator.py -v --cov=src/signals
```

**Definition of Done**:
- [ ] Can fetch live market data
- [ ] Can calculate ADX correctly (verify against TA-Lib)
- [ ] Can generate BUY/SELL signals
- [ ] Signals match manual calculations

---

#### Week 3: Position Sizing & Risk Management (SHORT-011 to SHORT-020)

**Implement** (TDD):
1. Kelly Criterion calculator
2. Cost calculator (all 6 Indian market costs)
3. Slippage simulator
4. Risk manager (2% max DD enforcement)
5. Position caps (20% equity, 4% F&O)

**Tests Required**: ~40 tests
**Coverage Target**: 100% (critical components)

**How to verify**:
```bash
# Kelly sizer MUST have 100% coverage
pytest tests/unit/test_kelly_sizer.py -v --cov=src/position_sizing/kelly_sizer --cov-fail-under=100

# Manually verify calculations:
# - Kelly = (0.55 * 0.05 - 0.45 * 0.03) / 0.05 = 0.28
# - Half-Kelly = 0.14
# - At ₹1L: Position = ₹14,000
```

**Definition of Done**:
- [ ] Kelly calculations match manual math
- [ ] Costs match real brokerage statements (±₹1)
- [ ] Risk manager prevents exceeding 2% DD
- [ ] 100% coverage on critical components

---

#### Week 4: Backtesting Engine (SHORT-021 to SHORT-030)

**Implement** (TDD):
1. Historical data loader
2. Signal generation on historical data
3. Position sizing with Kelly
4. Realistic cost application
5. Realistic slippage application
6. PnL tracking
7. Metrics calculation (Win rate, Calmar, Sharpe, Max DD)

**Tests Required**: ~30 tests

**Definition of Done**:
- [ ] Can backtest 2 years of data
- [ ] Costs applied to every trade
- [ ] Slippage applied to every trade
- [ ] Metrics calculated correctly
- [ ] Trade log exported to CSV

---

### **PHASE 2: Backtest Validation** (Week 5)

#### Run 2-Year Backtest

**Period**: January 2023 - December 2024
**Symbols**: NSE-500 (or Nifty 50 for faster testing)

**Command**:
```bash
python3 -m src.backtesting.backtest_engine \
    --start-date 2023-01-01 \
    --end-date 2024-12-31 \
    --initial-capital 100000 \
    --strategy ADX_DMA \
    --output backtest_results.csv
```

**Success Criteria** (from STORY-001):
- ✅ Win rate ≥ 40%
- ✅ Calmar ratio ≥ 2.0
- ✅ Max drawdown < 10%
- ✅ Final capital > ₹1.2L (+20%)
- ✅ Costs realistic (validate against 10 real brokerage statements)

**If Backtest FAILS**:
- Don't proceed to paper trading
- Analyze why (strategy issue? Cost too high? Slippage too aggressive?)
- Iterate on strategy parameters
- Re-test until criteria met

**How to validate manually**:
```python
# Pick 10 random trades from backtest_results.csv
# Manually calculate:
# 1. Entry/exit with slippage
# 2. All costs (brokerage, STT, GST, stamp duty, exchange, SEBI)
# 3. Net PnL
# 4. Compare to backtest result

# Difference should be < ₹5 per trade
```

---

### **PHASE 3: Paper Trading** (Weeks 6-10, ~30 trading days)

#### Setup Paper Trading Engine (SHORT-031 to SHORT-040)

**Implement**:
1. Virtual capital tracking
2. Real-time signal generation (at 9:30 AM daily)
3. Virtual order execution (with costs + slippage)
4. Position tracking
5. Stop-loss monitoring
6. Daily reconciliation
7. Telegram alerts

**How it runs**:
```bash
# Start paper trading (runs as daemon)
python3 -m src.paper_trading.engine --capital 100000 --max-dd 0.02

# Check status
python3 -m src.paper_trading.status

# View today's trades
python3 -m src.paper_trading.report --date 2025-11-20
```

#### Daily Workflow (30 Days)

**Every trading day at 9:00 AM**:
1. System fetches overnight news → Calculates sentiment
2. System predicts regime (expansion, trending, etc.)
3. System selects optimal strategy

**At 9:30 AM**:
1. System generates signals (ADX+DMA)
2. System calculates position sizes (Kelly + sentiment)
3. System checks risk limits (2% max DD)
4. System executes VIRTUAL orders (no real money)

**Throughout the day**:
1. System monitors stop-losses
2. System monitors targets
3. System updates unrealized PnL

**At 3:30 PM**:
1. System reconciles day's trades
2. System calculates daily PnL
3. System sends Telegram report:
```
📊 Paper Trading Report - Nov 20, 2025

Capital: ₹1,01,200 (+1.2%)
Daily PnL: +₹500
Max DD from peak: 0.8%

Trades Today:
- BUY RELIANCE @ ₹2,503 (10 shares) ✅
- SELL TCS @ ₹3,890 (8 shares, +₹320) ✅

Open Positions: 3
Total Risk: ₹1,800 (1.8% of peak)

Status: ✅ All systems normal
```

#### Paper Trading Success Criteria (from STORY-002)

After 30 consecutive trading days:

✅ **Max drawdown < 2%** from peak (HARD GATE)
✅ **Win rate within ±5%** of backtest
✅ **Returns within ±10%** of backtest prediction
✅ **All stop-losses executed** correctly
✅ **Daily reports sent** every day
✅ **Zero crashes** or system failures

**If Paper Trading FAILS**:
- Don't proceed to live trading
- Analyze discrepancies (backtest vs paper)
- Fix issues
- **RESTART 30-day clock** (yes, you must do full 30 days again)

**How to validate**:
```python
# After 30 days, compare:
backtest_return = 5.2%  # From backtest for same period
paper_return = 4.8%     # From paper trading

difference = abs(5.2 - 4.8) = 0.4%
tolerance = 5.2 * 0.10 = 0.52%

assert difference < tolerance  # ✅ PASS

# If this fails, something is wrong with:
# - Cost calculation
# - Slippage modeling
# - Signal generation
# - Position sizing
```

---

### **PHASE 4: Soft Launch** (Week 11)

#### Start Trading with ₹25,000 (NOT full ₹1L yet)

**Why only ₹25K**:
- Test with real money but limited risk
- Max loss = 2% of ₹25K = ₹500 (acceptable)
- Final validation before full capital

**Setup** (SHORT-041 to SHORT-050):
1. Connect to Angel One API (LIVE mode, not paper)
2. Deploy to server (runs 24/7)
3. Setup monitoring (health checks, alerts)
4. Setup kill switch (emergency stop)

**Command**:
```bash
# Deploy to production
python3 -m src.deployment.deploy \
    --capital 25000 \
    --max-dd 0.02 \
    --mode LIVE \
    --confirm "I understand this uses real money"

# Monitor
python3 -m src.monitoring.dashboard
```

#### Soft Launch Success Criteria (Week 11)

**Duration**: 5-7 trading days
**Capital**: ₹25,000

✅ **Max drawdown < 2%** (₹500 max loss)
✅ **All orders execute** correctly (no failed orders)
✅ **Stop-losses work** (test with small loss)
✅ **Telegram alerts work**
✅ **No manual intervention** needed
✅ **Daily review** shows system behaving as expected

**Daily Checklist**:
```
Day 1: ✅ System started, placed 2 orders, both filled
Day 2: ✅ 1 stop-loss hit (-₹120), executed correctly
Day 3: ✅ 1 target hit (+₹200), system working
Day 4: ✅ No trades today (no signals), system idle correctly
Day 5: ✅ 2 trades, 1 win, 1 small loss, DD at 1.2%
Day 6: ✅ Capital at ₹25,180 (+0.7%), all good
Day 7: ✅ Week complete, max DD was 1.4%, PASS ✅
```

**If Soft Launch FAILS**:
- IMMEDIATELY stop trading
- Withdraw remaining capital
- Debug issues
- Go back to paper trading
- Don't proceed to full launch

---

### **PHASE 5: Full Launch** (Week 12+)

#### Deploy Full ₹1,00,000 Capital

**Prerequisites** (ALL must be met):
- ✅ Backtest passed (Win rate ≥40%, Calmar ≥2.0, Max DD <10%)
- ✅ Paper trading passed (30 days, Max DD <2%)
- ✅ Soft launch passed (₹25K, 1 week, no issues)
- ✅ User approval (you consciously decide to proceed)

**Command**:
```bash
# Full launch
python3 -m src.deployment.deploy \
    --capital 100000 \
    --max-dd 0.02 \
    --mode LIVE \
    --confirm "I understand the risks and have validated the system"
```

#### Ongoing Monitoring

**Daily** (Automated):
- Telegram reports at 4:00 PM
- Email if Max DD > 1.5%
- SMS alert if Max DD > 1.9%

**Weekly** (Manual Review):
- Review all trades
- Check win rate vs backtest
- Check if regime detection is working
- Check if sentiment is adding value

**Monthly** (Performance Review):
- Calculate Sharpe, Calmar ratios
- Compare to Nifty 50 buy & hold
- Analyze what's working, what's not
- Retrain regime detector with new data

**Emergency Stop Conditions**:
```python
if max_drawdown >= 0.02:  # 2% hit
    system.emergency_stop()
    send_alert("EMERGENCY: Max drawdown reached. Trading stopped.")

if consecutive_losses >= 10:
    system.pause()
    send_alert("WARNING: 10 consecutive losses. Review required.")

if system_error_count >= 3:
    system.emergency_stop()
    send_alert("CRITICAL: Multiple system errors. Manual intervention required.")
```

---

## 🎓 Skills You Need to Develop

### 1. **Python Proficiency** (You likely have this)
- Understanding of classes, decorators, async/await
- Familiarity with pandas, numpy
- pytest for testing

### 2. **Financial Markets Knowledge** (You have 4.5 years)
✅ ADX, Moving Averages (you know this)
✅ Risk management (position sizing, stop-losses)
⏳ **Need to learn**:
   - How to interpret backtest results critically
   - When to trust the system vs when to pause
   - How to handle losing streaks emotionally

### 3. **Test-Driven Development** (Learning now)
✅ Write tests first
✅ Run tests (RED phase)
✅ Implement code (GREEN phase)
✅ Refactor
⏳ **Practice needed**: Do this for all 99 SHORT tasks

### 4. **DevOps / Deployment** (Will learn in Weeks 10-11)
- Running Python scripts as daemons
- Server monitoring
- Log analysis
- Alert setup (Telegram, Email, SMS)

### 5. **Emotional Discipline** (Most Important)
- **Trust the system**: Don't override signals because you "feel" market will go down
- **Accept losses**: 40-60% win rate means 40-60% of trades lose
- **Don't revenge trade**: If system says "no signal", don't manually place trades
- **Follow the gates**: If paper trading fails, DON'T skip to live trading

---

## 🚨 Common Failure Modes & How to Avoid

### Failure Mode 1: **Skipping Validation Gates**
**Symptom**: "Backtest looks good, let me just try with ₹10K live"
**Why it fails**: Backtest might have bugs, costs might be wrong
**Solution**: Follow ALL 6 gates. No shortcuts.

### Failure Mode 2: **Overriding the System**
**Symptom**: "System says SELL but I think market will rally, let me hold"
**Why it fails**: Destroys backtested performance, introduces emotions
**Solution**: If you don't trust the system, don't trade. Fix the system instead.

### Failure Mode 3: **Not Accepting Losses**
**Symptom**: "I'm down ₹1,000 already, let me increase position to recover"
**Why it fails**: Violates Kelly, violates risk management, path to ruin
**Solution**: Accept that 2% drawdown (₹2,000 loss) is possible. Mentally prepared for it.

### Failure Mode 4: **Ignoring System Errors**
**Symptom**: "Order failed, but market is moving, let me place manually"
**Why it fails**: Manual errors, no audit trail, breaks risk management
**Solution**: If system has errors, STOP trading, fix errors, resume.

### Failure Mode 5: **Tweaking Mid-Flight**
**Symptom**: "I'll change stop-loss from 3% to 5% just for this trade"
**Why it fails**: Invalidates backtesting, changes risk profile
**Solution**: Changes require full re-backtest, re-paper trade, re-soft launch.

---

## ✅ Readiness Checklist

### Before Paper Trading
- [ ] All 190+ tests passing
- [ ] 100% coverage on critical components (Kelly, Risk, Costs)
- [ ] Backtest shows Win rate ≥40%, Calmar ≥2.0, Max DD <10%
- [ ] Manual verification of 10 trades (costs match real statements)
- [ ] Comfortable with Python and pytest
- [ ] Comfortable with financial concepts (ADX, Kelly, Drawdown)

### Before Soft Launch
- [ ] 30 consecutive days of paper trading passed
- [ ] Max DD stayed below 2% during paper trading
- [ ] Paper trading results match backtest (±10%)
- [ ] All system monitoring set up (Telegram, alerts)
- [ ] Emergency stop tested and working
- [ ] Mentally prepared to lose ₹500 (2% of ₹25K)

### Before Full Launch
- [ ] Soft launch (₹25K) passed with no issues
- [ ] All gates passed (6/6)
- [ ] User conscious decision to proceed
- [ ] ₹1,00,000 capital ready
- [ ] Mentally prepared to lose ₹2,000 (2% of ₹1L)
- [ ] Understand this is HIGH RISK
- [ ] Have reviewed and accepted all risks

---

## 📅 Realistic Timeline

| Phase | Duration | Completion | Ready for Next? |
|-------|----------|------------|-----------------|
| **Documentation** | 2 days | ✅ 100% | Yes |
| **Implementation** (Weeks 1-4) | 4 weeks | ⏳ 5% | Not yet |
| **Backtest Validation** (Week 5) | 1 week | ⏳ 0% | Not yet |
| **Paper Trading** (Weeks 6-10) | ~30 days | ⏳ 0% | Not yet |
| **Soft Launch** (Week 11) | 1 week | ⏳ 0% | Not yet |
| **Full Launch** (Week 12) | Go live | ⏳ 0% | Not yet |

**Earliest Go-Live**: 11-12 weeks from now (early February 2026)

**More Realistic**: 14-16 weeks (late February / early March 2026)
- Allows for debugging, re-testing, learning

---

## 🎯 Next Immediate Steps (This Week)

### Step 1: Fix Remaining Angel One Auth Tests
```bash
# Work on each failing test
python3 -m pytest tests/unit/test_angel_one_auth.py::TestAngelOneAuthentication::test_authenticate_success -v --tb=short
```

### Step 2: Get to 15/15 Tests Passing
- Fix mocking issues
- Fix TOTP padding issue
- Get 100% coverage

### Step 3: Celebrate First TDD Component Complete
- SHORT-001 done = 1/99 tasks complete (1%)
- You've proven TDD works
- Continue with SHORT-002, SHORT-003, etc.

---

## 💡 Key Insight: The 6 Gates Protect You

Each gate is a safety checkpoint:

1. **Pre-commit**: Code quality (prevents bugs)
2. **Pull request**: Review (catches errors)
3. **Backtest**: Strategy validation (proves edge exists)
4. **Paper trading**: Real-world validation (proves system works)
5. **Soft launch**: Real money validation (proves execution works)
6. **Full launch**: Conscious decision (you're ready mentally)

**Skipping even ONE gate drastically increases failure probability.**

---

## 🎉 You Become Ready By...

1. **Completing implementation** (all 99 SHORT tasks with TDD)
2. **Passing backtest** (proves strategy works historically)
3. **Passing paper trading** (proves system works in real-time)
4. **Passing soft launch** (proves you can handle real money)
5. **Making conscious decision** (mentally prepared for risk)

**There are no shortcuts.**

But if you follow this roadmap, in 11-14 weeks you'll have:
- ✅ Production-tested trading system
- ✅ Validated strategy
- ✅ Risk management proven to work
- ✅ ₹1,00,000 deployed with confidence

---

**Created**: November 19, 2025
**Current Progress**: 1/99 tasks (SHORT-001 at 67%)
**Est. Completion**: February/March 2026
**Status**: PHASE 1 - Implementation In Progress
