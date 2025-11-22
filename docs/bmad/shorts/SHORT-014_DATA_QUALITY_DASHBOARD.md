# SHORT-014: Data Quality Metrics Dashboard

**Parent**: FX-001 (Data Ingestion)
**Estimated Effort**: 6 hours
**Priority**: MEDIUM

## Objective

Create a dashboard/reporting system that tracks and displays data quality metrics across all ingested data sources, providing visibility into data completeness, accuracy, and timeliness.

## Acceptance Criteria

- [ ] AC-1: Track data quality metrics per symbol per source
- [ ] AC-2: Calculate completeness rate (% of expected vs actual data points)
- [ ] AC-3: Track validation failure rates
- [ ] AC-4: Monitor data freshness (time since last update)
- [ ] AC-5: Detect and report data gaps
- [ ] AC-6: Generate summary reports (daily, weekly)
- [ ] AC-7: Export metrics to JSON/CSV

## Test Cases (Write FIRST)

### TC-1: Calculate completeness metrics
```python
def test_calculate_completeness():
    # Given: Data with some gaps
    # When: Calculate completeness
    # Then: Return accurate completeness percentage
```

### TC-2: Track validation failures
```python
def test_track_validation_failures():
    # Given: Mix of valid and invalid data
    # When: Process data
    # Then: Accurately count validation failures
```

### TC-3: Monitor data freshness
```python
def test_monitor_freshness():
    # Given: Data with different timestamps
    # When: Check freshness
    # Then: Correctly identify stale data
```

## Implementation Checklist

- [ ] Write all test cases
- [ ] Run tests (should FAIL)
- [ ] Implement DataQualityDashboard class
- [ ] Implement metric calculation methods
- [ ] Implement report generation
- [ ] Run tests (should PASS)
- [ ] Refactor
- [ ] Code coverage ≥ 95%
- [ ] Documentation

## Dependencies

- SHORT-004 (OHLCV validator)
- SHORT-006 (SQLite data cache)
- SHORT-011 (Data gap detection)

## Definition of Done

- [ ] All tests passing
- [ ] Code coverage ≥ 95%
- [ ] Documentation complete
- [ ] Sample reports generated
