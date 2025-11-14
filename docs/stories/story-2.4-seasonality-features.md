# Story 2.4: Seasonality Features

**Story ID**: 2.4
**Epic**: Epic 2 - Feature Engineering
**Priority**: P0 (Critical Path)
**Estimated Effort**: 1.5 days
**Status**: In Progress
**Dependencies**:
- Story 1.2 (UpperCircuitLabeler) - COMPLETE ✅
- Story 2.1 (Technical Features) - COMPLETE ✅
- Story 2.2 (Financial Features) - COMPLETE ✅
- Story 2.3 (Sentiment Features) - COMPLETE ✅

---

## Story Goal

Extract 4-6 seasonality features to capture quarterly patterns, fiscal year effects, and historical upper circuit rate by quarter for upper circuit prediction.

---

## Background

With Stories 2.1-2.3 complete, we have:
- ✅ 13 technical features
- ✅ 15 financial features
- ✅ 8 sentiment features
- ✅ 200K+ labeled samples with announcement dates and upper circuit labels

**Challenge**: Upper circuit frequency may vary by quarter due to:
1. **Fiscal Year Effects** - Q4 (Jan-Mar) often has strong earnings
2. **Quarterly Patterns** - Q1/Q2/Q3 may have different market reactions
3. **Month-Specific Trends** - January effect, March end rally
4. **Historical Circuit Rates** - Some quarters historically see more upper circuits

---

## Acceptance Criteria

### AC2.4.1: SeasonalityFeatureExtractor Class Initialization
- [ ] Class `SeasonalityFeatureExtractor` exists in `agents/ml/seasonality_feature_extractor.py`
- [ ] Constructor accepts `labels_db_path` and `output_db_path`
- [ ] Creates `seasonality_features` table with 6 feature columns
- [ ] Creates indexes on `bse_code` and `date` for query performance

### AC2.4.2: Quarter Indicator Features
- [ ] Extract quarter (Q1/Q2/Q3/Q4) from announcement date
- [ ] Create one-hot encoding for quarters (4 binary features)
- [ ] Handle Indian fiscal year quarters (Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar)

### AC2.4.3: Month Indicator
- [ ] Extract month (1-12) from announcement date
- [ ] Return as integer feature (1=January, 12=December)

### AC2.4.4: Historical Circuit Rate by Quarter
- [ ] Calculate upper circuit rate for same company, same quarter, historical data
- [ ] Formula: `(# upper circuits in Q) / (# total announcements in Q)` over last 3 years
- [ ] Handle companies with no historical data (return 0.0 or NaN)

### AC2.4.5: Batch Processing
- [ ] Method `extract_features_for_sample(bse_code, date)` returns `SeasonalityFeatures` object
- [ ] Method `extract_features_batch(samples)` processes multiple samples
- [ ] Returns DataFrame with all features
- [ ] Stores results in `seasonality_features.db`
- [ ] Performance: 1000 samples in <3 seconds

### AC2.4.6: Missing Data Handling
- [ ] Return 0 for historical circuit rate when no historical data
- [ ] Log warning when historical data <3 announcements for quarter
- [ ] Track missing data rate (target ≤5%)

---

## Technical Specifications

### SeasonalityFeatures Dataclass

```python
@dataclass
class SeasonalityFeatures:
    bse_code: str
    date: str  # Earnings announcement date

    # Quarter indicators (4 one-hot features)
    is_q1: int  # 1 if Q1 (Apr-Jun), 0 otherwise
    is_q2: int  # 1 if Q2 (Jul-Sep), 0 otherwise
    is_q3: int  # 1 if Q3 (Oct-Dec), 0 otherwise
    is_q4: int  # 1 if Q4 (Jan-Mar), 0 otherwise

    # Month indicator (1 feature)
    announcement_month: int  # 1-12

    # Historical circuit rate (1 feature)
    historical_circuit_rate_quarter: Optional[float]  # % of upper circuits in this quarter historically

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

**Total Features**: 6

---

## Database Schema

```sql
CREATE TABLE seasonality_features (
    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bse_code TEXT NOT NULL,
    date DATE NOT NULL,

    -- Quarter indicators (one-hot)
    is_q1 INTEGER,
    is_q2 INTEGER,
    is_q3 INTEGER,
    is_q4 INTEGER,

    -- Month indicator
    announcement_month INTEGER,

    -- Historical circuit rate
    historical_circuit_rate_quarter REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bse_code, date) ON CONFLICT REPLACE
);

CREATE INDEX idx_seasonality_sample_id ON seasonality_features(feature_id);
CREATE INDEX idx_seasonality_bse_date ON seasonality_features(bse_code, date);
```

---

## Calculation Details

### Quarter Determination (Indian Fiscal Year)

```
Month → Quarter Mapping:
January   → Q4
February  → Q4
March     → Q4
April     → Q1
May       → Q1
June      → Q1
July      → Q2
August    → Q2
September → Q2
October   → Q3
November  → Q3
December  → Q3
```

### One-Hot Encoding

```python
if quarter == 'Q1':
    is_q1, is_q2, is_q3, is_q4 = 1, 0, 0, 0
