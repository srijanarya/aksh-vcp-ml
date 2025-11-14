# ML Upper Circuit Prediction System - Implementation Roadmap

**Project:** Blockbuster Results Predictor
**Methodology:** BMAD Method (Breakthrough Method for Agile AI-Driven Development)
**Status:** Foundation Complete - Ready for Agent Execution
**Date:** 2025-11-13

---

## ✅ Phase 1: Foundation & SpecKit Documentation (COMPLETE)

### What We Built

#### 1. BMAD-Compliant Documentation

**[docs/prd.md](prd.md)** - Product Requirements Document (25KB)
- ✅ Goals and Background Context (leverage 127 existing agents)
- ✅ 15 Functional Requirements (FR1-FR15)
- ✅ 10 Non-Functional Requirements (NFR1-NFR10)
- ✅ Technical Assumptions (Monorepo, Multi-Agent Architecture, TDD)
- ✅ 5 Epic List with goal statements
- ✅ Epic 1 expanded with 6 user stories and acceptance criteria
- ✅ Next Steps with Architect prompt

**[docs/architecture.md](architecture.md)** - System Architecture (45KB)
- ✅ High-level architecture (Modular Monolith with Agents)
- ✅ 6 Architectural patterns (Multi-Agent, Feature Store, Model Registry, CQRS, Circuit Breaker, Observer)
- ✅ Complete tech stack table (20+ technologies with versions and rationale)
- ✅ 5 Data models (historical_upper_circuits, historical_financials, price_movements, feature_store, ml_monitoring)
- ✅ 8 Component descriptions with interfaces and dependencies
- ✅ 4 Mermaid sequence diagrams (data collection, training, inference, monitoring)
- ✅ Complete SQL schemas for 5 databases
- ✅ Source tree with 60+ files mapped
- ✅ Error handling strategy and 8 critical coding rules
- ✅ Test strategy (TDD with ≥80% coverage)
- ✅ Security and deployment specifications

#### 2. Ultra-Specific Epic 1: Data Collection

**[docs/epics/epic-1-data-collection.md](epics/epic-1-data-collection.md)** - (30KB)
- ✅ **Story 1.1:** Create MLDataCollectorAgent Orchestrator (7 acceptance criteria, 3-day estimate)
- ✅ **Story 1.2:** Build UpperCircuitLabeler (7 acceptance criteria, 4-day estimate)
- ✅ **Story 1.3:** Improve BSE-NSE Mapping 33.9% → ≥80% (8 acceptance criteria, 3-day estimate)
- ✅ **Story 1.4:** Extract Historical Financials from PDFs (7 acceptance criteria, 5-day estimate)
- ✅ **Story 1.5:** Collect Historical Price Data from BhavCopy (7 acceptance criteria, 4-day estimate)
- ✅ **Story 1.6:** Validate Data Quality (8 acceptance criteria, 2-day estimate)

**Each story includes:**
- User story in proper format ("As a... I want... so that...")
- Ultra-specific acceptance criteria (7-8 per story)
- Technical specifications with method signatures
- Test file paths and coverage requirements (≥90%)
- Definition of Done checklist (7-8 items)

#### 3. Agent Architecture Foundation

**[agents/ml/__init__.py](../agents/ml/__init__.py)**
- ✅ Package initialization exporting 8 agents
- ✅ Version tracking (v1.0.0)

**[agents/ml/ml_master_orchestrator.py](../agents/ml/ml_master_orchestrator.py)** - (250 lines)
- ✅ Master-Worker pattern following Dexter/Vikram architecture
- ✅ Lazy loading of 7 specialist sub-agents (avoid circular imports)
- ✅ `orchestrate_historical_data_collection()` - Epic 1 orchestration
- ✅ `orchestrate_training_pipeline()` - Epic 3 orchestration (stub)
- ✅ `orchestrate_realtime_inference()` - Epic 4 orchestration (async daemon)
- ✅ `trigger_retraining()` - Called by monitoring agent on drift
- ✅ Circuit breaker pattern (pause after 10 consecutive failures)
- ✅ Comprehensive error handling and logging
- ✅ `get_system_status()` - Health check endpoint
- ✅ Structured JSON logging with correlation IDs

