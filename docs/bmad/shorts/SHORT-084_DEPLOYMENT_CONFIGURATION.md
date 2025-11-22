# SHORT-084: Deployment Configuration Management

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Production Deployment

## Problem
Production deployment requires environment-specific configuration for API keys, thresholds, and system parameters.

## Solution
Configuration management system using environment variables and config files.

## Implementation

### Configuration Items
1. **API Credentials**: Angel One keys
2. **Trading Parameters**: Position limits, risk thresholds
3. **System Settings**: Logging, monitoring
4. **Environment**: dev, staging, production

### API

```python
from src.deployment.config_manager import ConfigManager

config = ConfigManager(env="production")

# Access configuration
api_key = config.get("ANGEL_ONE_API_KEY")
max_positions = config.get("MAX_POSITIONS", default=5)
kill_switch_daily_loss = config.get("KILL_SWITCH_DAILY_LOSS_PCT", default=3.0)

# Validate configuration
if not config.validate():
    raise ValueError("Invalid configuration")
```

## Test Requirements
- Config loading
- Environment variable override
- Default values
- Validation
- Multiple environments

## Dependencies
- python-dotenv
- os

## Acceptance Criteria
- 🔲 Loads from .env files
- 🔲 Environment override
- 🔲 Type-safe access
- 🔲 Validation rules
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/deployment/config_manager.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_config_manager.py` (to create)
- Config: `/Users/srijan/Desktop/aksh/.env.example` (to create)
