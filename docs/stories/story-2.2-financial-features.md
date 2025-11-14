# Story 2.2: Financial Features

**Story ID**: 2.2
**Epic**: Epic 2 - Feature Engineering
**Priority**: P0 (Critical Path)
**Estimated Effort**: 3 days
**Status**: In Progress
**Dependencies**:
- Story 1.4 (FinancialExtractor) - COMPLETE ✅
- Story 2.1 (Technical Features) - COMPLETE ✅

---

## Story Goal

Extract 10-15 high-quality financial features from quarterly financial data to capture company financial health, growth trends, and earnings quality for upper circuit prediction.

---

## Background

With Story 1.4 complete, we have:
- ✅ `historical_financials.db` with quarterly data (revenue, PAT, EPS, margins)
- ✅ 200K+ labeled samples from earnings announcements
- ✅ ≥80% companies with complete financial history

**Challenge**: Raw financial data needs to be transformed into predictive features:
1. **Growth Metrics** - QoQ and YoY revenue/profit growth
2. **Margin Trends** - OPM and NPM expansion/contraction
3. **Earnings Quality** - Consistency, beat/miss patterns
4. **Profitability** - ROE, ROCE, profit margins

---

## Acceptance Criteria

### AC2.2.1: FinancialFeatureExtractor Class Initialization
- [x] Class `FinancialFeatureExtractor` exists in `agents/ml/financial_feature_extractor.py`
- [x] Constructor accepts `financials_db_path` and `output_db_path`
- [x] Creates `financial_features` table with 15 feature columns
- [x] Creates indexes on `bse_code` and `date` for query performance

### AC2.2.2: Revenue Growth Features
- [x] Calculate quarter-over-quarter (QoQ) revenue growth (%)
- [x] Calculate year-over-year (YoY) revenue growth (%)
- [x] Calculate 4-quarter moving average revenue growth
- [x] Handle negative/zero revenue gracefully (return NaN)
- [x] Validate growth rate range (-100% to +1000%)

### AC2.2.3: Profit Growth Features
- [x] Calculate QoQ PAT (Profit After Tax) growth (%)
- [x] Calculate YoY PAT growth (%)
- [x] Calculate 4-quarter moving average PAT growth
- [x] Handle losses (negative PAT) with special logic
- [x] Detect profit turnarounds (loss → profit)

### AC2.2.4: Margin Features
- [x] Calculate Operating Profit Margin (OPM) for current quarter
- [x] Calculate Net Profit Margin (NPM) for current quarter
- [x] Calculate margin expansion/contraction (delta vs previous quarter)
- [x] Calculate 4-quarter average margins
- [x] Validate margin range (-100% to +100%)

### AC2.2.5: EPS Features
- [x] Calculate QoQ EPS growth (%)
- [x] Calculate YoY EPS growth (%)
- [x] Calculate EPS consistency (standard deviation over 4 quarters)

### AC2.2.6: Earnings Quality Features
- [x] Calculate earnings beat rate (% of quarters beating expectations)
- [x] Calculate consecutive quarters of growth (streak)
- [x] Detect earnings surprises (>20% growth vs previous quarter)

### AC2.2.7: Batch Processing
- [x] Method `extract_features_for_sample(bse_code, date)` returns `FinancialFeatures` object
- [x] Method `extract_features_batch(samples)` processes multiple samples
- [x] Returns DataFrame with all features
- [x] Stores results in `financial_features.db`
- [x] Performance: 1000 samples in <10 seconds

### AC2.2.8: Missing Data Handling
- [x] Return NaN for features when <4 quarters of data available
- [x] Log warning when insufficient data
- [x] Track missing data rate (target ≤5%)

---

## Technical Specifications

### FinancialFeatures Dataclass

