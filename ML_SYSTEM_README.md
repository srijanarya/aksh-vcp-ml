# Upper Circuit ML Prediction System

**Predict Indian stock upper circuits (5-20% surges) 15-30 minutes before the market reacts using Machine Learning.**

---

## 🚨 Current Status: Foundation Complete (20%)

**❌ System NOT ready for deployment or customers**

| Component | Status | Progress |
|-----------|--------|----------|
| Foundation (Specs + Framework) | ✅ Complete | 100% |
| Tools Library (18 utilities) | ✅ Complete | 100% |
| Skills Library (13 domain functions) | ✅ Complete | 100% |
| **Data Collection (Epic 1)** | ⏳ **NOT STARTED** | **0%** |
| Feature Engineering (Epic 2) | ⏳ Not started | 0% |
| Model Training (Epic 3) | ⏳ Not started | 0% |
| Real-Time Inference (Epic 4) | ⏳ Not started | 0% |
| Monitoring (Epic 5) | ⏳ Not started | 0% |
| **OVERALL PROGRESS** | **⏳ In Progress** | **20%** |

**Timeline to deployment**: 7-8 weeks (realistic estimate)

---

## 📖 Quick Navigation

### For Decision Makers
- 🎯 **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Current status, what's done, what's not
- 📋 **[docs/prd.md](docs/prd.md)** - Product requirements & goals
- 🏗️ **[docs/architecture.md](docs/architecture.md)** - System architecture

### For Developers
- 🚀 **[AUTONOMOUS_EXECUTION_MANIFEST.md](AUTONOMOUS_EXECUTION_MANIFEST.md)** - How to run autonomous agents
- 📚 **[docs/epics/epic-1-data-collection.md](docs/epics/epic-1-data-collection.md)** - First epic with 6 stories
- 🔧 **[tools/](tools/)** - 18 utility functions (72KB code)
- 🎓 **[skills/](skills/)** - 13 domain functions (50KB code)

### For Project Tracking
- 📊 **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Foundation completion summary
- 🗺️ **[docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md)** - Epic timeline

---

## ⚡ Quick Start

### Step 1: Verify Foundation

```bash
cd /Users/srijan/Desktop/aksh

# Check Tools library
ls -lh tools/
# Expected: 7 Python files (db_utils, rate_limiter, validation_utils, etc.)

# Check Skills library
ls -lh skills/
# Expected: 5 Python files (circuit_detector, pdf_text_extractor, etc.)

# Check documentation
ls -lh docs/
# Expected: prd.md, architecture.md, epics/epic-1-data-collection.md
```

### Step 2: Execute First Story (Data Collection Orchestrator)

```bash
# This will create the MLDataCollectorAgent
python agents/autonomous_executor.py execute-story EPIC1-S1 epic-1-data-collection

# Expected output:
# - MLDataCollectorAgent created at agents/ml/ml_data_collector.py
# - Tests created at tests/unit/test_epic1_s1.py
# - All 7 acceptance criteria passing
# - Test coverage ≥90%
```

### Step 3: Execute Remaining Epic 1 Stories

```bash
# Can run in parallel for speed
python agents/autonomous_executor.py execute-epic epic-1-data-collection --parallel

# Expected output (after 2-4 hours):
# - 5 databases created with 200K+ records
# - BSE-NSE mapping improved to ≥80%
# - Data quality checks: ≥4 of 5 passing
```

---

## 🎯 Project Goal

### The Problem

In Indian stock markets, quarterly earnings announcements often trigger **upper circuits** (5-20% price surges hitting daily limits). Traders like Srinidhi profit by buying stocks pre-announcement and selling at circuit prices.

**Current challenge**: Market reacts within minutes of BSE announcement.

**Our goal**: Predict which stocks will hit upper circuit BEFORE the market reacts (15-30 min advantage).

### The Solution

ML classification system:

```
BSE Telegram Alert
    ↓
Parse Company + PDF URL
    ↓
Extract Financials (Revenue, Profit, EPS)
    ↓
Calculate Features (25-30 metrics)
    ↓
ML Model (XGBoost/LightGBM/RF)
    ↓
Prediction: Will hit upper circuit? (YES/NO)
    ↓
Send Alert to User (<2 min total latency)
```

