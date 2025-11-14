# Epic 2: Feature Engineering

**Epic ID**: EPIC-2
**Priority**: P0 (Critical Path)
**Status**: Not Started
**Estimated Effort**: 15 days
**Dependencies**: EPIC-1 (Data Collection) - COMPLETE ✅

---

## Epic Goal

Engineer 20-30 high-quality features from collected data (200K+ samples) to predict upper circuit movements (5-20% price surge) with target F1 ≥ 0.70.

---

## Background

With Epic 1 complete, we have:
- ✅ 200K+ labeled samples (upper circuit = 1, no circuit = 0)
- ✅ 3.9 years of historical price/volume data
- ✅ Quarterly financial data (revenue, PAT, EPS, margins)
- ✅ 80%+ BSE-NSE mapping for yfinance integration

**Challenge**: Raw data alone cannot predict upper circuits. We need engineered features that capture:
1. **Technical momentum** - Price patterns, volume spikes
2. **Financial health** - Revenue growth, margin expansion
3. **Market sentiment** - Reaction to earnings announcements
4. **Seasonality** - Historical patterns by quarter/month

---

## Success Criteria

1. **Feature Count**: 20-30 features (down from 100+ raw candidates)
2. **Feature Quality**: Average feature importance ≥ 0.03 (top 30 features)
3. **Correlation**: Max pairwise correlation ≤ 0.85 (avoid redundancy)
4. **Missing Data**: ≤5% missing values across all features
5. **Training Readiness**: Feature matrix ready for XGBoost/LightGBM

---

## Stories

### Story 2.1: Technical Features (RSI, MACD, Bollinger Bands)
**Estimated Effort**: 3 days

Extract technical indicators from price/volume data:
- RSI (14-day, 30-day)
- MACD (12, 26, 9)
- Bollinger Bands (20-day, 2 std dev)
- Volume ratios (current vs 30-day avg)
- Price momentum (5-day, 10-day, 30-day)

**Target**: 15-20 technical features per sample

---

### Story 2.2: Financial Features (Revenue Growth, Margin Trends)
**Estimated Effort**: 3 days

Extract financial indicators from quarterly data:
- Revenue growth (QoQ, YoY)
- Margin trends (OPM, NPM expansion/contraction)
- EPS growth
- Surprise metrics (actual vs consensus estimates)

**Target**: 10-15 financial features per sample

---

### Story 2.3: Sentiment Features (Earnings Reaction)
**Estimated Effort**: 2 days

Calculate market reaction to earnings:
- Pre-announcement momentum (5 days before)
- Day 1 reaction (announcement day price change)
- Volume spike on announcement day
- Historical earnings beat/miss rate

**Target**: 5-8 sentiment features per sample

---

### Story 2.4: Seasonality Features (Q1-Q4 Patterns)
**Estimated Effort**: 2 days

Capture seasonal patterns:
- Quarter indicators (Q1, Q2, Q3, Q4)
- Month indicators
- Historical upper circuit rate by quarter
- Industry seasonality (if available)

**Target**: 4-6 seasonality features per sample

---

### Story 2.5: Feature Selection (SHAP, Correlation Analysis)
**Estimated Effort**: 3 days

Reduce from 100+ candidates to 20-30 best features:
- Remove highly correlated features (>0.85)
- Remove low-importance features (<0.01)
- Use SHAP values for feature importance
- Validate with cross-validation

**Target**: 20-30 features with avg importance ≥0.03

---

### Story 2.6: Feature Quality Validation
**Estimated Effort**: 2 days

Validate feature matrix quality:
- Check missing data ≤5%
- Check feature distributions (no extreme outliers)
- Check feature stability across train/validation splits
- Generate feature quality report

**Target**: All quality checks passing

---

## Technical Architecture

### Data Flow
```
Epic 1 Databases
    ├─ price_movements.db (OHLCV data)
    ├─ historical_financials.db (Quarterly financials)
    ├─ historical_upper_circuits.db (Labels)
    └─ bse_nse_mapping.db (Mapping)
         ↓
Story 2.1-2.4: Feature Extraction
         ↓
    feature_candidates.db (100+ features)
         ↓
Story 2.5: Feature Selection
         ↓
    final_features.db (20-30 features)
         ↓
Story 2.6: Quality Validation
         ↓
    training_matrix.parquet (Ready for ML)
```