```python
@dataclass
class FinancialFeatures:
    bse_code: str
    date: str  # Earnings announcement date

    # Revenue growth features (3)
    revenue_growth_qoq: Optional[float]  # Quarter-over-quarter (%)
    revenue_growth_yoy: Optional[float]  # Year-over-year (%)
    revenue_growth_avg_4q: Optional[float]  # 4-quarter moving average

    # Profit growth features (3)
    pat_growth_qoq: Optional[float]
    pat_growth_yoy: Optional[float]
    pat_growth_avg_4q: Optional[float]

    # Margin features (4)
    operating_margin: Optional[float]  # Current quarter OPM (%)
    net_profit_margin: Optional[float]  # Current quarter NPM (%)
    margin_expansion_qoq: Optional[float]  # NPM delta vs prev quarter
    avg_margin_4q: Optional[float]  # 4-quarter average NPM

    # EPS features (3)
    eps_growth_qoq: Optional[float]
    eps_growth_yoy: Optional[float]
    eps_consistency: Optional[float]  # Std dev over 4 quarters

    # Earnings quality features (2)
    consecutive_growth_quarters: Optional[int]  # Growth streak
    earnings_surprise: Optional[int]  # Binary: 1 if >20% growth QoQ

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

**Total Features**: 15

---

## Database Schema

```sql
CREATE TABLE financial_features (
    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bse_code TEXT NOT NULL,
    date DATE NOT NULL,

    -- Revenue growth features
    revenue_growth_qoq REAL,
    revenue_growth_yoy REAL,
    revenue_growth_avg_4q REAL,

    -- Profit growth features
    pat_growth_qoq REAL,
    pat_growth_yoy REAL,
    pat_growth_avg_4q REAL,

    -- Margin features
    operating_margin REAL,
    net_profit_margin REAL,
    margin_expansion_qoq REAL,
    avg_margin_4q REAL,

    -- EPS features
    eps_growth_qoq REAL,
    eps_growth_yoy REAL,
    eps_consistency REAL,

    -- Earnings quality features
    consecutive_growth_quarters INTEGER,
    earnings_surprise INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bse_code, date) ON CONFLICT REPLACE
);

CREATE INDEX idx_financial_sample_id ON financial_features(feature_id);
CREATE INDEX idx_financial_bse_date ON financial_features(bse_code, date);
```

---

## Calculation Details

### Revenue Growth (QoQ)
```
revenue_growth_qoq = ((Revenue_Q0 - Revenue_Q-1) / Revenue_Q-1) * 100

Where:
- Q0 = Current quarter
- Q-1 = Previous quarter (Q4 → Q3 → Q2 → Q1)
```

### Revenue Growth (YoY)
```
revenue_growth_yoy = ((Revenue_Q0 - Revenue_Q-4) / Revenue_Q-4) * 100

Where:
- Q0 = Current quarter
- Q-4 = Same quarter, previous year (e.g., Q1 2024 vs Q1 2023)
```

### Margin Calculation
```
operating_margin = (Operating_Profit / Revenue) * 100
net_profit_margin = (PAT / Revenue) * 100
margin_expansion_qoq = NPM_Q0 - NPM_Q-1
```

### Consecutive Growth Quarters
```
Count consecutive quarters where:
- Revenue_Growth_QoQ > 0
- PAT_Growth_QoQ > 0

