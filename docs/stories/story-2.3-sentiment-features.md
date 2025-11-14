# Story 2.3: Sentiment Features

**Story ID**: 2.3
**Epic**: Epic 2 - Feature Engineering
**Priority**: P0 (Critical Path)
**Estimated Effort**: 2 days
**Status**: In Progress
**Dependencies**:
- Story 1.2 (UpperCircuitLabeler) - COMPLETE ✅
- Story 1.3 (PriceDataCollector) - COMPLETE ✅
- Story 2.1 (Technical Features) - COMPLETE ✅
- Story 2.2 (Financial Features) - COMPLETE ✅

---

## Story Goal

Extract 5-8 sentiment/reaction features from price and volume data around earnings announcement dates to capture market reaction and investor sentiment for upper circuit prediction.

---

## Background

With Stories 2.1 and 2.2 complete, we have:
- ✅ 13 technical features (RSI, MACD, Bollinger Bands, volume indicators)
- ✅ 15 financial features (revenue/profit growth, margins, EPS, earnings quality)
- ✅ 200K+ labeled samples with announcement dates
- ✅ Historical price data for all stocks

**Challenge**: Need to capture market sentiment around earnings announcements:
1. **Pre-Announcement Momentum** - How stock moved before earnings (anticipation)
2. **Day 1 Reaction** - Immediate market response to earnings announcement
3. **Volume Behavior** - Volume spikes indicating strong conviction
4. **Post-Announcement Volatility** - Price stability after announcement

---

## Acceptance Criteria

### AC2.3.1: SentimentFeatureExtractor Class Initialization
- [ ] Class `SentimentFeatureExtractor` exists in `agents/ml/sentiment_feature_extractor.py`
- [ ] Constructor accepts `price_db_path`, `labels_db_path`, and `output_db_path`
- [ ] Creates `sentiment_features` table with 8 feature columns
- [ ] Creates indexes on `bse_code` and `date` for query performance

### AC2.3.2: Pre-Announcement Momentum Features
- [ ] Calculate 5-day price momentum before earnings (% change)
- [ ] Calculate 10-day price momentum before earnings
- [ ] Calculate relative momentum vs market index (if available)
- [ ] Handle missing price data gracefully (return NaN)

### AC2.3.3: Day 1 Reaction Features
- [ ] Calculate Day 0 price change (announcement day % change)
- [ ] Calculate Day 1 price change (next trading day % change)
- [ ] Detect gap up/down on announcement day
- [ ] Calculate 2-day cumulative reaction (Day 0 + Day 1)

### AC2.3.4: Volume Behavior Features
- [ ] Calculate volume spike ratio (announcement day vs 20-day avg)
- [ ] Detect volume surge (>2x average volume)
- [ ] Calculate pre-announcement volume trend (5-day avg vs 20-day avg)

### AC2.3.5: Post-Announcement Volatility
- [ ] Calculate 5-day post-announcement volatility (std dev of returns)
- [ ] Compare to pre-announcement volatility (5 days before)

### AC2.3.6: Batch Processing
- [ ] Method `extract_features_for_sample(bse_code, date)` returns `SentimentFeatures` object
- [ ] Method `extract_features_batch(samples)` processes multiple samples
- [ ] Returns DataFrame with all features
- [ ] Stores results in `sentiment_features.db`
- [ ] Performance: 1000 samples in <5 seconds

### AC2.3.7: Missing Data Handling
- [ ] Return NaN for features when insufficient price data
- [ ] Log warning when <30 days of data available around announcement
- [ ] Track missing data rate (target ≤5%)

---

## Technical Specifications

### SentimentFeatures Dataclass

```python
@dataclass
class SentimentFeatures:
    bse_code: str
    date: str  # Earnings announcement date

    # Pre-announcement momentum (2 features)
    pre_momentum_5d: Optional[float]  # 5-day price momentum before announcement (%)
    pre_momentum_10d: Optional[float]  # 10-day price momentum before announcement (%)

    # Day 1 reaction (3 features)
    day0_reaction: Optional[float]  # Announcement day price change (%)
    day1_reaction: Optional[float]  # Next trading day price change (%)
    cumulative_reaction_2d: Optional[float]  # Day 0 + Day 1 combined (%)

    # Volume behavior (2 features)
    volume_spike_ratio: Optional[float]  # Announcement volume / 20-day avg volume
    pre_volume_trend: Optional[float]  # 5-day avg volume / 20-day avg volume

    # Post-announcement volatility (1 feature)
    post_volatility_5d: Optional[float]  # Std dev of 5-day returns after announcement

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

**Total Features**: 8

---

## Database Schema

```sql
CREATE TABLE sentiment_features (
    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bse_code TEXT NOT NULL,
    date DATE NOT NULL,

    -- Pre-announcement momentum
    pre_momentum_5d REAL,
    pre_momentum_10d REAL,

    -- Day 1 reaction
    day0_reaction REAL,
    day1_reaction REAL,
    cumulative_reaction_2d REAL,

    -- Volume behavior
    volume_spike_ratio REAL,
    pre_volume_trend REAL,

    -- Post-announcement volatility
    post_volatility_5d REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bse_code, date) ON CONFLICT REPLACE
);

