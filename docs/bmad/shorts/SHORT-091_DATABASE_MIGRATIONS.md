# SHORT-091: Database Migration System

**Status**: 🔲 Not Started
**TDD Status**: 🔲 Tests Required
**Iteration**: 1
**Category**: Production Deployment

## Problem
Need versioned database schema changes for safe production updates.

## Solution
Migration system for SQLite schema evolution with rollback support.

## Implementation

### Features
1. **Version Control**: Sequential migration files
2. **Up/Down Migrations**: Apply and rollback
3. **Migration History**: Track applied migrations
4. **Validation**: Check schema consistency

### Migration Format

```python
# migrations/001_create_trades_table.py

def up(connection):
    """Apply migration"""
    connection.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            order_id TEXT UNIQUE,
            symbol TEXT,
            quantity INTEGER,
            price REAL,
            timestamp DATETIME
        )
    """)

def down(connection):
    """Rollback migration"""
    connection.execute("DROP TABLE IF EXISTS trades")
```

### API

```python
from src.deployment.migrations import MigrationManager

manager = MigrationManager(db_path="vcp_trading.db")

# Apply all pending migrations
manager.migrate()

# Rollback last migration
manager.rollback()

# Check migration status
status = manager.status()
# [
#   {"version": 1, "name": "create_trades_table", "applied": True},
#   {"version": 2, "name": "add_pnl_column", "applied": False}
# ]
```

## Test Requirements
- Migration application
- Rollback functionality
- Version tracking
- Error handling
- Schema validation

## Dependencies
- sqlite3

## Acceptance Criteria
- 🔲 Sequential migrations
- 🔲 Up/down support
- 🔲 Version tracking
- 🔲 Rollback capability
- 🔲 90%+ test coverage

## Files
- Implementation: `/Users/srijan/Desktop/aksh/src/deployment/migrations.py` (to create)
- Tests: `/Users/srijan/Desktop/aksh/tests/test_migrations.py` (to create)
- Migrations: `/Users/srijan/Desktop/aksh/migrations/` (to create)