### Target Performance
- **F1 Score**: ≥0.70
- **Precision**: ≥70% (few false positives)
- **Recall**: ≥60% (catch most opportunities)
- **Latency**: <2 minutes end-to-end
- **Uptime**: 99.5% during market hours

---

## 🏗️ Architecture

### 3-Layer Design

```
Layer 1: Tools (18 functions)
    ↓ Reusable utilities
Layer 2: Skills (13 functions)
    ↓ Domain-specific logic
Layer 3: ML Agents (8 specialists)
    ↓ Orchestrated execution
MLMasterOrchestrator
    ↓ Coordinates everything
User
```

### 8 ML Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| **MLMasterOrchestrator** | Coordinates all operations | ✅ Code ready (250 lines) |
| **MLDataCollectorAgent** | Historical data collection | 📋 Spec ready (not executed) |
| MLFeatureEngineerAgent | Extract 25-30 features | 📋 Spec TBD |
| MLTrainingAgent | Train XGBoost/LightGBM/RF | 📋 Spec TBD |
| MLInferenceAgent | Real-time predictions | 📋 Spec TBD |
| MLMonitoringAgent | Track accuracy, drift | 📋 Spec TBD |
| MLBacktestingAgent | Validate on Q4 FY25 | 📋 Spec TBD |
| MLAlertAgent | Send Telegram alerts | 📋 Spec TBD |

### 18 Tools (Reusable Utilities)

All tools are **production-ready** (72KB, 2,030 lines):

| Category | Tools | Status |
|----------|-------|--------|
| Database | get_db_connection, execute_query, bulk_insert, create_table | ✅ Complete |
| Rate Limiting | RateLimiter, respect_rate_limit (BSE/NSE/yfinance) | ✅ Complete |
| Validation | validate_ohlc, validate_financials, validate_date_range, validate_upper_circuit | ✅ Complete |
| BhavCopy | download_bse_bhav_copy, download_nse_bhav_copy, parse_bhav_copy | ✅ Complete |
| ISIN Matching | match_by_isin, build_isin_index, validate_isin | ✅ Complete |
| Fuzzy Matching | fuzzy_match_companies, clean_company_name, find_best_matches | ✅ Complete |
| PDF | download_pdf, download_pdf_with_retry, cache_pdf, get_cached_pdf_path | ✅ Complete |

### 13 Skills (Domain Logic)

All skills are **production-ready** (50KB, 1,550 lines):

| Skill | Purpose | Status |
|-------|---------|--------|
| **circuit_detector** | Detect upper/lower circuits (PRIMARY LABEL) | ✅ Complete (400 lines) |
| **pdf_text_extractor** | Extract financials from PDFs | ✅ Complete (380 lines) |
| **technical_indicators** | RSI, MACD, Bollinger Bands | ✅ Complete (320 lines) |
| **sentiment_analyzer** | Earnings sentiment (keyword + LLM) | ✅ Complete (300 lines) |
| vcp_detector | VCP patterns (legacy) | ⚠️ Placeholder (not used for ML) |

---

## 📁 Project Structure

```
/Users/srijan/Desktop/aksh/
│
├── agents/
│   ├── ml/
│   │   ├── __init__.py
│   │   └── ml_master_orchestrator.py     ✅ 250 lines - Master coordinator
│   └── autonomous_executor.py            ✅ 600 lines - 7-phase TDD workflow
│
├── tools/                                 ✅ 72KB, 18 functions
│   ├── __init__.py
│   ├── db_utils.py                       ✅ SQLite operations
│   ├── rate_limiter.py                   ✅ Token bucket rate limiting
│   ├── validation_utils.py               ✅ Data validation
│   ├── bhav_copy_downloader.py           ✅ BSE/NSE BhavCopy
│   ├── isin_matcher.py                   ✅ BSE-NSE via ISIN
│   ├── fuzzy_name_matcher.py             ✅ Company name matching
│   └── pdf_downloader.py                 ✅ PDF download with retry
│
├── skills/                                ✅ 50KB, 13 functions
│   ├── __init__.py
│   ├── circuit_detector.py               ✅ Upper/lower circuits
│   ├── pdf_text_extractor.py             ✅ Financial extraction
│   ├── technical_indicators.py           ✅ RSI, MACD, BB
│   ├── sentiment_analyzer.py             ✅ Earnings sentiment
│   └── vcp_detector.py                   ⚠️ Placeholder
│
├── mcp_servers/
│   └── README.md                         ✅ yfinance, Telegram, BSE/NSE
│
├── docs/                                  ✅ 165KB BMAD specs
│   ├── prd.md                            ✅ 25KB - Product requirements
│   ├── architecture.md                   ✅ 45KB - System architecture
│   ├── IMPLEMENTATION_ROADMAP.md         ✅ Epic timeline
│   └── epics/
│       └── epic-1-data-collection.md     ✅ 30KB - 6 stories, 44 ACs
│
├── AUTONOMOUS_EXECUTION_MANIFEST.md      ✅ 22KB - Execution guide
├── SETUP_COMPLETE.md                     ✅ Foundation summary
├── IMPLEMENTATION_STATUS.md              ✅ 20KB - Current status
└── ML_SYSTEM_README.md                   ✅ This file
```

