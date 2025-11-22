# SHORT-095: Error Recovery System

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Production Deployment

## Problem
System must recover gracefully from API failures, network errors, and transient issues.

## Solution
Error recovery system with retry logic, circuit breakers, and fallback strategies.

## Implementation

### Recovery Strategies
1. **Exponential Backoff**: Retry with increasing delays
2. **Circuit Breaker**: Stop calling failing APIs
3. **Fallback**: Switch to backup data sources
4. **State Recovery**: Reload from last known good state

### API

```python
from src.deployment.error_recovery import RecoveryManager

recovery = RecoveryManager()

# Retry with exponential backoff
@recovery.retry(max_attempts=3, backoff=2.0)
def fetch_data():
    return angel_client.get_ohlcv(...)

# Circuit breaker
@recovery.circuit_breaker(failure_threshold=5, timeout=60)
def place_order():
    return angel_client.place_order(...)

# Fallback
@recovery.fallback(fallback_func=use_yahoo_finance)
def get_price(symbol):
    return angel_client.get_ltp(symbol)

# Manual recovery
if recovery.is_circuit_open("angel_api"):
    logger.warning("Angel API circuit open, using fallback")
    use_fallback_data_source()
```

## Test Requirements
- Retry logic
- Circuit breaker
- Fallback execution
- State recovery
- Error logging

## Dependencies
- SHORT-007 (Data Source Fallback)
- tenacity (retry library)

## Acceptance Criteria
- 🔲 Exponential backoff
- 🔲 Circuit breaker
- 🔲 Fallback support
- 🔲 Error context
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/deployment/error_recovery.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_error_recovery.py` (to create)
