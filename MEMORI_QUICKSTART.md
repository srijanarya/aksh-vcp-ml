# Memori Quick Start Guide

Get your VCP agents remembering in 5 minutes! 🚀

---

## Prerequisites

```bash
# Ensure you have Python 3.9+
python3 --version

# Ensure OpenAI API key is set
echo $OPENAI_API_KEY
```

---

## Step 1: Install Dependencies (30 seconds)

```bash
cd /Users/srijan/Desktop/aksh
pip install memorisdk loguru
```

✅ Already done if you ran the integration!

---

## Step 2: Test Integration (1 minute)

```bash
python3 enable_memory.py
```

**Expected output:**
```
✅ OPENAI_API_KEY found ✓
✅ Memory modules imported successfully ✓
✅ Global memory enabled ✓
✅ Memory instance created successfully ✓
✅ Orchestrator memory integration successful ✓
```

---

## Step 3: Use Memory-Enabled Agents (2 minutes)

### Example 1: Orchestrator with Memory

```python
from agents.ml.ml_master_orchestrator import MLMasterOrchestrator

# Initialize (memory auto-enabled)
orchestrator = MLMasterOrchestrator()

# Verify memory
if orchestrator.memori:
    print("✅ Memory enabled!")

# Use normally - memory works transparently
report = orchestrator.orchestrate_training_pipeline("xgboost")
```

### Example 2: Store VCP Pattern

```python
from src.memory.vcp_memory_tools import VCPMemoryTools

vcp = VCPMemoryTools()
vcp.store_vcp_pattern(
    ticker="TCS.NS",
    pattern_data={
        "contraction_pct": 65.0,
        "breakout_price": 3850.0
    }
)
```

### Example 3: Remember Past Analysis

```python
from src.memory import remember

# Simple memory search
results = remember("What stocks had VCP patterns last month?")
print(results)
```

---

## Step 4: Check Memory Database (30 seconds)

```bash
# View database
ls -lh data/agent_memory.db

# Query memories (optional)
sqlite3 data/agent_memory.db "SELECT COUNT(*) FROM conversations;"
```

---

## What's Next?

Your system now has persistent memory! 🎉

### Immediate Benefits:
- ✅ Orchestrator remembers past training runs
- ✅ VCP patterns stored and searchable
- ✅ Agents learn from past successes/failures

### Future Enhancements:
- Add memory to individual agents (MLTrainingAgent, etc.)
- Build pattern library with similarity search
- Memory-driven hyperparameter optimization

### Learn More:
- Full docs: [MEMORI_INTEGRATION.md](MEMORI_INTEGRATION.md)
- Configuration: [src/memory/memori_config.py](src/memory/memori_config.py)
- VCP tools: [src/memory/vcp_memory_tools.py](src/memory/vcp_memory_tools.py)

---

## Common Issues

### "Memori not available"
```bash
pip install memorisdk
```

### "No OpenAI API key"
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### "Database not found"
```bash
mkdir -p data
python3 enable_memory.py
```

---

## Support

Questions? Check:
1. [MEMORI_INTEGRATION.md](MEMORI_INTEGRATION.md) - Full documentation
2. [Memori GitHub](https://github.com/GibsonAI/Memori) - SDK issues
3. System logs - `python3 enable_memory.py` for diagnostics

---

**That's it!** Your VCP system now has a memory. 🧠