elif quarter == 'Q2':
    is_q1, is_q2, is_q3, is_q4 = 0, 1, 0, 0
# ... etc
```

### Historical Circuit Rate Calculation

```python
# For a given company and quarter (e.g., Q1), look back 3 years
historical_announcements = load_announcements_for_quarter(bse_code, quarter, years=3)
upper_circuits = count(announcements where upper_circuit == 1)
total_announcements = count(all announcements)

historical_circuit_rate_quarter = upper_circuits / total_announcements if total > 0 else 0.0
```

---

## Test Structure

### Test Classes
1. `TestSeasonalityFeatureExtractorInitialization` (3 tests)
   - Class exists
   - Constructor instantiation
   - Database schema creation

2. `TestQuarterExtraction` (4 tests)
   - Q1 extraction (Apr-Jun)
   - Q2 extraction (Jul-Sep)
   - Q3 extraction (Oct-Dec)
   - Q4 extraction (Jan-Mar)

3. `TestOneHotEncoding` (4 tests)
   - Q1 one-hot encoding
   - Q2 one-hot encoding
   - Q3 one-hot encoding
   - Q4 one-hot encoding

4. `TestMonthExtraction` (2 tests)
   - Month extraction from date
   - Month range validation (1-12)

5. `TestHistoricalCircuitRate` (3 tests)
   - Calculate rate with historical data
   - Handle no historical data
   - Handle sparse historical data (<3 announcements)

6. `TestFeatureExtraction` (2 tests)
   - Single sample extraction
   - Batch extraction

7. `TestMissingDataHandling` (2 tests)
   - No historical data returns 0
   - Missing data logged

8. `TestPerformance` (1 test)
   - Batch processing speed

**Total Tests**: 21 tests

---

## Integration with Epic 1 Data

### Input Data (from Story 1.2)
```sql
SELECT bse_code, date, upper_circuit
FROM upper_circuit_labels
WHERE bse_code = ?
ORDER BY date DESC
```

### Quarter Mapping Logic
```python
MONTH_TO_QUARTER = {
    1: 'Q4', 2: 'Q4', 3: 'Q4',  # Jan-Mar
    4: 'Q1', 5: 'Q1', 6: 'Q1',  # Apr-Jun
    7: 'Q2', 8: 'Q2', 9: 'Q2',  # Jul-Sep
    10: 'Q3', 11: 'Q3', 12: 'Q3'  # Oct-Dec
}
```

---

## Edge Cases

### 1. Company Recently Listed
**Scenario**: Company listed <3 years ago, no historical data for quarter
**Handling**: Return `historical_circuit_rate_quarter = 0.0`, log warning

### 2. Quarterly Pattern Change
**Scenario**: Company historically announced in Q1, now announces in Q4
**Handling**: Calculate rate for current quarter (Q4), may be 0.0 if no prior Q4 data

### 3. Sparse Announcements
**Scenario**: Only 1-2 announcements in quarter over 3 years
**Handling**: Calculate rate with available data, flag as low confidence in logs

### 4. Multiple Announcements Per Quarter
**Scenario**: Company announces multiple times in same quarter (e.g., results + AGM)
**Handling**: Include all announcements in rate calculation

---

## Performance Targets

- **Single Sample**: <3ms per sample
- **Batch (1000 samples)**: <3 seconds (333 samples/second)
- **Full Dataset (200K samples)**: <10 minutes (estimated)

---

## Dependencies

### External Libraries
- `pandas` - Data manipulation
- `sqlite3` - Database access
- `datetime` - Date parsing

### Internal Dependencies
- `upper_circuit_labels.db` (Story 1.2) - for historical circuit rates

---

## Definition of Done

- [ ] All 6 acceptance criteria implemented
- [ ] 21 unit tests achieving 100% pass rate
- [ ] Database schema created with indexes
- [ ] Performance test: 1000 samples in <3 seconds
- [ ] Missing data rate ≤5% (measured across all features)
- [ ] Code review: Passes linter, type checking
- [ ] Documentation: Docstrings for all public methods
- [ ] Integration test: Extract features for 10 real companies

---

## Risks & Mitigations

**Risk 1**: Historical data too sparse for reliable circuit rate calculation
- **Mitigation**: Require minimum 3 announcements, flag low confidence

**Risk 2**: Quarter mapping confusion (fiscal vs calendar)
- **Mitigation**: Clear documentation, comprehensive tests for all months

**Risk 3**: Performance slower than expected due to historical lookups
- **Mitigation**: Single query loads all historical data per company, cache results

---

## Timeline

**Estimated Effort**: 1.5 days
- Day 1: Write tests (RED phase), implement basic structure
- Day 1.5: Implement all calculation methods (GREEN phase), refactor

**Start Date**: 2025-11-13
**Target Completion**: 2025-11-15

---

**Author**: VCP Financial Research Team
**Created**: 2025-11-13
**Last Updated**: 2025-11-13
