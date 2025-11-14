# Product Requirements Document: ML-Based Upper Circuit Prediction System

**Project Name:** Blockbuster Results Predictor
**Version:** 1.0.0
**Date:** November 13, 2025
**Owner:** VCP Financial Research Team
**Status:** Approved - Ready for Development

---

## 1. Executive Summary

Build an ML-powered system that predicts which Indian stocks will hit upper circuit (5-20% surge) after quarterly earnings announcements, **before** market participants like Srinidhi identify them. The system will analyze ~11,000 NSE/BSE companies in real-time using BSE Telegram alerts and deliver predictions within 2 minutes of earnings announcement.

**Key Innovation:** Replace rule-based blockbuster detection (Vikram's 7-criteria scoring) with ML classification trained on 2-3 years of historical upper circuit patterns.

---

## 2. Problem Statement

### 2.1 Current Challenges

**Manual Identification Gap:**
- Srinidhi posts "blockbuster results" → stocks go upper circuit next day
- Currently NO automated way to identify these companies before Srinidhi
- Time = Money: Late entry means losing 5-20% potential gains

**Rule-Based System Limitations:**
- Vikram's 7-criteria scoring uses fixed thresholds (EPS 40pts, Revenue 15pts, etc.)
- Cannot capture hidden patterns in data
- Requires manual threshold tuning
- No learning from historical patterns

**Data Source Issues:**
- Screener.in data is "old and stale" (2-3 day delay)
- Mapping issues between BSE/NSE symbols (only 33.9% mapped)
- Not suitable for real-time trading decisions

**Infrastructure Gaps:**
- No historical training dataset (which stocks went upper circuit after earnings)
- No feature engineering pipeline for ML
- No model training/evaluation framework
- No real-time inference system

### 2.2 Impact of Current State

- **Lost Opportunities:** Miss 5-20% gains by identifying blockbusters late
- **Manual Effort:** Analysts manually scan 100+ daily earnings announcements
- **False Positives:** Rule-based system flags companies that don't surge
- **Scalability:** Cannot track all ~11,000 NSE/BSE companies manually

---

## 3. Solution Overview

### 3.1 Proposed System

**ML Classification Model** that predicts upper circuit probability (0-100%) for every company announcing quarterly results.

**Core Components:**
1. **Historical Data Collection** - 2-3 years of earnings + price movements
2. **Feature Engineering** - 25-30 features per company-quarter
3. **Model Training** - XGBoost/LightGBM classification
4. **Real-Time Inference** - <2 min from BSE alert to prediction
5. **Continuous Monitoring** - Accuracy tracking and auto-retraining

### 3.2 System Architecture

**Multi-Agent Design:**
- **MLDataCollectorAgent** - Orchestrate historical data collection
- **MLFeatureEngineerAgent** - Extract 25-30 features per sample
- **MLTrainingAgent** - Train/tune classification models
- **MLInferenceAgent** - Real-time predictions on new earnings
- **MLMonitoringAgent** - Track accuracy and trigger retraining
- **MLBacktestingAgent** - Validate model on historical data

**Leverage Existing Infrastructure:**
- 127 existing agents (Dexter/Vikram architecture)
- BSE Telegram bot (@BseAlertsTelegram_bot) for real-time alerts
- Existing databases (earnings_calendar.db, price_movements.db)
- indian_pdf_extractor.py (80%+ PDF extraction success)

### 3.3 Key Differentiators

| Feature | Rule-Based (Current) | ML-Based (Proposed) |
|---------|---------------------|---------------------|
| **Accuracy** | 50-60% (manual tuning) | Target 70%+ precision |
| **Pattern Detection** | Fixed thresholds only | Finds hidden patterns |
| **Adaptability** | Manual retuning needed | Auto-learns from data |
| **Explainability** | Clear rules (transparent) | Black box (but more accurate) |
| **Development Time** | Done (but limited) | 6-8 weeks |

---

## 4. User Stories

### 4.1 Primary Users

**User Type 1: Day Trader**
- **Need:** Real-time alerts for high-probability upper circuit stocks
- **Goal:** Enter position before market realizes the opportunity
- **Success:** Beat Srinidhi's posts by 15-30 minutes

**User Type 2: System Administrator**
- **Need:** Automated data collection and model retraining
- **Goal:** Maintain ≥70% prediction accuracy over time
- **Success:** System runs autonomously with minimal manual intervention

**User Type 3: Financial Analyst**
- **Need:** Understand which features drive upper circuit predictions
- **Goal:** Validate model outputs and build trust
- **Success:** Access to SHAP values and feature importance

### 4.2 User Stories

**Epic 1: Historical Data Collection**

```
US-101: As a system, I need to identify all historical upper circuits after earnings announcements
Acceptance Criteria:
- Query BhavCopy data for price movements on earnings announcement days
- Label upper circuits (≥5% surge + circuit hit)
- Cover 2-3 years historical data (2022-2025)
- Store in historical_upper_circuits.db
- Achieve ≥200,000 labeled samples
```

```
US-102: As a system, I need to map BSE codes to NSE symbols for price data
Acceptance Criteria:
- Use ISIN-based matching via BhavCopy files
- Achieve ≥80% mapping coverage (up from 33.9%)
- Store in bse_nse_mapping.json
- Include company names for validation
```

```
US-103: As a system, I need to extract historical financial data from quarterly PDFs
Acceptance Criteria:
- Reuse indian_pdf_extractor.py (80%+ success rate)
- Extract Sep/Dec/Mar/Jun data for 2022-2025
- Store in historical_financials.db
- Cover ~11,000 companies
```

**Epic 2: Feature Engineering**

```
US-201: As a model, I need fundamental features for each company-quarter
Acceptance Criteria:
- Revenue QoQ growth (%)
- PAT QoQ growth (%)
- EPS QoQ growth (%)
- Operating margin (OPM)
- Net profit margin (NPM)
- Debt-to-equity ratio
- Revenue YoY growth (%)
- PAT YoY growth (%)
```

```
US-202: As a model, I need technical features for each company-quarter
Acceptance Criteria:
- Price momentum (RSI 14-day)
- Volume spike (ratio to 30-day avg)
- Previous upper circuits (count in last 6 months)
- Stock price change (1 week before announcement)
- Market cap (₹Cr)
- 50-day moving average distance (%)
```

```
US-203: As a model, I need qualitative features for each company-quarter
Acceptance Criteria:
- New orders mentioned (Y/N)
- Forward guidance tone (positive/neutral/negative)
- Management commentary sentiment (0-1 score)
- Exceptional items mentioned (Y/N)
```

```
US-204: As a model, I need seasonality features for each company-quarter
Acceptance Criteria:
- Historical Q1/Q2/Q3/Q4 avg growth
- Quarter-specific patterns (e.g., Q4 strong for IT)
- Festival season proximity (Y/N)
```

**Epic 3: Model Training**

```
US-301: As a data scientist, I need to train classification models
Acceptance Criteria:
- Train XGBoost, LightGBM, Random Forest
- 70% train, 15% validation, 15% test split
- Hyperparameter tuning (Optuna)
- Achieve F1 ≥0.70 on test set
- Precision ≥70%, Recall ≥60%
```

```
US-302: As a data scientist, I need to handle class imbalance
Acceptance Criteria:
- Upper circuits are rare (5-10% of samples)
- Use SMOTE for oversampling minority class
- Use class weights in loss function
- Validate on real distribution (not resampled)
```

```
US-303: As a system, I need to save trained models
Acceptance Criteria:
- Save model artifacts to /models/ directory
- Include feature preprocessing pipeline
- Version models (v1.0.0, v1.0.1, etc.)
- Track experiments in MLflow
```

**Epic 4: Real-Time Inference**

```
US-401: As a trader, I need real-time predictions on new earnings
Acceptance Criteria:
- BSE alert arrives via Telegram → <2 min → Prediction delivered
- Extract PDF using indian_pdf_extractor.py
- Engineer features using MLFeatureEngineerAgent
- Load latest model and predict upper circuit probability
- Send alert if probability ≥70%
```

```
US-402: As a trader, I need to see prediction confidence levels
Acceptance Criteria:
- 90-100%: "Very High Confidence" (≤5 per quarter expected)
- 70-89%: "High Confidence" (10-15 per quarter expected)
- 50-69%: "Medium Confidence" (20-30 per quarter expected)
- <50%: Don't alert (reduces noise)
```

```
US-403: As a trader, I need explanations for predictions
Acceptance Criteria:
- Show top 5 features driving the prediction
- Use SHAP values for model explainability
- Display in alert: "High confidence due to: EPS +45%, Volume spike 3x, Positive guidance"
```

**Epic 5: Monitoring & Improvement**

```
US-501: As a system, I need to track prediction accuracy over time
Acceptance Criteria:
- Record actual price movements 1 day, 3 days, 7 days after prediction
- Calculate precision/recall weekly
- Alert if accuracy drops below 65% (trigger retraining)
- Store metrics in mlflow_tracking.db
```

```
US-502: As a system, I need to auto-retrain when data drifts
Acceptance Criteria:
- Detect feature drift (distribution changes)
- Trigger retraining if accuracy drops ≥5%
- Use last 18 months data for retraining
- Deploy new model automatically if F1 improves by ≥2%
```

```
US-503: As an analyst, I need backtesting results
Acceptance Criteria:
- Run model on Q4 FY25 data (Jan-Mar 2025)
- Compare predictions vs actual upper circuits
- Generate confusion matrix
- Calculate ROI if traded on predictions
```

---

## 5. Success Metrics

### 5.1 Model Performance

| Metric | Target | Critical Threshold | Measurement |
|--------|--------|-------------------|-------------|
| **Precision** | ≥70% | ≥65% | True positives / (TP + FP) |
| **Recall** | ≥60% | ≥50% | True positives / (TP + FN) |
| **F1 Score** | ≥0.70 | ≥0.65 | Harmonic mean of precision/recall |
| **AUC-ROC** | ≥0.75 | ≥0.70 | Area under ROC curve |

**Confusion Matrix Example (on 100 test samples):**
```
                Predicted: Upper Circuit    Predicted: No Circuit
Actual: Upper    70 (TP)                    30 (FN)
Actual: No       30 (FP)                    870 (TN)

Precision = 70 / (70 + 30) = 70%
Recall = 70 / (70 + 30) = 70%
F1 = 0.70
```

### 5.2 System Performance

| Metric | Target | Critical Threshold | Measurement |
|--------|--------|-------------------|-------------|
| **Latency** | <2 min | <3 min | BSE alert → Prediction delivered |
| **Coverage** | ~11,000 companies | ≥8,000 companies | % of companies trackable |
| **Uptime** | 99.5% | 99% | During market hours (9:15-3:30 IST) |
| **Data Quality** | ≥95% | ≥90% | % of complete feature vectors |

### 5.3 Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time Advantage** | Beat Srinidhi by 15-30 min | Time from announcement to alert |
| **Alert Precision** | ≥70% | % of alerts that actually go upper circuit |
| **False Positive Rate** | ≤30% | % of alerts that don't surge |
| **Coverage** | 90% of upper circuits | % of actual upper circuits we catch |

### 5.4 Development Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Test Coverage** | ≥80% | pytest coverage report |
| **Test Pass Rate** | 100% | CI/CD pipeline status |
| **Documentation** | 100% | All agents + functions documented |
| **Code Review** | 100% | All PRs reviewed before merge |

---

## 6. Technical Requirements

### 6.1 Data Requirements

**Historical Data:**
- **Time Period:** 2-3 years (2022-2025 preferred)
- **Companies:** All NSE/BSE listed (~11,000)
- **Samples:** 200,000-300,000 labeled earnings announcements
- **Labels:** Upper circuit Y/N (≥5% surge + circuit hit)

**Features (25-30 total):**

**Fundamental (8):**
1. Revenue QoQ growth (%)
2. PAT QoQ growth (%)
3. EPS QoQ growth (%)
4. Operating margin (OPM %)
5. Net profit margin (NPM %)
6. Debt-to-equity ratio
7. Revenue YoY growth (%)
8. PAT YoY growth (%)

**Technical (6):**
9. RSI (14-day)
10. Volume spike (ratio to 30-day avg)
11. Previous upper circuits (count, last 6 months)
12. Price change 1 week before (%)
13. Market cap (₹Cr, log scale)
14. Distance from 50-day MA (%)

**Qualitative (4):**
15. New orders mentioned (0/1)
16. Forward guidance tone (0=negative, 0.5=neutral, 1=positive)
17. Management sentiment score (0-1, from NLP)
18. Exceptional items mentioned (0/1)

**Seasonality (3):**
19. Historical Q1 avg performance (%)
20. Historical Q2 avg performance (%)
21. Historical Q3 avg performance (%)

**VCP Pattern (3):**
22. VCP detected (0/1)
23. VCP stage (1-4)
24. Volatility contraction depth (%)

**Market Context (3):**
25. Nifty 50 change same day (%)
26. Sector index change same day (%)
27. Market breadth (advancers/decliners ratio)

### 6.2 Model Requirements

**Algorithms:**
- XGBoost (primary)
- LightGBM (secondary)
- Random Forest (baseline)

**Training:**
- 70% train, 15% validation, 15% test
- Stratified split (preserve class balance)
- Cross-validation (5-fold)
- Hyperparameter tuning (Optuna, 100 trials)

**Class Imbalance Handling:**
- SMOTE oversampling (upper circuits are rare)
- Class weights in loss function
- Threshold tuning (optimize F1 on validation set)

**Model Artifacts:**
- Trained model (.pkl or .joblib)
- Feature preprocessing pipeline (scaler, encoders)
- Feature importance (SHAP values)
- Confusion matrix
- Training metrics (MLflow)

### 6.3 Infrastructure Requirements

**Agents to Build (8 new):**
1. `ml_data_collector.py` - Orchestrate historical data collection
2. `ml_feature_engineer.py` - Extract 25-30 features
3. `ml_training_agent.py` - Train and tune models
4. `ml_inference_agent.py` - Real-time predictions
5. `ml_monitoring_agent.py` - Track accuracy over time
6. `ml_backtesting_agent.py` - Validate on historical data
7. `ml_alert_agent.py` - Send alerts to Telegram
8. `ml_master_orchestrator.py` - Coordinate all ML agents

**Agents to Reuse (from 127 existing):**
- `indian_pdf_extractor.py` - PDF extraction (80%+ success)
- `intelligent_earnings_collector.py` - 3-phase AI research
- `blockbuster_detector.py` - Vikram's 7-criteria (for comparison)
- `vcp_detector.py` - VCP pattern features
- `earnings_analyzer.py` - Earnings quality analysis
- `bse_telegram_bot.py` - Real-time BSE alerts
- `dexter/agent.py` - Multi-agent orchestration pattern

**Databases:**
- `historical_upper_circuits.db` - Labels (upper circuit Y/N)
- `historical_financials.db` - Fundamental features
- `price_movements.db` - Technical features
- `feature_store.db` - Engineered features for training
- `mlflow_tracking.db` - Experiment tracking

**APIs:**
- BSE Telegram bot (@BseAlertsTelegram_bot) - Real-time alerts
- yfinance - Price/volume data
- BhavCopy (BSE/NSE) - Historical daily data
- Existing FastAPI endpoints

### 6.4 Testing Requirements

**Unit Tests (6 files):**
- `test_ml_data_collector.py` - Data collection logic
- `test_ml_feature_engineer.py` - Feature extraction
- `test_ml_training_agent.py` - Model training
- `test_ml_inference_agent.py` - Prediction logic
- `test_ml_monitoring_agent.py` - Accuracy tracking
- `test_ml_backtesting_agent.py` - Backtesting logic

**Integration Tests (3 files):**
- `test_data_pipeline.py` - End-to-end data collection
- `test_training_pipeline.py` - Feature engineering → Training
- `test_inference_pipeline.py` - PDF → Features → Prediction

**E2E Tests (3 files):**
- `test_e2e_historical.py` - Full system on historical data (Q4 FY25)
- `test_e2e_realtime.py` - BSE alert → Prediction → Alert
- `test_e2e_monitoring.py` - Accuracy tracking and retraining

**Coverage Target:**
- Unit tests: ≥90% coverage
- Integration tests: ≥85% coverage
- E2E tests: ≥80% coverage
- Overall: ≥80% coverage

**CI/CD:**
- GitHub Actions workflow
- Run on every PR
- Block merge if tests fail
- Auto-deploy to production on main branch merge

### 6.5 Performance Requirements

**Latency:**
- BSE alert received → PDF extracted: <30 seconds
- PDF extracted → Features engineered: <30 seconds
- Features engineered → Prediction generated: <10 seconds
- Prediction generated → Alert sent: <10 seconds
- **Total: <2 minutes**

**Throughput:**
- Handle 100 earnings announcements per day
- Process 10 concurrent PDF extractions
- Train model on 200K samples in <4 hours
- Batch predictions: 1,000 companies in <5 minutes

**Resource Limits:**
- Memory: <4GB per agent
- CPU: <2 cores per agent
- Disk: <20GB for all databases
- Model size: <500MB

---

## 7. Non-Functional Requirements

### 7.1 Scalability

- **Horizontal:** Add more MLInferenceAgent instances for higher throughput
- **Vertical:** Train larger models as data grows (XGBoost → Neural Networks)
- **Data:** Handle 5 years of historical data (500K+ samples)

### 7.2 Reliability

- **Uptime:** 99.5% during market hours (9:15 AM - 3:30 PM IST)
- **Error Handling:** Graceful degradation (if PDF fails, skip and log)
- **Data Quality:** Validate all features before training/inference
- **Monitoring:** Alert if accuracy drops ≥5% in any week

### 7.3 Maintainability

- **Code Quality:** PEP8 compliant, type hints, docstrings
- **Testing:** TDD approach (write tests before code)
- **Documentation:** Every agent documented in architecture.md
- **Versioning:** Semantic versioning for models (v1.0.0, v1.1.0, etc.)

### 7.4 Security

- **API Keys:** Store in .env, never commit to git
- **Data Privacy:** No PII collected (only public financial data)
- **Model Security:** Version control model artifacts
- **Access Control:** Restrict production deployment to authorized users

---

## 8. Constraints and Assumptions

### 8.1 Constraints

**Technical:**
- Must use existing 127 agents (cannot rebuild from scratch)
- Must integrate with BSE Telegram bot (no alternative real-time source)
- Must achieve ≥80% BSE-NSE mapping (required for price data)
- Cannot access Screener.in paid APIs (data quality issues)

**Business:**
- 6-8 week development timeline
- Development on single machine (no cloud budget for now)
- Manual validation required for first 2 weeks of production

**Data:**
- Historical PDFs may not exist for all companies (2022-2025)
- BhavCopy data availability varies by exchange
- Upper circuits are rare (5-10% of samples) → Class imbalance

### 8.2 Assumptions

**Data Assumptions:**
- BSE Telegram bot delivers alerts within 3 seconds of announcement
- PDFs are available within 5 minutes of announcement
- BhavCopy data is accurate for price movements
- indian_pdf_extractor.py maintains 80%+ success rate

**Model Assumptions:**
- Historical patterns (2022-2024) are predictive of future (2025-2026)
- 25-30 features are sufficient for 70%+ precision
- XGBoost/LightGBM can model non-linear relationships
- Model performance on test set generalizes to production

**Business Assumptions:**
- Upper circuits after earnings indicate "blockbuster" quality
- Beating Srinidhi by 15-30 minutes provides trading edge
- Traders can act on alerts within 2-5 minutes
- 70% precision is acceptable (30% false positive rate tolerable)

---

## 9. Dependencies and Risks

### 9.1 Dependencies

**Internal:**
- 127 existing agents (Dexter/Vikram architecture)
- BSE-NSE mapping improvement (from 33.9% to 80%+)
- historical_financials.db population (200K-300K samples)
- indian_pdf_extractor.py reliability

**External:**
- BSE Telegram bot uptime (@BseAlertsTelegram_bot)
- BSE website availability (for PDF downloads)
- BhavCopy data availability (NSE/BSE)
- yfinance API reliability

### 9.2 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **BSE-NSE mapping fails to reach 80%** | Medium | High | Use ISIN-based matching, manual top 1,000 companies |
| **Insufficient historical data (<100K samples)** | Low | High | Extend collection to 2019, use data augmentation |
| **Model accuracy <70%** | Medium | High | Add more features, try ensemble methods, extend training data |
| **BSE Telegram bot downtime** | Low | High | Fallback to direct BSE website scraping (slower) |
| **PDF extraction drops below 70%** | Low | Medium | Add more extraction strategies, manual fallback for top companies |
| **Class imbalance too severe** | Medium | Medium | Use SMOTE, class weights, threshold tuning |
| **Latency exceeds 2 minutes** | Low | Medium | Optimize feature engineering, use GPU for inference |
| **Data drift in production** | High | Medium | Continuous monitoring, auto-retraining every quarter |

---

## 10. Timeline and Milestones

### Phase 1: Foundation - SpecKit Documentation (Week 1)
- **Deliverables:** PRD.md ✓, architecture.md, epics, test framework, CI/CD
- **Success Criteria:** All docs reviewed and approved, tests run in CI/CD

### Phase 2: Data Collection (Week 2)
- **Deliverables:** MLDataCollectorAgent, historical data (200K+ samples), BSE-NSE mapping 80%+
- **Success Criteria:** ≥90% test coverage, data quality validation passes

### Phase 3: Feature Engineering (Week 3)
- **Deliverables:** MLFeatureEngineerAgent, feature_store.db, 25-30 features
- **Success Criteria:** Integration tests pass, feature correlation analysis complete

### Phase 4: Model Training (Week 4)
- **Deliverables:** MLTrainingAgent, trained models, F1 ≥0.70
- **Success Criteria:** Test set metrics meet thresholds, confusion matrix validated

### Phase 5: Inference & Deployment (Week 5)
- **Deliverables:** MLInferenceAgent, FastAPI endpoint, <2 min latency
- **Success Criteria:** E2E tests pass, real-time predictions working

### Phase 6: Monitoring & Improvement (Week 6-8)
- **Deliverables:** MLMonitoringAgent, backtesting results, production deployment
- **Success Criteria:** Accuracy tracking live, auto-retraining working, ROI validated

---

## 11. Acceptance Criteria

**Phase 1 (Documentation) - Ready to Code:**
- [ ] PRD.md reviewed and approved
- [ ] architecture.md reviewed and approved
- [ ] 5 epics with stories created
- [ ] pytest framework setup (unit/integration/e2e)
- [ ] CI/CD pipeline running

**Phase 2 (Data Collection) - Ready to Train:**
- [ ] ≥200,000 labeled samples collected
- [ ] BSE-NSE mapping ≥80% coverage
- [ ] historical_upper_circuits.db populated
- [ ] historical_financials.db populated
- [ ] Data quality tests passing (≥90% complete features)

**Phase 3 (Feature Engineering) - Ready to Model:**
- [ ] 25-30 features extracted per sample
- [ ] feature_store.db populated
- [ ] Feature correlation analysis complete
- [ ] Integration tests passing (≥85% coverage)

**Phase 4 (Training) - Ready to Deploy:**
- [ ] Model trained (XGBoost/LightGBM)
- [ ] F1 ≥0.70 on test set
- [ ] Precision ≥70%, Recall ≥60%
- [ ] Model artifacts saved with versioning
- [ ] SHAP values computed for explainability

**Phase 5 (Inference) - Ready for Production:**
- [ ] Real-time pipeline <2 min latency
- [ ] FastAPI endpoint live
- [ ] E2E tests passing (historical data)
- [ ] Telegram alerts working

**Phase 6 (Monitoring) - Production Ready:**
- [ ] Accuracy tracking live
- [ ] Backtesting results validated (Q4 FY25)
- [ ] Auto-retraining working
- [ ] All tests passing (≥80% coverage)
- [ ] Production deployment complete

---

## 12. Open Questions

1. **Historical Data Depth:** If we can only collect 1.5 years (instead of 2-3 years), is 100K samples sufficient?
2. **Model Explainability:** Should we prioritize explainability (use simpler models like Random Forest) over accuracy (XGBoost)?
3. **Alert Threshold:** Should we alert at ≥70% probability or higher (≥80%) to reduce false positives?
4. **Retraining Frequency:** Should we retrain every quarter, every 6 months, or based on accuracy drop?
5. **Feature Selection:** Should we use automated feature selection (e.g., RFECV) or domain expertise to choose 25-30 features?

---

## 13. Appendix

### A. Glossary

- **Upper Circuit:** Daily price limit (5-20% surge) imposed by exchange to prevent excessive volatility
- **Blockbuster Results:** Srinidhi's term for quarterly results that cause upper circuits
- **BSE/NSE:** Bombay Stock Exchange / National Stock Exchange (India's two main exchanges)
- **VCP:** Volatility Contraction Pattern (technical analysis pattern)
- **BhavCopy:** Daily price/volume data file published by BSE/NSE
- **ISIN:** International Securities Identification Number (unique ID for securities)
- **SHAP:** SHapley Additive exPlanations (model explainability method)
- **SMOTE:** Synthetic Minority Over-sampling Technique (class imbalance handling)

### B. References

- Vikram's 7-Criteria Blockbuster Detector: `/Users/srijan/vcp/agents/blockbuster_detector.py`
- Indian PDF Extractor: `/Users/srijan/Desktop/aksh/agents/indian_pdf_extractor.py`
- Dexter Multi-Agent Pattern: `/vcp/agents/dexter/agent.py`
- BSE Telegram Bot: `@BseAlertsTelegram_bot`
- Srinidhi's Posts: [Example needed from user]

### C. Related Documents

- [architecture.md](./architecture.md) - System design and agent architecture
- [epics/epic-1-data-collection.md](./epics/epic-1-data-collection.md) - Data collection stories
- [epics/epic-2-feature-engineering.md](./epics/epic-2-feature-engineering.md) - Feature engineering stories
- [epics/epic-3-model-training.md](./epics/epic-3-model-training.md) - Model training stories
- [epics/epic-4-inference-deployment.md](./epics/epic-4-inference-deployment.md) - Inference stories
- [epics/epic-5-monitoring-improvement.md](./epics/epic-5-monitoring-improvement.md) - Monitoring stories

---

**Document Status:** Approved for Development
**Next Steps:** Create architecture.md → Setup test framework → Build MLDataCollectorAgent
**Questions/Feedback:** Contact VCP Financial Research Team