**Total**: 287KB code, 6,288+ lines

---

## 🚀 Execution Plan

### Epic 1: Historical Data Collection (Target: 2 weeks)

**Goal**: Collect 200K+ labeled samples (2022-2025)

```bash
# Execute all 6 stories
python agents/autonomous_executor.py execute-epic epic-1-data-collection --parallel
```

**Expected Output**:
- ✅ 5 databases created
- ✅ 200K+ samples collected
- ✅ BSE-NSE mapping: 80%+
- ✅ Data quality: 4/5 checks passing

**Stories**:
1. MLDataCollectorAgent (orchestrator)
2. UpperCircuitLabeler (label 200K+ samples)
3. BSE-NSE Mapping (33.9% → 80%)
4. Extract Financials from PDFs
5. Collect Price Data (BhavCopy)
6. Data Quality Validation

### Epic 2: Feature Engineering (Target: 1 week)

**Goal**: Extract 25-30 features per company-quarter

### Epic 3: Model Training (Target: 2 weeks)

**Goal**: Train XGBoost/LightGBM/RF with F1 ≥0.70

### Epic 4: Real-Time Inference (Target: 2 weeks)

**Goal**: Deploy inference system with <2 min latency

### Epic 5: Monitoring & Improvement (Target: 1 week)

**Goal**: Track accuracy, detect drift, auto-retrain

---

## 🎓 Key Concepts