---

## 📋 Next Steps: Agent Execution (Phase 2)

### What Needs to Be Built

The foundation is complete. Now we need autonomous agents to execute the 6 stories in Epic 1.

#### Priority 1: Epic 1 Story Execution (2 weeks)

**Story 1.1: MLDataCollectorAgent** (3 days)
- [ ] TDD: Write `tests/unit/test_ml_data_collector.py` FIRST (20 test cases)
- [ ] Implement `MLDataCollectorAgent` class with 7 methods
- [ ] Implement `collect_all_data()` orchestrating 4 sub-tasks
- [ ] Create `ml_collection_status.db` with 3 tables
- [ ] Add progress reporting every 100 companies
- [ ] Add retry logic (3x exponential backoff)
- [ ] Add rate limiting (0.5s BSE, 1s yfinance)
- [ ] Add output validation before marking complete
- [ ] Integration test: Collect data for 10 companies (2022-2025)
- [ ] Achieve ≥90% unit test coverage

**Story 1.2: UpperCircuitLabeler** (4 days)
- [ ] TDD: Write `test_upper_circuit_labeler.py` FIRST
- [ ] Implement `UpperCircuitLabeler` class
- [ ] Implement `label_upper_circuits()` with dual criteria (price ≥5% AND circuit hit)
- [ ] Download and parse BhavCopy CSV files
- [ ] Create `historical_upper_circuits.db` with schema
- [ ] Handle missing data (try next 5 trading days)
- [ ] Validate class distribution (5-15% positive)
- [ ] Collect ≥200,000 labeled samples
- [ ] Integration test: Label 100 real earnings (2024 Q1)

**Story 1.3: BSENSEMapper** (3 days)
- [ ] TDD: Write `test_bse_nse_mapper.py` FIRST
- [ ] Implement `BSENSEMapper` class
- [ ] Load existing 392 mappings from `bse_nse_mapping_current.json`
- [ ] Implement ISIN-based matching (BSE BhavCopy ↔ NSE BhavCopy)
- [ ] Implement fuzzy name matching (fuzzywuzzy ≥90% threshold)
- [ ] Generate `mapping_validation_top1000.csv` for manual review
- [ ] Store final mapping in JSON and SQLite
- [ ] Achieve ≥80% mapping coverage (≥4,400/5,500 companies)
- [ ] Log unmapped companies to `unmapped_companies.csv`

**Story 1.4: FinancialExtractor** (5 days)
- [ ] TDD: Write `test_financial_extractor.py` FIRST
- [ ] Implement `FinancialExtractor` class
- [ ] Reuse existing `indian_pdf_extractor.py` via importable function
- [ ] Query `earnings_calendar.db` for 2022-2025 announcements
- [ ] Download PDFs to `/tmp/earnings_pdfs_cache/`
- [ ] Extract: Revenue, PAT, EPS, OPM, NPM
- [ ] Create `historical_financials.db` with schema
- [ ] Achieve ≥80% extraction success rate
- [ ] Log failures to `extraction_failures.csv`
- [ ] Validate data quality (4 checks)

**Story 1.5: PriceCollector** (4 days)
- [ ] TDD: Write `test_price_collector.py` FIRST
- [ ] Implement `PriceCollector` class
- [ ] Download BSE BhavCopy CSV files (960 trading days)
- [ ] Download NSE BhavCopy CSV files
- [ ] Parse and store in `price_movements.db`
- [ ] Use yfinance as fallback for gaps
- [ ] Achieve ≥95% data completeness per company
- [ ] Validate OHLC relationships and data quality
- [ ] Create indexes for fast querying

