# SHORT-093: Graceful Shutdown Handler

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Production Deployment

## Problem
System must shutdown cleanly to avoid losing position state or leaving orphaned orders.

## Solution
Signal handler that performs cleanup before shutdown.

## Implementation

### Shutdown Steps
1. **Stop New Orders**: Block new order placement
2. **Cancel Pending**: Cancel all pending orders
3. **Save State**: Persist position and capital state
4. **Close Connections**: Close API, database connections
5. **Flush Logs**: Write remaining logs

### API

```python
from src.deployment.shutdown_handler import ShutdownHandler

handler = ShutdownHandler(
    executor=order_executor,
    account=virtual_account,
    db=database
)

# Register signal handlers
handler.register()

# Manual shutdown
handler.shutdown(reason="User requested")

# Shutdown sequence:
# 1. Block new orders
# 2. Cancel pending orders
# 3. Save state to disk
# 4. Close connections
# 5. Exit gracefully
```

### Signal Handling

```python
import signal

def shutdown_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
    handler.shutdown(reason=f"Signal {signum}")

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)
```

## Test Requirements
- Signal handling
- State persistence
- Order cancellation
- Connection cleanup
- Exit codes

## Dependencies
- signal
- atexit

## Acceptance Criteria
- 🔲 Handles SIGINT, SIGTERM
- 🔲 Cancels pending orders
- 🔲 Saves state
- 🔲 Clean exit
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/deployment/shutdown_handler.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_shutdown_handler.py` (to create)
