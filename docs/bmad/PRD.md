# Portfolio Management System - Product Requirements Document

**Version**: 1.0
**Date**: November 19, 2025
**Status**: Draft
**Owner**: AI Portfolio Manager

---

## Executive Summary

### Product Vision
Build an institutional-grade adaptive portfolio management system that manages ₹1,00,000 capital with:
- **Machine Learning regime detection** to select optimal strategies
- **Kelly Criterion position sizing** for mathematically optimal bet sizing
- **Sentiment-aware trading** using news analysis
- **Professional backtesting** with realistic cost modeling
- **Test-Driven Development** ensuring code quality and reliability

### Success Metrics
- **Capital Preservation**: Never exceed 2% drawdown from peak
- **Calmar Ratio**: > 5.0 (return/max drawdown)
- **System Reliability**: 99%+ uptime during market hours
- **Code Quality**: 80%+ test coverage
- **Strategy Adaptation**: ML improves win rate over time

---

## Problem Statement

### Current State (Why Existing Solutions Fail)
1. **Retail Trading Bots**:
   - Fixed position sizing (don't adapt to performance)
   - Unrealistic backtesting (ignore costs/slippage)
   - No regime awareness (same strategy in all market conditions)
   - No sentiment integration
   - Poor code quality (no tests, brittle)

2. **Manual Trading**:
   - Emotional decisions
   - Inconsistent position sizing
   - Can't track multiple strategies simultaneously
   - Slow to adapt to changing conditions

### Gap
No system exists that combines:
- Institutional-grade risk management (Kelly Criterion)
- ML-driven regime detection & strategy selection
- Sentiment-aware position sizing
- Realistic cost modeling (Indian markets)
- Professional software engineering (TDD, modular architecture)

---

## Solution Overview

### Core Innovation: Adaptive Intelligence
The system LEARNS and ADAPTS rather than following fixed rules:

1. **Regime Detection**: ML analyzes today's market open → Predicts which strategy will work best
2. **Strategy Selection**: Allocates capital to strategies based on recent performance
3. **Sentiment Integration**: News analysis filters/adjusts trades
4. **Dynamic Risk**: Position sizes scale with profit (conservative → aggressive as winning)
5. **Continuous Learning**: After each trade, updates Kelly parameters and strategy preferences

### Architecture Philosophy
- **Test-Driven Development**: Write tests first, ensure correctness
- **Modular Design**: Each component independent and testable
- **Data-Driven**: Every decision backed by historical data
- **Cost-Aware**: Model reality (brokerage, slippage, impact cost)

---

## User Personas

### Persona 1: The AI Portfolio Manager (Primary User = The System Itself)
**Role**: Autonomous trading system
**Goals**:
- Maximize Calmar ratio (not just returns)
- Preserve capital (2% max DD)
- Learn from mistakes (RL/ML)
- Operate 24/7 during market hours

**Pain Points**:
- Must make decisions with incomplete information
- Market regimes change constantly
- Costs eat into profits
- One bad day can wipe out weeks of gains

**Needs**:
- Accurate regime detection
- Precise cost calculations
- Real-time sentiment data
- Robust backtesting before live deployment

---

### Persona 2: The Human Investor (You, the Capital Provider)
**Role**: Oversees AI, provides capital, sets constraints
**Goals**:
- Grow capital safely (2% max risk)
- Understand what system is doing
- Override when necessary
- Trust system to run autonomously

**Pain Points**:
- Can't watch markets all day
- Emotional trading led to losses in past
- Need transparency into decisions
- Want institutional-quality risk management

**Needs**:
- Daily performance reports (Telegram/email)
- Real-time dashboard (check anytime)
- Clear alerts when action needed
- Ability to pause/override system

---

## Functional Requirements

### FR-1: Regime Detection & Optimal Strategy Discovery

**Description**: ML system that predicts which trading strategy will perform best on any given day

**User Story**:
*"As the Portfolio Manager, I want to know at 9:15 AM which strategy to use today, so I allocate capital optimally."*

**Acceptance Criteria**:
1. At market open, system classifies today as one of:
   - Expansion Day (gap up + volume → use momentum)
   - Contraction Day (narrow range → use mean reversion)
   - Trending Day (strong ADX → use trend following)
   - Choppy Day (low ADX → reduce position sizes)
   - High Volatility (VIX >20 → stay defensive)

2. For each historical day (2+ years), system labels:
   - Which strategy would have made most money
   - Day features (gap %, volume ratio, VIX, sentiment)

3. ML model (Random Forest/XGBoost) trained on labeled data:
   - Input: Today's morning features
   - Output: Recommended strategy + confidence score

4. Backtesting shows:
   - Regime-aware trading outperforms single-strategy by >10%
   - Prediction accuracy >55% (better than random)

**Dependencies**: Historical OHLCV data, strategy performance database, VIX data

**Priority**: P0 (Critical)

---

### FR-2: Kelly Criterion Position Sizing

**Description**: Calculate mathematically optimal position size for each trade

**User Story**:
*"As the Portfolio Manager, I want position sizes optimized by Kelly Criterion, so I maximize long-term capital growth."*

**Acceptance Criteria**:
1. For each strategy, track:
   - Win rate (rolling 30 trades)
   - Average win %
   - Average loss %

2. Calculate Kelly fraction:
   ```
   Kelly = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
   ```

3. Use Half-Kelly (divide by 2 for safety)

4. Cap at 20% of capital (hard limit)

5. Scale with profit:
   - At ₹1L capital: Risk standard Kelly
   - At ₹1.05L (+5%): Risk 1.2× Kelly
   - At ₹1.10L (+10%): Risk 1.5× Kelly
   - At ₹1.20L (+20%): Risk 2.0× Kelly (up to 20% cap)

6. Total risk never exceeds 2% of peak capital

**Tests**:
- Unit test: Kelly calculation with known inputs
- Integration test: Position sizing end-to-end
- System test: Backtest with Kelly vs fixed sizing (Kelly wins)

**Dependencies**: Trade history database, real-time capital tracking

**Priority**: P0 (Critical)

---

### FR-3: Sentiment Integration (Trium Finance News)

**Description**: Analyze news sentiment, filter/adjust trades accordingly

**User Story**:
*"As the Portfolio Manager, I want to avoid trades when sentiment contradicts technical signals, so I improve win rate."*

**Acceptance Criteria**:
1. Fetch news for each stock from Trium Finance API:
   - Last 24 hours of news
   - Headlines + summaries

2. Analyze sentiment using FinBERT or GPT-4:
   - Score: -1 (very bearish) to +1 (very bullish)
   - Confidence: 0-1

3. Decision rules:
   - **BUY signal + bearish sentiment (<-0.3)**: Skip trade
   - **BUY signal + bullish sentiment (>0.3)**: Increase position size by 10%
   - **BUY signal + neutral sentiment**: Normal sizing

4. Backtest shows:
   - Sentiment filtering improves win rate by >5%
   - Reduces losses on "false breakouts"

**Tests**:
- Unit test: Sentiment scoring accuracy
- Integration test: Trium Finance API connection
- System test: Backtest with vs without sentiment (with wins)

**Dependencies**: Trium Finance API credentials, LLM API (GPT-4/Claude)

**Priority**: P1 (High)

---

### FR-4: Realistic Cost Modeling (Indian Markets)

**Description**: Calculate EXACT costs for every trade (no optimistic assumptions)

**User Story**:
*"As the Portfolio Manager, I want costs modeled accurately, so backtests predict live performance."*

**Acceptance Criteria**:
1. **Cost Calculator** includes ALL Indian market costs:
   - Brokerage: ₹20 per order or 0.03%, whichever higher (Angel One)
   - STT: 0.1% on sell side (equity), 0.0625% (F&O)
   - Exchange charges: 0.00325% (NSE)
   - GST: 18% on brokerage
   - SEBI charges: ₹10 per crore
   - Stamp duty: 0.015% on buy side

2. **Slippage Simulator** models realistic fills:
   - Large cap: 0.05% avg slippage
   - Mid cap: 0.10% avg slippage
   - Small cap: 0.20% avg slippage
   - Adjust for order size (>1% of daily volume = higher slippage)
   - Adjust for time of day (open/close = higher slippage)
   - Adjust for volatility (VIX-based multiplier)

3. **Impact Cost** for large orders:
   - Orders >₹5L: Add 0.05% impact cost
   - Orders >₹10L: Add 0.10% impact cost

4. Backtest compares:
   - Gross P&L (before costs)
   - Net P&L (after costs)
   - Shows: "Costs reduced return from 25% to 18%"

**Tests**:
- Unit test: Cost calculation for sample trade
- Integration test: Slippage simulation accuracy
- System test: Paper trading costs match live costs within 10%

**Dependencies**: Angel One fee schedule, historical volume data

**Priority**: P0 (Critical)

---

### FR-5: Professional Backtesting Engine

**Description**: Test strategies on 2+ years historical data with ALL costs included

**User Story**:
*"As the Portfolio Manager, I want to validate strategies historically before risking real money, so I avoid unprofitable systems."*

**Acceptance Criteria**:
1. Backtest period: January 2023 - November 2025 (2+ years)

2. For each day:
   - Generate signals (ADX+DMA, Camarilla, etc.)
   - Predict regime (expansion, contraction, etc.)
   - Select strategy based on regime
   - Calculate position size (Kelly)
   - Simulate entry (with slippage)
   - Calculate entry costs
   - Track position
   - Simulate exit when SL/target hit (with slippage)
   - Calculate exit costs
   - Record net P&L

3. Generate comprehensive report:
   - Starting capital vs Ending capital
   - Total return %
   - Max drawdown % (MUST be <2%)
   - Calmar ratio (return / max DD)
   - Win rate (after costs)
   - Average win vs average loss
   - Total costs paid (brokerage + STT + slippage)
   - Number of trades
   - By strategy breakdown

4. **Pass Criteria**:
   - Max drawdown < 2.0%
   - Calmar ratio > 5.0
   - Positive return after costs
   - Win rate > 45%
   - No single position exceeded 20%

5. If backtest fails, tune parameters and re-run until passes

**Tests**:
- Unit test: Backtest calculation logic
- Integration test: Full backtest pipeline
- System test: Compare backtest to paper trading (should match within 15%)

**Dependencies**: Historical OHLCV data (2+ years), all previous FRs

**Priority**: P0 (Critical)

---

### FR-6: 30-Day Paper Trading

**Description**: Simulate live trading with real market data before deploying capital

**User Story**:
*"As the Human Investor, I want to see the system work for 30 days with fake money, so I trust it with real capital."*

**Acceptance Criteria**:
1. Paper trading runs daily for minimum 30 consecutive days

2. Each day:
   - 8:00 AM: Generate signals using live scanners
   - 9:15 AM: Get LIVE prices from Angel One
   - 9:20 AM: "Execute" paper entries (simulate with slippage)
   - Throughout day: Monitor positions every 5 minutes
   - Exit when SL/target hit (simulate with slippage)
   - 4:00 PM: Generate daily report

3. Track virtual capital:
   - Starts at ₹1,00,000
   - Updated with each paper trade P&L
   - Track virtual peak capital
   - Calculate virtual drawdown

4. **Success Criteria** (all must pass):
   - 30 days without system crashes
   - Virtual drawdown < 1.5% at any point
   - Virtual capital is positive (any profit)
   - Win rate matches backtest within 10%
   - Costs match backtest within 10%

5. If paper trading fails, fix bugs and restart 30-day clock

6. Daily Telegram report:
   - Virtual capital, drawdown, positions
   - Trades executed today
   - P&L today

**Tests**:
- Integration test: Paper trade entry → exit flow
- System test: 30-day paper trading simulation (accelerated time)

**Dependencies**: Angel One API (live data), Telegram bot, all previous FRs

**Priority**: P0 (Critical)

---

### FR-7: Angel One Live Execution

**Description**: Place real orders via Angel One SmartAPI

**User Story**:
*"As the Portfolio Manager, I want to execute trades automatically via Angel One, so I don't miss opportunities."*

**Acceptance Criteria**:
1. Angel One authentication:
   - Use credentials from `/Users/srijan/vcp_clean_test/vcp/.env.angel`
   - Login at 8:00 AM daily
   - Handle 2FA (TOTP)

2. Order placement:
   - Bracket orders (entry + SL + target in single order)
   - Market orders for entries (fast execution)
   - Automatic SL triggers

3. Position tracking:
   - Fetch open positions from Angel One every 5 minutes
   - Calculate unrealized P&L
   - Update peak capital when new high reached

4. Error handling:
   - If order fails, retry once
   - If still fails, send alert to Telegram
   - Log all orders to database

5. Safety checks before every order:
   - Verify capital available
   - Verify drawdown < 1.8% (warning threshold)
   - Verify position won't exceed 20% of capital
   - Verify Angel One API is responding

**Tests**:
- Unit test: Order placement logic
- Integration test: Mock Angel One API, test orders
- System test: Place test order with ₹100 (verify works)

**Dependencies**: Angel One credentials, network connectivity

**Priority**: P0 (Critical)

---

### FR-8: Pyramiding into Winners

**Description**: Add to profitable positions (up to 20% total cap)

**User Story**:
*"As the Portfolio Manager, I want to add to winning trades, so I maximize profits on best setups."*

**Acceptance Criteria**:
1. Pyramid conditions:
   - Position profitable >3%
   - Stop-loss moved to breakeven
   - Price making new highs
   - Total position won't exceed 20% after pyramid

2. Pyramid sizing:
   - Add 50% of original position size
   - Calculate new average price
   - Update stop-loss to protect profits

3. Example:
   - Buy 100 TCS @ ₹3500 (₹3.5L, 10% of capital)
   - Stock moves to ₹3650 (+4.3%)
   - Add 50 shares @ ₹3650
   - New position: 150 shares, avg price ₹3550
   - Total value: ₹5.475L (15.6% of capital) ✅ Under 20%
   - Move SL to ₹3500 (breakeven on original)

4. Backtest shows:
   - Pyramiding increases Calmar ratio by >15%
   - Max drawdown still <2%

**Tests**:
- Unit test: Pyramid size calculation
- Integration test: Pyramid trade execution
- System test: Backtest with vs without pyramiding (pyramiding wins)

**Dependencies**: Position tracking, Kelly sizer, risk manager

**Priority**: P1 (High)

---

### FR-9: Reinforcement Learning Strategy Selector

**Description**: Learn which strategies/signals work best, allocate more capital to winners

**User Story**:
*"As the Portfolio Manager, I want to bet more on what's working, so capital allocation improves over time."*

**Acceptance Criteria**:
1. Track performance by:
   - Strategy type (ADX+DMA, Camarilla, etc.)
   - Signal strength bucket (70-80, 80-90, 90-100)
   - Sector (IT, Banking, Pharma, etc.)
   - Time of day (morning, afternoon)

2. For each category, track:
   - Number of trades
   - Win rate
   - Average win/loss
   - Sharpe ratio (rolling 30 days)

3. Allocate capital dynamically:
   - Best performing strategy gets 40% of new trades
   - 2nd best gets 30%
   - 3rd best gets 20%
   - Others get 10%

4. Adjust signal quality multiplier:
   - Category with 65% win rate → Use 1.3× normal position size
   - Category with 45% win rate → Use 0.7× normal position size

5. Monthly review:
   - Show which strategies won/lost
   - Show capital allocation shifts
   - Recommend strategy deprecation if consistently losing

**Tests**:
- Unit test: Performance tracking accuracy
- Integration test: Capital allocation calculation
- System test: Backtest shows RL improves over time

**Dependencies**: Trade database, performance analytics

**Priority**: P1 (High)

---

### FR-10: Monitoring & Dashboards

**Description**: Real-time visibility into system state

**User Story**:
*"As the Human Investor, I want to see portfolio status anytime, so I know system is working."*

**Acceptance Criteria**:
1. **Web Dashboard** (FastAPI + HTML):
   - URL: http://localhost:8003/portfolio
   - Auto-refreshes every 30 seconds
   - Shows:
     - Current capital, peak capital, drawdown %
     - Open positions table (symbol, entry, current, P&L, SL, days held)
     - Today's closed trades
     - Top signals not yet executed
     - Performance chart (capital over time)

2. **Telegram Alerts**:
   - Morning briefing (8:30 AM):
     - Portfolio summary
     - Today's top signals
     - Regime prediction
   - Trade alerts (real-time):
     - Entry: "Bought 100 TCS @ ₹3500"
     - Exit: "Sold 100 TCS @ ₹3600, Profit ₹8,655"
   - Risk warnings:
     - "Drawdown 1.7%, approaching limit"
   - Daily summary (4:00 PM):
     - Today's P&L
     - Open positions
     - Week's performance

3. **Email Reports** (weekly):
   - PDF with charts
   - Strategy performance breakdown
   - Kelly parameter evolution
   - RL allocation changes

**Tests**:
- Integration test: Dashboard renders correctly
- System test: Telegram alerts sent at right times

**Dependencies**: FastAPI, Telegram bot, email service

**Priority**: P1 (High)

---

## Non-Functional Requirements

### NFR-1: Performance
- **Backtest Speed**: Complete 2-year backtest in <10 minutes
- **Paper Trading Latency**: React to signals within 30 seconds
- **Live Execution Latency**: Place orders within 5 seconds of signal

### NFR-2: Reliability
- **Uptime**: 99.5% during market hours (9:15 AM - 3:30 PM IST)
- **Data Accuracy**: 100% (costs, P&L must be exact)
- **Order Success Rate**: >95% (Angel One orders execute successfully)

### NFR-3: Test Coverage
- **Unit Tests**: 90%+ code coverage
- **Integration Tests**: All critical paths covered
- **System Tests**: 5+ end-to-end scenarios
- **Continuous Integration**: All tests run on every commit

### NFR-4: Security
- **API Keys**: Stored in environment variables, never in code
- **Credentials**: Encrypted at rest
- **Logging**: No sensitive data in logs (mask API keys, passwords)

### NFR-5: Maintainability
- **Code Style**: PEP 8 compliant (Python)
- **Documentation**: Every function has docstring
- **Type Hints**: All functions have type annotations
- **Comments**: Complex logic explained inline

---

## Success Criteria (Go-Live Gate)

**System CANNOT go live with real capital until ALL criteria met**:

### Backtest Gate
- ✅ Max drawdown < 2.0% over 2 years
- ✅ Calmar ratio > 5.0
- ✅ Positive return after all costs
- ✅ Win rate > 45%
- ✅ All unit tests passing (90%+ coverage)
- ✅ All integration tests passing

### Paper Trading Gate
- ✅ 30 consecutive days without crashes
- ✅ Virtual drawdown < 1.5%
- ✅ Virtual P&L positive
- ✅ Costs match backtest within 10%
- ✅ Win rate matches backtest within 10%
- ✅ User reviews daily reports and approves

### Soft Launch Gate (₹25K)
- ✅ 2 weeks of live trading with ₹25K
- ✅ Real drawdown < 1.0%
- ✅ Real costs match paper trading within 10%
- ✅ No critical bugs
- ✅ User comfortable with system behavior

### Full Launch Gate (₹1L)
- ✅ All above gates passed
- ✅ User explicitly approves full deployment
- ✅ Emergency stop procedures tested
- ✅ Monitoring alerts working reliably

---

## Out of Scope (V1)

The following are explicitly NOT included in V1:

- ❌ Options multi-leg strategies (iron condors, spreads)
- ❌ Intraday scalping (<1 hour holds)
- ❌ Cryptocurrency trading
- ❌ International markets (US stocks, etc.)
- ❌ Automated rebalancing without human approval
- ❌ Leverage >1x (margin beyond F&O 4% limit)
- ❌ Social trading (copy others' trades)
- ❌ Mobile app (web dashboard only)

These may be considered for V2 after V1 proves successful.

---

## Timeline & Milestones

| Week | Phase | Deliverable | Gate |
|------|-------|-------------|------|
| 1 | Design | BMAD docs complete | Architecture approved |
| 2-3 | Build (TDD) | Core components with tests | Unit tests 90%+ coverage |
| 4 | Integration | Backtest engine functional | Backtest gate passed |
| 5-8 | Validation | 30-day paper trading | Paper trading gate passed |
| 9-10 | Soft Launch | ₹25K live trading | Soft launch gate passed |
| 11+ | Full Launch | ₹1L live trading | Full launch gate passed |

**Estimated go-live**: 9-11 weeks from start

---

## Risk Management

### Technical Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Angel One API downtime | Medium | High | Fallback to manual execution |
| Backtest too optimistic | High | Critical | Conservative cost assumptions, paper trading validation |
| ML model overfitting | Medium | High | Walk-forward testing, out-of-sample validation |
| Bugs in cost calculator | Medium | High | Extensive unit tests, compare to manual calculations |

### Financial Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Strategy stops working | Medium | High | RL adapts, 2% max DD prevents catastrophic loss |
| Black swan event | Low | Critical | Hard stop at 1.8% DD, close all positions |
| Slippage worse than modeled | Medium | Medium | Conservative slippage assumptions, paper trading calibration |

### Operational Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| System crash during market hours | Low | High | Auto-restart, health monitoring, alerts |
| Internet outage | Low | Medium | Mobile hotspot backup, manual execution plan |
| Human override errors | Medium | Medium | Require confirmation for all manual actions |

---

## Approval & Sign-Off

**Created By**: AI System Designer
**Reviewed By**: [User to fill]
**Approved By**: [User to fill]
**Approval Date**: [To be filled]

**Version History**:
- v1.0 (2025-11-19): Initial draft with regime detection, sentiment, TDD

---

## Next Steps

After PRD approval:
1. Create ARCHITECTURE.md (system design)
2. Create TEST_STRATEGY.md (TDD approach)
3. Create FX documents (functional specs for each component)
4. Create STORY documents (user stories with acceptance criteria)
5. Create SHORT tasks (granular implementation tasks)
6. Begin TDD implementation (write tests first!)

---

**END OF PRD**