**Story 1.6: DataQualityValidator** (2 days)
- [ ] TDD: Write `test_data_quality_validator.py` FIRST
- [ ] Implement `DataQualityValidator` class
- [ ] Check 1: ≥200,000 labeled samples
- [ ] Check 2: 5-15% class distribution
- [ ] Check 3: ≥80% financial data coverage
- [ ] Check 4: ≥95% price data completeness
- [ ] Check 5: ≥80% BSE-NSE mapping coverage
- [ ] Generate comprehensive validation report
- [ ] Provide actionable remediation steps

#### Priority 2: Epic 2-5 Story Creation (1 week)

- [ ] Create `docs/epics/epic-2-feature-engineering.md` (7 stories)
- [ ] Create `docs/epics/epic-3-model-training.md` (7 stories)
- [ ] Create `docs/epics/epic-4-inference-deployment.md` (7 stories)
- [ ] Create `docs/epics/epic-5-monitoring-improvement.md` (7 stories)

#### Priority 3: Tools & Skills Library (1 week)

**Tools (Reusable Functions):**
- [ ] `tools/bhav_copy_downloader.py` - Download/parse BSE/NSE BhavCopy
- [ ] `tools/pdf_downloader.py` - Download PDFs with retry/caching
- [ ] `tools/isin_matcher.py` - ISIN-based BSE→NSE mapping
- [ ] `tools/fuzzy_name_matcher.py` - Company name fuzzy matching
- [ ] `tools/rate_limiter.py` - Token bucket rate limiting
- [ ] `tools/db_utils.py` - SQLite connection helpers
- [ ] `tools/validation_utils.py` - Data quality validation functions

**Skills (Domain-Specific Logic):**
- [ ] `skills/pdf_financial_extraction.py` - Wrapper around indian_pdf_extractor
- [ ] `skills/sentiment_analysis.py` - FinBERT for management commentary
- [ ] `skills/vcp_integration.py` - Integrate with existing vcp_detector.py
- [ ] `skills/technical_indicators.py` - RSI, MA, volume spike calculations
- [ ] `skills/circuit_detection.py` - Upper/lower circuit identification logic

#### Priority 4: Test Infrastructure (3 days)

- [ ] Create `tests/conftest.py` - pytest fixtures
- [ ] Create `tests/unit/` structure (6 test files for Epic 1)
- [ ] Create `tests/integration/` structure (3 test files)
- [ ] Create `tests/e2e/` structure (3 test files)
- [ ] Create `tests/fixtures/` - Sample PDFs, BhavCopy CSVs, test data
- [ ] Setup pytest.ini with coverage configuration
- [ ] Setup CI/CD: `.github/workflows/ci.yml`

---

## 🎯 Success Metrics

### Phase 1 (Foundation) - ACHIEVED ✅

- [x] PRD.md created following BMAD template (25KB)
- [x] Architecture.md created following BMAD template (45KB)
- [x] Epic 1 created with 6 ultra-specific stories (30KB)
- [x] MLMasterOrchestrator created with orchestration logic (250 lines)
- [x] Agent package structure created

### Phase 2 (Epic 1 Execution) - IN PROGRESS

Target: Complete by 2025-11-27 (2 weeks)

- [ ] All 6 stories in Epic 1 meet Definition of Done
- [ ] ≥90% unit test coverage across all agents
- [ ] Integration tests passing: Full collection for 100 companies
- [ ] Data quality validation: ≥4 of 5 checks passing
- [ ] Performance: Complete 11,000 companies in <7 days
- [ ] Deliverables exist:
  - [ ] `ml_data_collector.py` (1,000+ lines)
  - [ ] `historical_upper_circuits.db` (≥200K samples)
  - [ ] `historical_financials.db` (≥80K quarterly records)
  - [ ] `price_movements.db` (≥10M daily records)
  - [ ] `bse_nse_mapping.json` (≥4,400 mappings, 80%+ coverage)
  - [ ] `data_quality_validation_report.txt`

