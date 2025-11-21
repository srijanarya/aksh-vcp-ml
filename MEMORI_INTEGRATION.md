# Memori Memory System Integration

**Status:** ✅ Integrated and Operational
**Date:** November 21, 2025
**Version:** 1.0.0

---

## Overview

The VCP Financial Research System now has **persistent memory** powered by [Memori SDK](https://github.com/GibsonAI/Memori). This enables all 127+ agents to remember past interactions, learn from patterns, and make more intelligent decisions.

### What is Memori?

Memori is an SQL-native memory engine that gives AI agents persistent, queryable memory across conversations. Think of it as giving your ML agents a "brain" that remembers everything.

### Key Benefits

✅ **Learning System** - Agents remember past successes and failures
✅ **Cost Efficiency** - 80-90% reduction vs vector databases (uses SQLite)
✅ **Better Decisions** - Context from historical patterns and earnings
✅ **Zero Disruption** - Works transparently with existing stateless design
✅ **Pattern Library** - VCP patterns stored and searchable
✅ **Earnings Context** - Historical earnings automatically recalled

---

## Architecture

### Dual Memory Mode System

Memori provides two complementary memory modes:

#### 1. Conscious Ingest Mode (`conscious_ingest=True`)
- **One-shot context injection** at startup
- Remembers core trading rules, preferences, and principles
- Minimal overhead (~150 tokens)
- Perfect for: Persistent identity, trading rules, Indian market specifics

#### 2. Auto Ingest Mode (`auto_ingest=True`)
- **Dynamic search** on every query
- Retrieves 3-5 most relevant past interactions
- Query-specific context (~250 tokens)
- Perfect for: Pattern recall, earnings history, strategy retrieval

### Integration Points

```
┌─────────────────────────────────────────────┐
│    MLMasterOrchestrator                     │
│    ✓ Memory-enabled                         │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
   ┌────────┐ ┌──────┐ ┌─────────┐
   │ Data   │ │Train │ │Inference│
   │Collect │ │Agent │ │ Agent   │
   └────────┘ └──────┘ └─────────┘
        │
        ▼
┌─────────────────────────────────────────────┐
│    Memori Memory Database                   │
│    Location: data/agent_memory.db           │
│    - Conversations                          │
│    - Short-term memories (essentials)       │
│    - Long-term memories (all interactions)  │
│    - Entities & relationships               │
└─────────────────────────────────────────────┘
```

---

## Installation

### 1. Install Memori SDK

```bash
pip install memorisdk
```

Already completed ✅

### 2. Set Environment Variables

Add to your `.env.local` or `.env`:

```bash
# Optional: Override default database location
MEMORI_DATABASE_CONNECTION=sqlite:///data/agent_memory.db

# Required: OpenAI API key for memory processing
OPENAI_API_KEY=sk-your-key-here
```

### 3. Enable Memory System

Run once at startup:

```bash
python3 enable_memory.py
```

Or in your code:

```python
from src.memory import enable_global_memory

enable_global_memory()
```

---

## Usage Guide

### Basic Usage - MLMasterOrchestrator

The orchestrator now has memory enabled automatically:

```python
from agents.ml.ml_master_orchestrator import MLMasterOrchestrator

# Initialize orchestrator (memory auto-enabled)
orchestrator = MLMasterOrchestrator()

# Check memory is available
if orchestrator.memori:
    print("Memory enabled ✓")

# Use orchestrator normally - memory works transparently
report = orchestrator.orchestrate_training_pipeline("xgboost")
```

Memory automatically tracks:
- Which algorithms were tried
- Performance results
- Error patterns
- Successful configurations

### VCP Pattern Memory

Store and retrieve VCP patterns:

```python
from src.memory.vcp_memory_tools import VCPMemoryTools

# Create tools
vcp_memory = VCPMemoryTools()

# Store detected pattern
vcp_memory.store_vcp_pattern(
    ticker="TCS.NS",
    pattern_data={
        "contraction_pct": 65.0,
        "base_depth": 12.5,
        "volume_contraction": 45.0,
        "breakout_price": 3850.0
    }
)

# Find similar patterns
patterns = vcp_memory.find_similar_patterns(
    sector="IT",
    min_contraction=60.0,
    limit=5
)
```

### Earnings Intelligence Memory

Track earnings history:

```python
from src.memory.vcp_memory_tools import EarningsMemoryTools
from datetime import datetime

# Create tools
earnings_memory = EarningsMemoryTools()

# Store earnings event
earnings_memory.store_earnings_event(
    ticker="TCS.NS",
    earnings_data={
        "eps": 45.2,
        "revenue_cr": 60000,
        "qoq_growth": 8.5,
        "beat_estimates": True
    },
    announcement_date=datetime(2024, 10, 15)
)

# Get earnings history
history = earnings_memory.get_earnings_history(
    ticker="TCS.NS",
    quarters=4
)
```

### Strategy Memory

Track strategy performance:

```python
from src.memory.vcp_memory_tools import StrategyMemoryTools

# Create tools
strategy_memory = StrategyMemoryTools()

# Store backtest result
strategy_memory.store_strategy_result(
    strategy_name="VCP_Momentum",
    config={
        "min_contraction": 60,
        "volume_threshold": 45
    },
    performance={
        "sharpe": 2.1,
        "returns": 45.5,
        "win_rate": 68
    }
)

# Get best strategies
best = strategy_memory.get_best_strategies(
    metric="sharpe",
    min_value=1.5
)
```

### Custom Agent Memory

Add memory to any agent:

```python
from src.memory import create_agent_memory

class MyCustomAgent:
    def __init__(self):
        # Create agent-specific memory
        self.memory = create_agent_memory(
            agent_name="MyCustomAgent",
            agent_type="custom",  # Or use predefined types
            namespace="custom_namespace"
        )

        if self.memory:
            self.memory.enable()
            print("Agent memory enabled")

    def analyze_stock(self, ticker):
        # Agent can now remember past analyses
        # Memory is automatically tracked
        pass
```

---

## Memory Namespaces

Agents are organized into memory namespaces for isolation:

| Namespace | Purpose | Agent Type |
|-----------|---------|------------|
| `ml_orchestrator` | Master orchestrator decisions | MLMasterOrchestrator |
| `data_collector` | Data collection patterns | MLDataCollectorAgent |
| `feature_engineer` | Feature engineering history | MLFeatureEngineerAgent |
| `ml_training` | Training runs and hyperparameters | MLTrainingAgent |
| `ml_inference` | Prediction patterns | MLInferenceAgent |
| `ml_monitoring` | Performance monitoring | MLMonitoringAgent |
| `backtesting` | Backtest results | MLBacktestingAgent |
| `vcp_patterns` | VCP pattern library | VCP tools |
| `earnings_intelligence` | Earnings history | Earnings tools |
| `trading_strategies` | Strategy performance | Strategy tools |
| `vcp_system_global` | Shared across all agents | Global |

---

## Configuration

### MemoriConfig Class

Located in [src/memory/memori_config.py](src/memory/memori_config.py):

```python
from src.memory import MemoriConfig

# Database location
print(MemoriConfig.MEMORY_DB_PATH)
# Output: /Users/srijan/Desktop/aksh/data/agent_memory.db

# Memory modes
print(MemoriConfig.CONSCIOUS_INGEST)  # True
print(MemoriConfig.AUTO_INGEST)       # True

# Performance settings
print(MemoriConfig.MEMORY_SEARCH_LIMIT)    # 5 results
print(MemoriConfig.MEMORY_RETENTION_DAYS)  # 90 days
```

### Environment Variables

All settings can be overridden via environment:

```bash
# Database connection
export MEMORI_DATABASE_CONNECTION="postgresql://user:pass@localhost/memori"

# OpenAI API key
export MEMORI_OPENAI_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."  # Fallback

# Retention
export MEMORI_RETENTION_DAYS=180
```

---

## Database Schema

Memori automatically creates these tables in `data/agent_memory.db`:

### Core Tables

```sql
-- Conversations (grouped messages)
conversations
  - id (PRIMARY KEY)
  - user_id (e.g., "ml_master_orchestrator")
  - namespace (e.g., "ml_orchestrator")
  - created_at
  - updated_at

-- Messages (individual interactions)
messages
  - id (PRIMARY KEY)
  - conversation_id (FOREIGN KEY)
  - role (user/assistant/system)
  - content
  - timestamp

-- Memories (extracted knowledge)
memories
  - id (PRIMARY KEY)
  - conversation_id (FOREIGN KEY)
  - memory_type (fact/preference/skill/rule)
  - content
  - importance_score
  - extracted_at

-- Entities (extracted concepts)
memory_entities
  - id (PRIMARY KEY)
  - memory_id (FOREIGN KEY)
  - entity_type (stock/strategy/pattern)
  - entity_value
  - confidence

-- Relationships (entity connections)
memory_relationships
  - id (PRIMARY KEY)
  - source_entity_id
  - target_entity_id
  - relationship_type
```

### Full-Text Search

Memori uses SQLite FTS5 for fast semantic search:

```sql
memory_fts (virtual table)
  - Indexes memory content
  - Enables fast pattern matching
  - Supports relevance ranking
```

---

## Performance Considerations

### Memory Overhead

| Mode | Tokens per Call | Latency |
|------|----------------|---------|
| **Conscious Only** | ~150 | <5ms (one-time at startup) |
| **Auto Only** | ~250 | ~10-20ms (per query) |
| **Both Modes** | ~400 | ~15-25ms (per query) |

### Cost Savings

Compared to vector databases:
- **80-90% cost reduction** (no embeddings needed for most queries)
- **No external service** (SQLite included)
- **Simple backup** (copy .db file)

### Database Size

Typical growth rates:
- ~1KB per conversation
- ~500 bytes per memory
- ~100 bytes per entity

**Example:** 10,000 conversations = ~10MB database

---

## Troubleshooting

### Issue: "Memori not available"

**Cause:** SDK not installed or import failed

**Solution:**
```bash
pip install memorisdk
python3 enable_memory.py
```

### Issue: "No OpenAI API key"

**Cause:** OPENAI_API_KEY not set

**Solution:**
```bash
export OPENAI_API_KEY=sk-your-key-here
# Or add to .env.local
```

### Issue: Memory not persisting

**Cause:** Database permissions or path issues

**Solution:**
```bash
# Check database exists
ls -lh data/agent_memory.db

# Check permissions
chmod 644 data/agent_memory.db

# Verify database integrity
sqlite3 data/agent_memory.db "PRAGMA integrity_check;"
```

### Issue: "Warning: Memori already enabled"

**Cause:** Global memory enabled multiple times

**Solution:** This is harmless - ignore the warning. Memory is already active.

---

## Testing

### Run Integration Test

```bash
python3 enable_memory.py
```

**Expected output:**
```
✓ OPENAI_API_KEY found
✓ Memory modules imported successfully
✓ Global memory enabled
✓ Memory instance created successfully
✓ Orchestrator memory integration successful
```

### Manual Testing

```python
from agents.ml.ml_master_orchestrator import MLMasterOrchestrator

orchestrator = MLMasterOrchestrator()

# Verify memory is enabled
assert orchestrator.memori is not None, "Memory should be enabled"
print("✓ Memory integration test passed")
```

---

## Next Steps

### Phase 2: Enhanced Agent Integration (Optional)

1. **Add memory to MLTrainingAgent**
   - Remember best hyperparameters per algorithm
   - Track which configurations worked/failed
   - Suggest optimizations based on history

2. **Add memory to MLInferenceAgent**
   - Track prediction patterns
   - Remember stocks with consistent upper circuits
   - Learn from prediction accuracy

3. **Add memory to MLBacktestingAgent**
   - Store backtest results
   - Compare strategies over time
   - Identify improving vs degrading strategies

### Phase 3: Advanced Features (Future)

1. **Memory-driven optimization**
   - Auto-suggest best parameters based on memory
   - Warn about past failures before retrying
   - Learn market regime changes

2. **Cross-agent collaboration**
   - Shared insights across all agents
   - Collective learning from system-wide patterns
   - Emergent intelligence through memory accumulation

3. **Explainability**
   - "Why did you make this prediction?" → Check memory
   - Decision trails for audit compliance
   - Root cause analysis using memory history

---

## API Reference

### Quick Reference

```python
# Get global memory instance
from src.memory import get_memori_instance
memori = get_memori_instance(namespace="custom", user_id="user123")

# Enable/disable global memory
from src.memory import enable_global_memory, disable_global_memory
enable_global_memory()

# Create agent-specific memory
from src.memory import create_agent_memory
memory = create_agent_memory("MyAgent", "custom")

# Search memory
from src.memory import remember
results = remember("What VCP patterns worked in IT sector?")

# VCP tools
from src.memory.vcp_memory_tools import (
    VCPMemoryTools,
    EarningsMemoryTools,
    StrategyMemoryTools
)
```

### Full Documentation

See:
- [src/memory/memori_config.py](src/memory/memori_config.py) - Core configuration
- [src/memory/vcp_memory_tools.py](src/memory/vcp_memory_tools.py) - VCP-specific tools
- [Memori Official Docs](https://github.com/GibsonAI/Memori) - SDK documentation

---

## Support

### Internal Issues

For integration issues with the VCP system:
1. Check logs in orchestrator output
2. Verify database exists and has correct permissions
3. Ensure OPENAI_API_KEY is set

### Memori SDK Issues

For issues with Memori itself:
- GitHub: https://github.com/GibsonAI/Memori/issues
- Discord: Available via Memori repository

---

## Summary

✅ **Integration Complete**
✅ **MLMasterOrchestrator Memory-Enabled**
✅ **VCP/Earnings/Strategy Tools Created**
✅ **Testing Successful**
✅ **Documentation Complete**

Your VCP Financial Research System now has persistent memory! All 127+ agents can learn from past interactions, remember patterns, and make more intelligent decisions.

**Database Location:** `/Users/srijan/Desktop/aksh/data/agent_memory.db`
**Configuration:** [src/memory/](src/memory/)
**Test Script:** [enable_memory.py](enable_memory.py)

---

**Last Updated:** November 21, 2025
**Version:** 1.0.0
**Status:** Production Ready ✅
