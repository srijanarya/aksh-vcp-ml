# SHORT-094: State Persistence System

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Production Deployment

## Problem
System must persist state across restarts to maintain positions and capital.

## Solution
State persistence layer that saves and loads critical state to disk.

## Implementation

### Persisted State
1. **Positions**: Open positions with entry data
2. **Capital**: Available cash
3. **Orders**: Pending orders
4. **Performance**: Metrics and P&L

### Storage Format
- JSON for readability
- Atomic writes (temp file + rename)
- Versioning
- Checksums

### API

```python
from src.deployment.state_manager import StateManager

state = StateManager(state_file="/opt/vcp/state.json")

# Save state
state.save({
    "capital": 95000,
    "positions": [
        {"symbol": "RELIANCE", "quantity": 10, "entry_price": 2500}
    ],
    "pending_orders": ["ORD_123"],
    "metrics": {"total_pnl": 5000}
})

# Load state
loaded_state = state.load()

# Validate state
if not state.validate(loaded_state):
    logger.error("State file corrupted, using defaults")
    loaded_state = state.get_default_state()
```

## Test Requirements
- State save
- State load
- Atomic writes
- Corruption handling
- Version compatibility

## Dependencies
- json
- pathlib

## Acceptance Criteria
- 🔲 Persists all state
- 🔲 Atomic writes
- 🔲 Load validation
- 🔲 Corruption recovery
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/deployment/state_manager.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_state_manager.py` (to create)
