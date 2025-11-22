# SHORT-096: Rate Limit Protection

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Production Deployment

## Problem
Must prevent API rate limit violations that could result in temporary bans.

## Solution
Centralized rate limiter with per-endpoint limits and adaptive throttling.

## Implementation

### Features
1. **Per-Endpoint Limits**: Different limits for different APIs
2. **Token Bucket**: Smooth rate limiting
3. **Adaptive Throttling**: Slow down on 429 errors
4. **Queue Management**: Buffer requests during spikes

### API

```python
from src.deployment.rate_limit_manager import RateLimitManager

rate_limiter = RateLimitManager({
    "angel_api_orders": {"calls": 10, "period": 60},  # 10/min
    "angel_api_data": {"calls": 100, "period": 60},   # 100/min
    "yahoo_finance": {"calls": 2000, "period": 3600}  # 2000/hour
})

# Wait for rate limit availability
@rate_limiter.limit("angel_api_orders")
def place_order():
    return angel_client.place_order(...)

# Manual check
if rate_limiter.can_call("angel_api_data"):
    data = fetch_data()
else:
    wait_time = rate_limiter.time_until_available("angel_api_data")
    logger.info(f"Rate limited, waiting {wait_time}s")
```

## Test Requirements
- Rate limiting enforcement
- Token replenishment
- Multi-endpoint limits
- Adaptive throttling
- Statistics

## Dependencies
- SHORT-008 (Rate Limiter) - enhance existing
- time
- threading

## Acceptance Criteria
- 🔲 Per-endpoint limits
- 🔲 Token bucket algorithm
- 🔲 Adaptive throttling
- 🔲 Statistics tracking
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/deployment/rate_limit_manager.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_rate_limit_manager.py` (to create)