### Phase 3-6 (Epics 2-5) - PLANNED

Target: Complete by 2026-01-15 (6 weeks)

- [ ] Feature engineering: 25-30 features extracted for 200K samples
- [ ] Model training: F1 ≥0.70, Precision ≥70%, Recall ≥60%
- [ ] Real-time inference: <2 min latency (BSE alert → prediction)
- [ ] Monitoring: Accuracy tracking, drift detection, auto-retraining
- [ ] Production deployment: 99.5% uptime during market hours

---

## 🛠️ How to Execute (Developer Guide)

### For AI Agents

Each story in `docs/epics/epic-1-data-collection.md` is self-contained with:
1. **User story** - Understand the "why"
2. **Acceptance criteria** - Testable requirements (7-8 per story)
3. **Technical specifications** - Method signatures, dependencies
4. **Test requirements** - ≥90% coverage, specific test cases
5. **Definition of Done** - 7-8 checklist items

**Execution Pattern (TDD):**
```bash
# Step 1: Read story acceptance criteria
cat docs/epics/epic-1-data-collection.md | grep "Story 1.1" -A 100

# Step 2: Write tests FIRST
code tests/unit/test_ml_data_collector.py
# Write 20 test cases covering all 7 acceptance criteria

# Step 3: Run tests (all should fail initially - RED)
pytest tests/unit/test_ml_data_collector.py -v

# Step 4: Implement agent to make tests pass (GREEN)
code agents/ml/ml_data_collector.py

# Step 5: Refactor for quality (REFACTOR)
ruff check agents/ml/ml_data_collector.py
mypy agents/ml/ml_data_collector.py

# Step 6: Verify Definition of Done
pytest tests/unit/test_ml_data_collector.py --cov=agents.ml.ml_data_collector --cov-report=term-missing
# Must achieve ≥90% coverage
```

### For Human Developers

1. **Start with Story 1.1** (MLDataCollectorAgent Orchestrator)
2. Follow TDD strictly: Write tests → Implement → Refactor
3. Each story is 2-5 days of focused work
4. Integration tests after every story completion
5. Epic 1 complete = Ready for Epic 2 (Feature Engineering)

---

## 📚 Key Architecture Decisions

### 1. BMAD Method Adoption ✅

**Why:** Structured, AI-friendly documentation with ultra-specific acceptance criteria enables autonomous agent execution without ambiguity.

**Evidence:**
- PRD.md follows official BMAD template from `/Users/srijan/Indian Social media app/.bmad-core/templates/prd-tmpl.yaml`
- Architecture.md follows official BMAD template from `architecture-tmpl.yaml`
- Epic stories use proper user story format with numbered acceptance criteria

### 2. Multi-Agent Architecture (Dexter/Vikram Pattern) ✅

**Why:** Existing 127 agents already use this pattern. New ML agents integrate seamlessly.

**Evidence:**
- MLMasterOrchestrator coordinates 7 specialist sub-agents
- Lazy loading prevents circular imports
- Circuit breaker pattern for fault tolerance
- Follows existing pattern from `/Users/srijan/vcp/agents/dexter/agent.py`

### 3. TDD with ≥80% Coverage ✅

**Why:** ML systems have subtle bugs. Tests catch issues before production. Requirement from PRD NFR7.

**Evidence:**
- Every story requires tests written FIRST
- Coverage targets: ≥90% unit, ≥85% integration, ≥80% E2E
- Definition of Done includes "Unit tests achieving ≥90% coverage"

### 4. SQLite for MVP, PostgreSQL Later ✅

**Why:** No cloud budget (PRD constraint). SQLite handles <20GB data easily. Migrate when scale requires.

**Evidence:**
- 5 SQLite databases: historical_upper_circuits, historical_financials, price_movements, feature_store, ml_monitoring
- Architecture.md Tech Stack: "SQLite 3.40.0 - Serverless, <20GB data fits easily, no deployment overhead"

