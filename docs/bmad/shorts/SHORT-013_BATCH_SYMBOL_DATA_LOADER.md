# SHORT-013: Batch Symbol Data Loader

**Parent**: FX-001 (Data Ingestion)
**Estimated Effort**: 4 hours
**Priority**: HIGH

## Objective

Implement a batch data loader that can efficiently fetch OHLCV data for multiple symbols concurrently with proper rate limiting, error handling, and progress tracking.

## Acceptance Criteria

- [ ] AC-1: Load data for multiple symbols concurrently (configurable max workers)
- [ ] AC-2: Respect rate limits across all workers
- [ ] AC-3: Track progress and report status for each symbol
- [ ] AC-4: Handle individual symbol failures without stopping entire batch
- [ ] AC-5: Return structured results with success/failure status per symbol
- [ ] AC-6: Support retry logic for failed symbols
- [ ] AC-7: Validate all fetched data before returning

## Test Cases (Write FIRST)

### TC-1: Load multiple symbols successfully
```python
def test_batch_load_success():
    # Given: List of valid symbols
    # When: Batch loading data
    # Then: All symbols return valid OHLCV data
```

### TC-2: Handle partial failures
```python
def test_batch_load_partial_failure():
    # Given: Mix of valid and invalid symbols
    # When: Batch loading data
    # Then: Valid symbols succeed, invalid fail gracefully
```

### TC-3: Respect rate limits
```python
def test_batch_load_respects_rate_limit():
    # Given: Many symbols and strict rate limit
    # When: Batch loading data
    # Then: Rate limit not exceeded
```

### TC-4: Retry failed symbols
```python
def test_batch_load_retry_logic():
    # Given: Symbols that fail initially
    # When: Retry enabled
    # Then: Failed symbols retried up to max attempts
```

## Implementation Checklist

- [ ] Write all test cases
- [ ] Run tests (should FAIL)
- [ ] Implement BatchSymbolDataLoader class
- [ ] Implement concurrent fetching with ThreadPoolExecutor
- [ ] Implement progress tracking
- [ ] Implement retry logic
- [ ] Run tests (should PASS)
- [ ] Refactor
- [ ] Code coverage ≥ 95%
- [ ] Documentation

## Dependencies

- SHORT-002 (Angel One OHLCV fetcher)
- SHORT-003 (Yahoo Finance fetcher)
- SHORT-004 (OHLCV validator)
- SHORT-007 (Data source fallback)
- SHORT-008 (Rate limiter)

## Definition of Done

- [ ] All tests passing
- [ ] Code coverage ≥ 95%
- [ ] Documentation complete
- [ ] Integrated with data ingestion system