### Upper Circuit
- Price surge of 5-20% hitting daily limit
- Trading locked at upper circuit (can't buy higher)
- Triggered by strong earnings, major announcements
- Target prediction: Will stock hit upper circuit after earnings?

### ISIN (International Securities Identification Number)
- 12-character unique ID (e.g., INE467B01029 for TCS)
- Same ISIN across BSE and NSE
- Used for BSE→NSE mapping (100% confidence)
- Example: BSE code 500570 → NSE symbol TCS via ISIN

### BhavCopy
- Daily end-of-day price CSV published by BSE/NSE
- Contains OHLCV (Open, High, Low, Close, Volume) for all stocks
- Downloaded via tools/bhav_copy_downloader.py
- Example: `EQ131124_CSV.ZIP` (BSE, Nov 13, 2024)

### TDD (Test-Driven Development)
- Write tests FIRST (RED phase - tests fail)
- Implement code (GREEN phase - tests pass)
- Refactor code (REFACTOR phase - improve quality)
- Target: ≥90% test coverage

### Checkpoint-Resume
- Save execution state after each phase
- Can resume from checkpoint if interrupted
- Critical for long-running stories (3-5 days)
- Prevents losing progress on failures

---

## 📊 Progress Tracking

### Current Metrics

| Metric | Target | Current | Gap |
|--------|--------|---------|-----|
| **Phase 1 (Foundation)** | 100% | ✅ 100% | 0% |
| **Phase 2 (Epic 1)** | 100% | ⏳ 0% | -100% |
| **Overall Progress** | 100% | 20% | -80% |
| | | | |
| Historical samples | 200,000+ | 0 | -200,000 |
| Companies with data | 11,000 | 0 | -11,000 |
| BSE-NSE mapping | 80% | 33.9% | -46.1% |
| Databases created | 5 | 0 | -5 |
| Models trained | 3 | 0 | -3 |

### Estimated Timeline

| Phase | Duration | Start Date | End Date | Status |
|-------|----------|------------|----------|--------|
| Phase 1: Foundation | Complete | Nov 1 | Nov 13 | ✅ Done |
| Phase 2: Epic 1 (Data) | 2 weeks | Nov 14 | Nov 27 | ⏳ Next |
| Phase 3: Epic 2-3 (Features & Training) | 3 weeks | Nov 28 | Dec 18 | ⏳ Pending |
| Phase 4: Epic 4-5 (Inference & Monitoring) | 3 weeks | Dec 19 | Jan 8 | ⏳ Pending |
| **TOTAL TO DEPLOYMENT** | **8 weeks** | **Nov 14** | **Jan 8** | ⏳ **20% done** |

---

## ❓ FAQ

### Can we deploy this system now and get customers?

**NO.** System is only 20% complete:
- ✅ Planning & code framework ready
- ❌ No data collected (0/200,000 samples)
- ❌ No models trained (0/3 models)
- ❌ No real-time system deployed

**Timeline to deployment**: 7-8 weeks

### What exactly is "foundation complete"?

Foundation = Plans + Framework + Utilities:
- ✅ BMAD-compliant specs (PRD, Architecture, Epic 1)
- ✅ Autonomous execution framework (AutonomousExecutor)
- ✅ 18 reusable Tools (BhavCopy, ISIN, PDF, etc.)
- ✅ 13 domain Skills (circuit detection, PDF extraction, etc.)

Think of it as having architectural blueprints, building materials, and construction tools — but the house isn't built yet.

### What's the immediate next action?

**Execute Story 1.1** (MLDataCollectorAgent):
```bash
python agents/autonomous_executor.py execute-story EPIC1-S1 epic-1-data-collection
```

This creates the data collection orchestrator that coordinates all subsequent data collection tasks.

### Why build Tools and Skills before collecting data?

**Bottom-up approach for reliability**:
1. Build tested utilities first (Tools)
2. Build domain logic on top (Skills)
3. Use Tools + Skills for data collection (Epic 1)
4. This prevents code duplication and ensures quality

### How does autonomous execution work?

**AI agents execute stories autonomously**:
1. AutonomousExecutor reads Epic markdown
2. Spawns specialist agents (DevAgent, TestAgent, ReviewAgent)
3. Agents follow TDD: Write tests → Implement → Review
4. Human reviews and approves output
5. Repeat for next story

### How long until we can onboard customers?

**Realistic estimate**: 7-8 weeks from now (January 2026)

Breakdown:
- Week 1-2: Epic 1 (data collection)
- Week 3-5: Epic 2-3 (features + training)
- Week 6-7: Epic 4-5 (inference + monitoring)
- Week 8: Production deployment

---

## 🔗 Related Systems

This ML system is part of a larger ecosystem:

1. **Earnings Collector** (Deployed at http://13.200.109.29:8001)
   - Collects quarterly earnings from BSE/NSE
   - Provides data for ML training
   - Status: ✅ Production deployed

2. **Upper Circuit ML System** (This project)
   - Predicts upper circuits using ML
   - Uses data from Earnings Collector
   - Status: ⏳ 20% complete (foundation only)

3. **VCP Trading System** (Legacy at `/Users/srijan/vcp/`)
   - 127 existing agents for VCP pattern detection
   - Provides Dexter/Vikram agent pattern
   - Status: ✅ Production (not related to ML system)

---

## 📞 Contact & Support

**Project Location**: `/Users/srijan/Desktop/aksh`
**Documentation**: [docs/](docs/)
**Status Reports**: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
**Next Milestone**: Execute Epic 1 (data collection)
**Target Deployment**: January 8, 2026 (8 weeks from Nov 13, 2025)

---

**Last Updated**: 2025-11-13 17:40 IST
**Current Phase**: Foundation Complete → Ready for Epic 1 Execution
**Overall Progress**: 20% (Foundation 100%, Implementation 0%)
**Next Action**: `python agents/autonomous_executor.py execute-story EPIC1-S1 epic-1-data-collection`
