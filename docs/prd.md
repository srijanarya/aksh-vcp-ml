# Blockbuster Results Predictor Product Requirements Document (PRD)

<!-- Powered by BMAD™ Core -->

## Goals and Background Context

### Goals

- Predict which Indian stocks will hit upper circuit (5-20% surge) after quarterly earnings announcements
- Beat market participants like Srinidhi by 15-30 minutes in identifying blockbuster results
- Achieve ≥70% precision and ≥60% recall in upper circuit prediction
- Process ~11,000 NSE/BSE companies in real-time with <2 minute latency from earnings announcement to prediction
- Build ML classification system leveraging 2-3 years of historical data (200K-300K labeled samples)
- Replace rule-based Vikram's 7-criteria scoring system with ML-powered pattern recognition

### Background Context

Srinidhi consistently posts "blockbuster results" that lead to upper circuit movements (5-20% surge) the next trading day. Currently, there is NO automated system to identify these opportunities before Srinidhi or other market participants. The existing rule-based blockbuster detector (Vikram's 7-criteria) uses fixed thresholds and cannot learn from historical patterns.

The project has 127 existing agents in production (Dexter/Vikram multi-agent architecture) that provide foundational infrastructure for financial research, earnings data collection, VCP pattern detection, and PDF extraction. This ML system will leverage 80% of existing infrastructure and build 20% new ML-specific components to create a comprehensive upper circuit prediction platform.

Real-time BSE Telegram alerts (@BseAlertsTelegram_bot) deliver sub-3-second notifications, enabling timely analysis. Screener.in was evaluated but found to have stale data (2-3 day delay) and mapping issues, making it unsuitable for real-time trading decisions.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-13 | 1.0.0 | Initial PRD creation using BMAD Method | VCP Financial Research Team |

## Requirements

### Functional

**FR1:** System must collect historical data (2-3 years) including earnings announcements, financial metrics, price movements, and upper circuit labels for ~11,000 NSE/BSE companies

**FR2:** System must map BSE codes to NSE symbols with ≥80% coverage (up from current 33.9%) using ISIN-based matching via BhavCopy files

**FR3:** System must extract 25-30 features per company-quarter including: fundamental (8 features: Revenue/PAT/EPS QoQ, YoY, margins, debt-to-equity), technical (6 features: RSI, volume spike, previous circuits, price momentum, market cap, MA distance), qualitative (4 features: new orders, guidance tone, sentiment, exceptional items), seasonality (3 features: Q1/Q2/Q3 historical performance), VCP pattern (3 features: detected, stage, contraction depth), market context (3 features: Nifty change, sector change, breadth)

**FR4:** System must train ML classification models (XGBoost, LightGBM, Random Forest) to predict upper circuit probability (0-100%) with F1 ≥0.70, Precision ≥70%, Recall ≥60%

**FR5:** System must handle class imbalance (upper circuits are 5-10% of samples) using SMOTE oversampling and class weights

**FR6:** System must provide real-time inference pipeline: BSE alert received → PDF extracted (<30s) → Features engineered (<30s) → Prediction generated (<10s) → Alert sent (<10s) = Total <2 minutes

**FR7:** System must use indian_pdf_extractor.py (existing 80%+ success rate) for extracting quarterly financial data from BSE PDFs

**FR8:** System must send alerts only for high-confidence predictions (probability ≥70%) via Telegram to reduce noise

**FR9:** System must provide SHAP-based explainability showing top 5 features driving each prediction (e.g., "High confidence due to: EPS +45%, Volume spike 3x, Positive guidance")

**FR10:** System must track actual price movements (1 day, 3 days, 7 days post-prediction) and calculate weekly precision/recall metrics

**FR11:** System must detect feature drift and auto-trigger retraining when accuracy drops ≥5%

**FR12:** System must auto-deploy new models if F1 improves by ≥2% after retraining

**FR13:** System must provide backtesting capability to validate models on historical quarters (e.g., Q4 FY25)

**FR14:** System must integrate with existing 127 agents including intelligent_earnings_collector.py, blockbuster_detector.py, vcp_detector.py, earnings_analyzer.py for feature engineering

**FR15:** System must store training data in historical_upper_circuits.db, historical_financials.db, price_movements.db, and feature_store.db

### Non Functional

**NFR1:** System must maintain 99.5% uptime during Indian market hours (9:15 AM - 3:30 PM IST)

**NFR2:** System must achieve <2 minute end-to-end latency (BSE alert → prediction → alert)

**NFR3:** System must process 100 earnings announcements per day and handle 10 concurrent PDF extractions

**NFR4:** System must train models on 200K samples in <4 hours

**NFR5:** System must use <4GB memory per agent, <2 CPU cores per agent, <20GB total disk for databases

**NFR6:** System must maintain ≥80% test coverage with unit/integration/E2E tests passing at 100%

**NFR7:** System must follow TDD (Test-Driven Development) approach with tests written before code

**NFR8:** System must use SpecKit methodology with PRD.md, architecture.md, epic/story structure

**NFR9:** System must version models semantically (v1.0.0, v1.1.0) and track experiments in MLflow

**NFR10:** System must never log PII or sensitive financial data, validate all inputs, and handle errors gracefully

## User Interface Design Goals

**Note:** This is a backend ML system with minimal UI requirements. Primary interface is Telegram alerts for traders.

### Overall UX Vision

Traders receive real-time Telegram alerts with clear signal strength, explainability, and actionable insights. Alerts are formatted for mobile viewing with key metrics highlighted.

### Key Interaction Paradigms

- **Push notifications:** System sends alerts to traders, no pull required
- **Confidence levels:** Clear visual hierarchy (90-100% "Very High", 70-89% "High", 50-69% "Medium")
- **Explainability:** Top 5 features inline in alert for quick understanding

### Core Screens and Views

- **Telegram Alert Message:** Company name, confidence %, top 5 features, historical performance
- **Dashboard (Optional Future):** Real-time monitoring of predictions vs actuals, accuracy metrics over time, top performing features

### Accessibility

Not applicable for Telegram text alerts

### Branding

No specific branding requirements - focus on clarity and readability in mobile Telegram client

### Target Device and Platforms

Mobile-first Telegram notifications (iOS and Android), optional web dashboard for monitoring

## Technical Assumptions

### Repository Structure

**Monorepo** - The existing VCP project structure is a monorepo containing 127 agents. All ML components will be added as new agents within `/Users/srijan/Desktop/aksh/agents/` directory.

### Service Architecture

**Modular Monolith with Agent Architecture** - The system follows a multi-agent pattern where specialized agents (MLDataCollectorAgent, MLFeatureEngineerAgent, MLTrainingAgent, MLInferenceAgent, MLMonitoringAgent, MLBacktestingAgent, MLAlertAgent, MLMasterOrchestrator) coordinate via a master orchestrator. Each agent is independently testable and can scale horizontally if needed.

### Testing Requirements

**Full Testing Pyramid with TDD**:
- **Unit tests:** ≥90% coverage, test all agent logic, feature engineering functions, model evaluation metrics
- **Integration tests:** ≥85% coverage, test data pipelines (collection → feature store), training pipelines (features → model artifacts), inference pipelines (PDF → prediction)
- **E2E tests:** ≥80% coverage, test full system on Q4 FY25 historical data, real-time simulation (BSE alert → prediction → alert), accuracy tracking and retraining workflows

### Additional Technical Assumptions and Requests

- **Python 3.10+:** All ML agents use Python for compatibility with scikit-learn, XGBoost, LightGBM ecosystems
- **yfinance API:** For fetching historical price/volume data (free, no API key required)
- **BhavCopy Data:** BSE and NSE publish daily BhavCopy CSV files for historical price movements
- **SQLite Databases:** For development and initial production (migrate to PostgreSQL if scale requires)
- **pytest Framework:** For all testing with fixtures and parameterized tests
- **MLflow:** For experiment tracking, model versioning, and artifact storage
- **SHAP Library:** For model explainability and feature importance
- **Optuna:** For hyperparameter tuning (100 trials per model)
- **SMOTE (imbalanced-learn):** For handling class imbalance in training
- **CI/CD GitHub Actions:** Run tests on every PR, block merge if tests fail, auto-deploy to production on main merge
- **Telegram Bot API:** For sending real-time alerts (use existing bot token)
- **Existing Agent Reuse:** Leverage indian_pdf_extractor.py (80%+ PDF extraction), intelligent_earnings_collector.py (3-phase research), blockbuster_detector.py (baseline comparison), vcp_detector.py (VCP features), earnings_analyzer.py (earnings quality features)
- **No Cloud Budget:** Development on single machine, optimize for local execution (<4GB RAM, <2 CPU cores per agent)

## Epic List

**Epic 1: Historical Data Collection & Preparation**
**Goal:** Build the foundation for ML training by collecting 2-3 years of labeled data (200K-300K samples) for ~11,000 NSE/BSE companies, achieving ≥80% BSE-NSE mapping and establishing data quality validation pipelines.

**Epic 2: Feature Engineering Pipeline**
**Goal:** Create MLFeatureEngineerAgent to extract 25-30 features per company-quarter, integrating with 127 existing agents for fundamental, technical, qualitative, seasonality, VCP, and market context features, and populate feature_store.db with validated, complete feature vectors.

**Epic 3: ML Model Training & Evaluation**
**Goal:** Train XGBoost/LightGBM/Random Forest classification models with hyperparameter tuning, achieve F1 ≥0.70 (Precision ≥70%, Recall ≥60%), handle class imbalance via SMOTE, and establish model versioning with MLflow.

**Epic 4: Real-Time Inference & Alert System**
**Goal:** Deploy MLInferenceAgent for <2 minute latency predictions, integrate with BSE Telegram bot, provide SHAP explainability, and send alerts only for ≥70% confidence predictions.

**Epic 5: Monitoring, Backtesting & Continuous Improvement**
**Goal:** Build MLMonitoringAgent to track accuracy over time, detect feature drift, auto-trigger retraining when accuracy drops ≥5%, validate models via backtesting on Q4 FY25, and establish continuous learning loop.

## Epic 1: Historical Data Collection & Preparation

**Expanded Goal:** Establish the ML training foundation by orchestrating multi-source data collection across 2-3 years (2022-2025) for all NSE/BSE listed companies (~11,000). The epic delivers labeled datasets identifying which stocks hit upper circuit after earnings announcements, fundamental financial metrics extracted from quarterly PDFs, price movement data from BhavCopy files, and improved BSE-NSE mapping from 33.9% to ≥80% coverage. Data quality validation ensures ≥90% complete feature vectors before training begins.

### Story 1.1: Create MLDataCollectorAgent Orchestrator

**As a** ML System,
**I want** an orchestrator agent to coordinate all historical data collection tasks,
**so that** I can systematically collect 200K-300K labeled samples across 3 years without manual intervention.

#### Acceptance Criteria

1. MLDataCollectorAgent class created at `/Users/srijan/Desktop/aksh/agents/ml_data_collector.py` with initialization, configuration loading from `.env`, and logging setup
2. Agent coordinates 4 sub-collection tasks: (1) Upper circuit labeling, (2) BSE-NSE mapping, (3) Financial data extraction, (4) Price movement collection
3. Agent tracks progress in SQLite database `ml_collection_status.db` with tables for collection_runs, company_status, error_logs
4. Agent provides progress reporting (X/11,000 companies processed, Y% complete) with estimated time remaining
5. Agent handles failures gracefully: retry 3x with exponential backoff, log errors, continue with next company
6. Agent respects rate limits: 0.5s between BSE requests, 1s between yfinance API calls
7. Agent validates outputs before marking complete: check for null values, date range coverage, schema compliance

### Story 1.2: Build UpperCircuitLabeler to Identify Training Labels

**As a** ML Model,
**I want** labeled data identifying which earnings announcements led to upper circuits,
**so that** I can learn patterns that predict future upper circuit movements.

#### Acceptance Criteria

1. UpperCircuitLabeler class created in ml_data_collector.py with method `label_upper_circuits(company_bse_code: str, date_range: tuple) -> List[UpperCircuitLabel]`
2. For each earnings announcement date, fetch next-day price data from BhavCopy CSV files
3. Label as upper circuit (Y=1) if: (a) Price increase ≥5%, AND (b) Stock hit upper circuit limit (check volume traded vs delivery volume ratio, or upper_circuit flag in BhavCopy)
4. Label as no circuit (Y=0) otherwise
5. Store labels in `historical_upper_circuits.db` with schema: `(bse_code, nse_symbol, earnings_date, next_day_date, price_change_pct, hit_circuit, label)`
6. Collect 200,000+ labeled samples across 2-3 years
7. Validate class distribution: expect 5-15% upper circuits (Y=1), log warning if outside range

### Story 1.3: Improve BSE-NSE Mapping from 33.9% to ≥80%

**As a** Price Data Fetcher,
**I want** accurate BSE-to-NSE symbol mapping for ≥80% of companies,
**so that** I can fetch price/volume data via yfinance for training and inference.

#### Acceptance Criteria

1. Read existing mapping from `/Users/srijan/Desktop/aksh/bse_nse_mapping_current.json` (392 mappings, 33.9% coverage)
2. Fetch latest BSE BhavCopy CSV and NSE BhavCopy CSV files
3. Use ISIN-based matching: (a) Extract ISIN from BSE BhavCopy, (b) Match ISIN in NSE BhavCopy to get NSE symbol
4. For companies with no ISIN match, use fuzzy company name matching (fuzzywuzzy library, threshold ≥90)
5. Manual validation: generate CSV of top 1,000 companies by market cap with proposed mappings for user review
6. Store final mapping in `bse_nse_mapping.json` with schema: `{bse_code: {nse_symbol, company_name, isin, match_method, confidence}}`
7. Achieve ≥80% mapping coverage (≥4,400 companies out of ~5,500)
8. Log unmapped companies to `unmapped_companies.csv` for future manual review

### Story 1.4: Extract Historical Financials from Quarterly PDFs

**As a** Feature Engineer,
**I want** historical quarterly financial data (Revenue, PAT, EPS, Margins) for 2-3 years,
**so that** I can calculate fundamental features like QoQ growth, YoY growth, and margin trends.

#### Acceptance Criteria

1. Reuse existing `indian_pdf_extractor.py` (80%+ success rate) via importable function
2. Query `earnings_calendar.db` for all earnings announcements between 2022-01-01 and 2025-11-13
3. For each announcement, download PDF from BSE if not cached, extract: Revenue (Cr), PAT (Cr), EPS, Operating Margin (%), Net Profit Margin (%)
4. Store extracted data in `historical_financials.db` with schema: `(bse_code, quarter, year, revenue_cr, pat_cr, eps, opm, npm, extraction_date, extraction_confidence)`
5. Achieve ≥80% extraction success rate across all PDFs
6. For failures, log PDF path and error reason to `extraction_failures.csv`
7. Validate data quality: (a) Revenue > 0, (b) -100% < Margins < 100%, (c) No duplicate (bse_code, quarter, year) entries

### Story 1.5: Collect Historical Price & Volume Data from BhavCopy

**As a** Technical Feature Engineer,
**I want** historical daily price, volume, and circuit data for 2-3 years,
**so that** I can calculate technical features like RSI, volume spikes, previous circuits, and price momentum.

#### Acceptance Criteria

1. Download BSE BhavCopy CSV files for all trading days between 2022-01-01 and 2025-11-13 from BSE website (`https://www.bseindia.com/markets/MarketInfo/DispQuot.aspx`)
2. Download NSE BhavCopy CSV files from NSE website (`https://www.nseindia.com/all-reports-derivatives`)
3. Parse CSV files and store in `price_movements.db` with schema: `(bse_code, nse_symbol, date, open, high, low, close, volume, prev_close, circuit_limit, hit_upper_circuit, hit_lower_circuit)`
4. Use yfinance API as fallback for missing dates (query by NSE symbol format "TICKER.NS")
5. Achieve ≥95% data completeness (no more than 5% missing dates per company)
6. Validate data quality: (a) OHLC relationships (open, high, low, close), (b) Volume > 0, (c) No future dates
7. Create indexes on (bse_code, date) and (nse_symbol, date) for fast querying

### Story 1.6: Validate Data Quality Before Training

**As a** ML System,
**I want** comprehensive data quality validation before training begins,
**so that** I don't train models on incomplete or invalid data.

#### Acceptance Criteria

1. DataQualityValidator class created with method `validate_training_readiness() -> ValidationReport`
2. Check 1: Verify ≥200,000 labeled samples in historical_upper_circuits.db
3. Check 2: Verify class distribution 5-15% upper circuits (Y=1)
4. Check 3: Verify ≥80% companies have complete financial data (all quarters 2022-2025)
5. Check 4: Verify ≥95% price data completeness
6. Check 5: Verify ≥80% BSE-NSE mapping coverage
7. Generate validation report with pass/fail for each check, total companies usable for training, estimated model performance based on data quality
8. If any check fails, provide remediation steps (e.g., "Missing financial data for 1,200 companies - extend collection to Q1 2022")

*(Remaining epics 2-5 with stories omitted for brevity - full PRD continues with all stories)*

## Checklist Results Report

*This section will be populated after running the pm-checklist to validate PRD completeness.*

## Next Steps

### UX Expert Prompt

*N/A - This is a backend ML system with minimal UI (Telegram alerts only). No UX expert engagement required.*

### Architect Prompt

**Architect, please create the architecture.md document for the Blockbuster Results Predictor ML system.**

Use this PRD as input and design a system architecture that:

1. Leverages the existing 127-agent infrastructure (Dexter/Vikram architecture) at `/Users/srijan/Desktop/aksh/agents/` and `/Users/srijan/vcp/agents/`
2. Defines 8 new ML-specific agents (MLDataCollectorAgent, MLFeatureEngineerAgent, MLTrainingAgent, MLInferenceAgent, MLMonitoringAgent, MLBacktestingAgent, MLAlertAgent, MLMasterOrchestrator)
3. Specifies tech stack: Python 3.10+, XGBoost, LightGBM, scikit-learn, SHAP, MLflow, Optuna, yfinance, SQLite, pytest, GitHub Actions
4. Details data models for 5 databases: historical_upper_circuits.db, historical_financials.db, price_movements.db, feature_store.db, ml_monitoring.db
5. Describes real-time inference pipeline achieving <2 min latency
6. Defines API endpoints (if any) and Telegram bot integration
7. Establishes testing strategy with ≥80% coverage (unit/integration/E2E)
8. Specifies security, error handling, and monitoring requirements

Reference the Technical Assumptions section above for repository structure (monorepo), service architecture (modular monolith with agents), and testing requirements (full pyramid with TDD).