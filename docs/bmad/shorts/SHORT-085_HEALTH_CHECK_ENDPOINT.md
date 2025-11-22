# SHORT-085: Health Check Endpoint

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Production Deployment

## Problem
Need health check endpoint for monitoring system status and detecting failures.

## Solution
Health check service that monitors critical components and dependencies.

## Implementation

### Health Checks
1. **Angel One API**: Connection status
2. **Database**: SQLite connectivity
3. **Kill Switch**: Current status
4. **System Resources**: Memory, disk

### API

```python
from src.deployment.health_check import HealthChecker

checker = HealthChecker(
    angel_client=client,
    database=db,
    executor=executor
)

# Run health check
status = checker.check_health()

# Response format
# {
#   "status": "healthy" | "unhealthy",
#   "checks": {
#     "angel_api": "ok",
#     "database": "ok",
#     "kill_switch": "active",
#     "memory": "ok"
#   },
#   "timestamp": "2024-11-01T14:30:00Z"
# }
```

## Test Requirements
- All checks passing
- Individual check failure
- Aggregated status
- Timestamp inclusion
- Error handling

## Dependencies
- SHORT-001 (Angel One Auth)
- SHORT-063 (Kill Switch)
- psutil (for system metrics)

## Acceptance Criteria
- 🔲 Checks all components
- 🔲 Returns status dict
- 🔲 Detects failures
- 🔲 Includes timestamp
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/deployment/health_check.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_health_check.py` (to create)