---

## Implementation Details

### File Structure
```
agents/ml/
├── ml_feature_engineer.py         # Main orchestrator (Story 2.1-2.6)
├── technical_feature_extractor.py # Story 2.1
├── financial_feature_extractor.py # Story 2.2
├── sentiment_feature_extractor.py # Story 2.3
├── seasonality_feature_extractor.py # Story 2.4
└── feature_selector.py            # Story 2.5

tests/unit/
├── test_technical_features.py
├── test_financial_features.py
├── test_sentiment_features.py
├── test_seasonality_features.py
├── test_feature_selector.py
└── test_feature_quality_validator.py

data/
└── features/
    ├── feature_candidates.db
    ├── final_features.db
    └── training_matrix.parquet
```

---

## Acceptance Criteria

### Epic-Level Acceptance Criteria
1. ✅ All 6 stories complete with ≥90% test coverage
2. ✅ Feature matrix generated for 200K+ samples
3. ✅ 20-30 features selected with avg importance ≥0.03
4. ✅ Missing data ≤5% across all features
5. ✅ Max pairwise correlation ≤0.85
6. ✅ Feature quality validation report generated
7. ✅ Training matrix saved in Parquet format

---

## Risks & Mitigations

**Risk 1**: Feature leakage (using future data)
- **Mitigation**: Strict time-based validation, use only data available before prediction date

**Risk 2**: High correlation between features
- **Mitigation**: Correlation analysis + SHAP-based selection

**Risk 3**: Missing financial data for some companies
- **Mitigation**: Imputation strategies, feature availability flags

**Risk 4**: Technical features unstable during low-volume periods
- **Mitigation**: Volume filters, rolling window smoothing

---

## Dependencies

### Input Dependencies (Epic 1)
- ✅ `price_movements.db` - OHLCV data
- ✅ `historical_financials.db` - Quarterly financials
- ✅ `historical_upper_circuits.db` - Training labels
- ✅ `bse_nse_mapping.db` - BSE-NSE mapping

### Library Dependencies
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `ta` (Technical Analysis Library) - RSI, MACD, Bollinger Bands
- `shap` - Feature importance
- `scikit-learn` - Feature selection, preprocessing
- `pyarrow` - Parquet file I/O

---

## Testing Strategy

### TDD Workflow (Same as Epic 1)
1. **RED**: Write tests first
2. **GREEN**: Implement to pass tests
3. **REFACTOR**: Improve code quality

### Test Coverage Target
- Unit tests: ≥90% coverage
- Integration tests: End-to-end feature extraction
- Performance tests: Feature extraction time <10 minutes for 200K samples

---

## Timeline

**Total Estimated Duration**: 15 days

- Story 2.1: 3 days (Technical Features)
- Story 2.2: 3 days (Financial Features)
- Story 2.3: 2 days (Sentiment Features)
- Story 2.4: 2 days (Seasonality Features)
- Story 2.5: 3 days (Feature Selection)
- Story 2.6: 2 days (Quality Validation)

**Start Date**: 2025-11-13
**Target Completion**: 2025-11-28

---

## Definition of Done

- [ ] All 6 stories implemented with TDD
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Extract features for 200K+ samples
- [ ] Performance test: Feature extraction completes in <10 minutes
- [ ] Feature importance analysis: Top 30 features identified
- [ ] Correlation analysis: Max correlation ≤0.85
- [ ] Missing data report: ≤5% missing values
- [ ] Training matrix saved: `training_matrix.parquet` (20-30 features × 200K samples)
- [ ] Code review: Passes linter, type checking
- [ ] Documentation: Epic summary, feature dictionary

---

## Next Epic

**Epic 3: Model Training & Hyperparameter Tuning**
- Train XGBoost/LightGBM models
- Hyperparameter optimization
- Cross-validation
- Target: F1 ≥ 0.70 on validation set

---

**Author**: VCP Financial Research Team
**Created**: 2025-11-13
**Last Updated**: 2025-11-13