Reset counter when either metric declines.
```

### Earnings Surprise
```
earnings_surprise = 1 if (Revenue_Growth_QoQ > 20% OR PAT_Growth_QoQ > 20%) else 0
```

---

## Test Structure

### Test Classes
1. `TestFinancialFeatureExtractorInitialization` (3 tests)
   - Class exists
   - Constructor instantiation
   - Database schema creation

2. `TestRevenueGrowthCalculation` (4 tests)
   - QoQ growth calculation
   - YoY growth calculation
   - 4-quarter average
   - Negative revenue handling

3. `TestProfitGrowthCalculation` (4 tests)
   - QoQ PAT growth
   - YoY PAT growth
   - Loss-to-profit turnaround
   - Profit-to-loss detection

4. `TestMarginCalculation` (4 tests)
   - Operating margin calculation
   - Net profit margin calculation
   - Margin expansion/contraction
   - 4-quarter average margins

5. `TestEPSFeatures` (3 tests)
   - QoQ EPS growth
   - YoY EPS growth
   - EPS consistency (std dev)

6. `TestEarningsQuality` (3 tests)
   - Consecutive growth quarters
   - Earnings surprise detection
   - Growth streak reset

7. `TestFeatureExtraction` (2 tests)
   - Single sample extraction
   - Batch extraction

8. `TestMissingDataHandling` (2 tests)
   - Insufficient data returns NaN
   - Missing data logged

9. `TestPerformance` (1 test)
   - Batch processing speed

**Total Tests**: 26 tests

---

## Integration with Epic 1 Data

### Input Data (from Story 1.4)
```sql
SELECT bse_code, quarter, year, revenue, pat, opm, npm, eps
FROM historical_financials
WHERE bse_code = ?
ORDER BY year DESC, quarter DESC
LIMIT 12  -- Load 3 years (12 quarters)
```

### Quarter Ordering
```
Q1 = Apr-Jun (Fiscal Q1)
Q2 = Jul-Sep (Fiscal Q2)
Q3 = Oct-Dec (Fiscal Q3)
Q4 = Jan-Mar (Fiscal Q4)

Ordering: Q4 2024 > Q3 2024 > Q2 2024 > Q1 2024 > Q4 2023 > ...
```

---

## Edge Cases

### 1. Negative Revenue
**Scenario**: Revenue < 0 (rare, but possible due to accounting adjustments)
**Handling**: Return `NaN` for growth rates, log warning

### 2. Loss-to-Profit Turnaround
**Scenario**: PAT_Q-1 = -100 Cr, PAT_Q0 = +50 Cr
**Handling**:
- Calculate as special case: `((50 - (-100)) / abs(-100)) * 100 = 150%`
- Flag as turnaround event

### 3. Profit-to-Loss
**Scenario**: PAT_Q-1 = +100 Cr, PAT_Q0 = -50 Cr
**Handling**: Return `-150%` growth

### 4. Zero Revenue
**Scenario**: Revenue = 0 (company not operational)
**Handling**: Return `NaN` for margins and growth, log warning

### 5. Missing Quarters
**Scenario**: Only 2 quarters of data available
**Handling**: Return `NaN` for YoY and 4Q averages, calculate QoQ if possible

---

## Performance Targets

- **Single Sample**: <10ms per sample
- **Batch (1000 samples)**: <10 seconds (100 samples/second)
- **Full Dataset (200K samples)**: <35 minutes (estimated)

---

## Dependencies

### External Libraries
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `sqlite3` - Database access

### Internal Dependencies
- `historical_financials.db` (Story 1.4)
- `upper_circuit_labels.db` (Story 1.2) - for date mapping

---

## Definition of Done

- [ ] All 8 acceptance criteria implemented
- [ ] 26 unit tests achieving 100% pass rate
- [ ] Database schema created with indexes
- [ ] Performance test: 1000 samples in <10 seconds
- [ ] Missing data rate ≤5% (measured across all features)
- [ ] Code review: Passes linter, type checking
- [ ] Documentation: Docstrings for all public methods
- [ ] Integration test: Extract features for 10 real companies

---

## Risks & Mitigations

**Risk 1**: Financial data quality issues (missing quarters, inconsistent reporting)
- **Mitigation**: Robust NaN handling, validation checks, logging

**Risk 2**: Quarter ordering complexity (Q1-Q4 vs calendar quarters)
- **Mitigation**: Clear quarter ordering logic, comprehensive tests

**Risk 3**: Performance slower than expected for 200K samples
- **Mitigation**: Batch loading of financials, caching, vectorized operations

---

## Timeline

**Estimated Effort**: 3 days
- Day 1: Write tests (RED phase), implement basic structure
- Day 2: Implement all calculation methods (GREEN phase)
- Day 3: Refactor, optimize, integration testing

**Start Date**: 2025-11-13
**Target Completion**: 2025-11-16

---

**Author**: VCP Financial Research Team
**Created**: 2025-11-13
**Last Updated**: 2025-11-13
