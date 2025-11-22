# SHORT-088: Production Logging System

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Production Deployment

## Problem
Need comprehensive logging for debugging, audit, and monitoring in production.

## Solution
Structured logging system with rotation, levels, and formatting.

## Implementation

### Features
1. **Structured Logging**: JSON format for parsing
2. **Log Rotation**: Daily rotation with compression
3. **Multiple Handlers**: File, console, syslog
4. **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
5. **Contextual Info**: Request ID, user, component

### API

```python
from src.deployment.logging_config import setup_logging
import logging

# Initialize logging
setup_logging(
    level="INFO",
    log_file="/var/log/vcp/trading.log",
    json_format=True
)

# Get logger
logger = logging.getLogger(__name__)

# Structured logging
logger.info(
    "Order placed",
    extra={
        "order_id": "ORD_123",
        "symbol": "RELIANCE",
        "quantity": 10,
        "price": 2500.0
    }
)

# Error with context
logger.error(
    "API call failed",
    extra={"api": "angel_one", "error_code": 500},
    exc_info=True
)
```

## Test Requirements
- Logger initialization
- Multiple handlers
- Log rotation
- JSON formatting
- Context inclusion

## Dependencies
- python-json-logger
- logging.handlers

## Acceptance Criteria
- 🔲 Structured JSON logs
- 🔲 Rotation enabled
- 🔲 Multiple outputs
- 🔲 Contextual data
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/deployment/logging_config.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_logging_config.py` (to create)
- Config: `/Users/srijan/Desktop/aksh/config/logging.yaml` (to create)