### 5. Feature Store Pattern ✅

**Why:** Feature engineering is expensive (30s per sample). Store 200K pre-computed features for fast training.

**Evidence:**
- `feature_store.db` caches all 27 features per sample
- Ensures train-serve consistency (same features in training and inference)
- Architecture.md: "Feature Store Pattern - Centralized feature_store.db caching engineered features"

---

## 📊 Project Statistics

### Documentation Created

| File | Lines | Size | Status |
|------|-------|------|--------|
| docs/prd.md | 296 | 25KB | ✅ Complete |
| docs/architecture.md | 652 | 45KB | ✅ Complete |
| docs/epics/epic-1-data-collection.md | 430 | 30KB | ✅ Complete |
| agents/ml/__init__.py | 38 | 1.5KB | ✅ Complete |
| agents/ml/ml_master_orchestrator.py | 250 | 12KB | ✅ Complete |
| **Total** | **1,666** | **113.5KB** | **Phase 1 Done** |

### Work Remaining

| Epic | Stories | Est. Days | Status |
|------|---------|-----------|--------|
| Epic 1: Data Collection | 6 | 21 days | 📋 Ready for Dev |
| Epic 2: Feature Engineering | 7 (TBD) | 14 days | 📝 Needs Stories |
| Epic 3: Model Training | 7 (TBD) | 14 days | 📝 Needs Stories |
| Epic 4: Inference Deployment | 7 (TBD) | 10 days | 📝 Needs Stories |
| Epic 5: Monitoring & Improvement | 7 (TBD) | 10 days | 📝 Needs Stories |
| **Total** | **34** | **69 days** | **33% Planned** |

### Agent Implementation Status

| Agent | Status | Lines (Est.) | Test Coverage |
|-------|--------|--------------|---------------|
| MLMasterOrchestrator | ✅ Done | 250 | TBD |
| MLDataCollectorAgent | 🔄 Story 1.1 | 1,000+ | TBD |
| MLFeatureEngineerAgent | 📋 Epic 2 | 800+ | TBD |
| MLTrainingAgent | 📋 Epic 3 | 600+ | TBD |
| MLInferenceAgent | 📋 Epic 4 | 500+ | TBD |
| MLMonitoringAgent | 📋 Epic 5 | 400+ | TBD |
| MLBacktestingAgent | 📋 Epic 5 | 300+ | TBD |
| MLAlertAgent | 📋 Epic 4 | 200+ | TBD |
| **Total** | **12.5% Done** | **4,050+** | **Target: ≥80%** |

---

## 🚀 Ready to Execute

**Phase 1 (Foundation) is 100% complete.** We now have:

1. ✅ BMAD-compliant PRD with 15 functional requirements, 5 epics
2. ✅ BMAD-compliant Architecture with 8 agents, 5 databases, 6 patterns
3. ✅ Ultra-specific Epic 1 with 6 stories, 47 acceptance criteria total
4. ✅ MLMasterOrchestrator with orchestration logic and circuit breaker
5. ✅ Agent package structure ready for 7 sub-agents

**Next Immediate Action:** Start Story 1.1 execution

```bash
# Autonomous agent execution (recommended):
python agents/ml/ml_master_orchestrator.py --execute-story EPIC1-S1

# OR Manual developer execution:
# 1. Read: docs/epics/epic-1-data-collection.md (Story 1.1)
# 2. Write: tests/unit/test_ml_data_collector.py (TDD)
# 3. Implement: agents/ml/ml_data_collector.py
# 4. Verify: pytest --cov=agents.ml.ml_data_collector
```

---

**Last Updated:** 2025-11-13 21:30 IST
**Methodology:** BMAD Method v4
**Agent Architecture:** Dexter/Vikram Pattern
**Total Doc Size:** 113.5KB across 5 files