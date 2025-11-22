# SHORT-015: Historical Data Backfill Utility

**Parent**: FX-001 (Data Ingestion)
**Estimated Effort**: 5 hours
**Priority**: HIGH

## Objective

Create a utility to backfill historical OHLCV data for symbols, handling date ranges, data gaps, and incremental updates efficiently.

## Acceptance Criteria

- [ ] AC-1: Backfill data for specified date range
- [ ] AC-2: Detect existing data and only fill gaps
- [ ] AC-3: Support incremental backfill (only fetch missing dates)
- [ ] AC-4: Handle weekends and market holidays
- [ ] AC-5: Persist backfilled data to cache
- [ ] AC-6: Track backfill progress and errors
- [ ] AC-7: Support batch backfilling multiple symbols

## Test Cases (Write FIRST)

### TC-1: Backfill full date range
```python
def test_backfill_full_range():
    # Given: Symbol with no data
    # When: Backfill date range
    # Then: All dates fetched and cached
```

### TC-2: Incremental backfill
```python
def test_incremental_backfill():
    # Given: Symbol with partial data
    # When: Backfill same range
    # Then: Only missing dates fetched
```

### TC-3: Handle market holidays
```python
def test_skip_market_holidays():
    # Given: Date range with holidays
    # When: Backfill
    # Then: Holidays skipped appropriately
```

## Implementation Checklist

- [ ] Write all test cases
- [ ] Run tests (should FAIL)
- [ ] Implement HistoricalBackfillUtility class
- [ ] Implement gap detection logic
- [ ] Implement incremental fetch
- [ ] Run tests (should PASS)
- [ ] Refactor
- [ ] Code coverage ≥ 95%
- [ ] Documentation

## Dependencies

- SHORT-006 (SQLite data cache)
- SHORT-007 (Data source fallback)
- SHORT-011 (Data gap detection)
- SHORT-013 (Batch symbol loader)

## Definition of Done

- [ ] All tests passing
- [ ] Code coverage ≥ 95%
- [ ] Documentation complete
- [ ] CLI utility created