CREATE INDEX idx_sentiment_sample_id ON sentiment_features(feature_id);
CREATE INDEX idx_sentiment_bse_date ON sentiment_features(bse_code, date);
```

---

## Calculation Details

### Pre-Announcement Momentum (5-day)
```
Price on Day -5 = P_-5
Price on Day -1 = P_-1 (day before announcement)

pre_momentum_5d = ((P_-1 - P_-5) / P_-5) * 100
```

### Day 0 Reaction
```
Open on Day 0 = O_0
Close on Day 0 = C_0

day0_reaction = ((C_0 - O_0) / O_0) * 100
```

### Volume Spike Ratio
```
Volume on Day 0 = V_0
20-day average volume = Avg(V_-20 to V_-1)

volume_spike_ratio = V_0 / Avg_20d
```

### Post-Announcement Volatility
```
Daily returns for Days +1 to +5 = [r_1, r_2, r_3, r_4, r_5]

post_volatility_5d = std_dev([r_1, r_2, r_3, r_4, r_5])
```

---

## Test Structure

### Test Classes
1. `TestSentimentFeatureExtractorInitialization` (3 tests)
   - Class exists
   - Constructor instantiation
   - Database schema creation

2. `TestPreAnnouncementMomentum` (3 tests)
   - 5-day momentum calculation
   - 10-day momentum calculation
   - Missing data handling

3. `TestDay1Reaction` (4 tests)
   - Day 0 reaction calculation
   - Day 1 reaction calculation
   - Cumulative 2-day reaction
   - Gap up/down detection

4. `TestVolumeBehavior` (3 tests)
   - Volume spike ratio calculation
   - Pre-announcement volume trend
   - Volume surge detection (>2x)

5. `TestPostVolatility` (2 tests)
   - 5-day post-announcement volatility
   - Volatility comparison (pre vs post)

6. `TestFeatureExtraction` (2 tests)
   - Single sample extraction
   - Batch extraction

7. `TestMissingDataHandling` (2 tests)
   - Insufficient data returns NaN
   - Missing data logged

8. `TestPerformance` (1 test)
   - Batch processing speed

**Total Tests**: 20 tests

---

## Integration with Epic 1 Data

### Input Data (from Story 1.3)
```sql
SELECT date, open, high, low, close, volume
FROM historical_prices
WHERE bse_code = ?
  AND date BETWEEN ? AND ?  -- 30 days before to 10 days after announcement
ORDER BY date ASC
```

### Date Alignment
- Day 0 = Announcement date (from `upper_circuit_labels.db`)
- Days -1 to -10 = Pre-announcement period
- Days +1 to +5 = Post-announcement period

---

## Edge Cases

### 1. Announcement on Market Holiday
**Scenario**: Announcement date falls on weekend/holiday
**Handling**: Use next trading day as Day 0

### 2. Insufficient Price Data
**Scenario**: Stock recently listed, <30 days of data
**Handling**: Return NaN for features requiring longer history, log warning

### 3. Zero Volume Day
**Scenario**: No trading on announcement day (rare)
**Handling**: Return NaN for volume features, flag anomaly

### 4. Circuit Breaker Hit
**Scenario**: Stock hits upper/lower circuit before normal close
**Handling**: Use circuit price as close, flag in data

### 5. Stock Suspension
**Scenario**: Stock suspended for corporate action
**Handling**: Return NaN for period with no trading, log event

---

## Performance Targets

- **Single Sample**: <5ms per sample
- **Batch (1000 samples)**: <5 seconds (200 samples/second)
- **Full Dataset (200K samples)**: <17 minutes (estimated)

---

## Dependencies

### External Libraries
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `sqlite3` - Database access

### Internal Dependencies
- `historical_prices.db` (Story 1.3)
- `upper_circuit_labels.db` (Story 1.2) - for announcement dates

---

## Definition of Done

- [ ] All 7 acceptance criteria implemented
- [ ] 20 unit tests achieving 100% pass rate
- [ ] Database schema created with indexes
- [ ] Performance test: 1000 samples in <5 seconds
- [ ] Missing data rate ≤5% (measured across all features)
- [ ] Code review: Passes linter, type checking
- [ ] Documentation: Docstrings for all public methods
- [ ] Integration test: Extract features for 10 real companies

---

## Risks & Mitigations

**Risk 1**: Announcement dates may not align with trading days
- **Mitigation**: Use next trading day logic, validate date alignment

**Risk 2**: Volume data quality issues (missing, zero values)
- **Mitigation**: Robust NaN handling, volume validation checks

**Risk 3**: Market-wide events affecting all stocks (budget, policy)
- **Mitigation**: Calculate relative metrics vs index (future enhancement)

---

## Timeline

**Estimated Effort**: 2 days
- Day 1: Write tests (RED phase), implement basic structure
- Day 2: Implement all calculation methods (GREEN phase), refactor

**Start Date**: 2025-11-13
**Target Completion**: 2025-11-15

---

**Author**: VCP Financial Research Team
**Created**: 2025-11-13
**Last Updated**: 2025-11-13
