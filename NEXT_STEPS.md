# Next Steps - Using Your New RAG + Workflow System

## ✅ What's Complete

Phases 1 & 2 are **production-ready**:
- ✅ RAG system for earnings documents (semantic search)
- ✅ 4-stage VCP workflow (automated analysis)
- ✅ 35/35 tests passing
- ✅ Complete documentation
- ✅ Zero breaking changes

---

## 🚀 Start Using It NOW

### Step 1: Set API Key (Required)
```bash
export OPENAI_API_KEY='your-openai-api-key-here'
```

### Step 2: Verify Everything Works
```bash
# Run all tests (should see 35 passed)
python3 -m pytest tests/unit/test_earnings_rag.py tests/unit/test_vcp_workflow.py -v
```

### Step 3: Try the VCP Workflow
```bash
# Quick test with Python one-liner
python3 -c "
from agents.workflows.vcp_workflow import run_vcp_analysis
result = run_vcp_analysis('TCS', 'NSE')
print('Success:', result.success)
print('Confidence:', f'{result.confidence_score:.1%}')
print('\\nRecommendation:')
print(result.final_recommendation)
"
```

### Step 4: Add Your Earnings PDFs
```bash
# Create directory if needed
mkdir -p data/earnings_pdfs

# Add your PDFs with this naming convention:
# TCS_Q4FY24_Results.pdf
# INFY_Q3FY24_Earnings.pdf
# WIPRO_Q2FY25_Presentation.pdf

# Then ingest them
python3 src/rag/earnings_ingestion.py data/earnings_pdfs
```

### Step 5: Query Your Earnings Data
```bash
python3 -c "
from src.rag.earnings_query import get_earnings_query_engine

engine = get_earnings_query_engine()

# Semantic search
result = engine.query('Which companies showed strong QoQ revenue growth?')
print('Answer:', result.response)

# Company-specific search
tcs_result = engine.search_by_company('TCS', 'What was the profit margin trend?')
print('\\nTCS Analysis:', tcs_result.response if tcs_result else 'No data found')
"
```

---

## 📖 Full Code Examples

### Example 1: Basic VCP Analysis
```python
from agents.workflows.vcp_workflow import run_vcp_analysis

# Analyze a stock
result = run_vcp_analysis("TCS", "NSE")

if result.success:
    signal_stage = result.get_stage("SignalGenerator")
    signal = signal_stage.data.get("signal")
    entry = signal_stage.data.get("entry_price")
    stop = signal_stage.data.get("stop_loss")
    target = signal_stage.data.get("target_price")

    print(f"Signal: {signal}")
    print(f"Entry: ₹{entry:.2f}")
    print(f"Stop Loss: ₹{stop:.2f}")
    print(f"Target: ₹{target:.2f}")
    print(f"Confidence: {result.confidence_score:.1%}")
else:
    print("Analysis failed:", result.error)
```

### Example 2: Async VCP Analysis (Faster)
```python
from agents.workflows import get_vcp_workflow
import asyncio

async def analyze_multiple_stocks(symbols):
    workflow = get_vcp_workflow(use_memory=True)

    for symbol in symbols:
        result = await workflow.run(symbol, "NSE")

        print(f"\n{'='*50}")
        print(f"Analysis: {symbol}")
        print(f"{'='*50}")

        for stage in result.stages:
            status = "✓" if stage.success else "✗"
            print(f"{status} {stage.stage_name}: {stage.execution_time:.2f}s")

        print(f"\nConfidence: {result.confidence_score:.1%}")
        print(result.final_recommendation)

# Run
symbols = ["TCS", "INFY", "WIPRO"]
asyncio.run(analyze_multiple_stocks(symbols))
```

### Example 3: Combined RAG + Workflow
```python
from agents.workflows import get_vcp_workflow
from src.rag.earnings_query import get_earnings_query_engine
import asyncio

async def deep_analysis(symbol):
    # 1. VCP technical analysis
    workflow = get_vcp_workflow()
    vcp_result = await workflow.run(symbol, "NSE")

    # 2. Earnings fundamental analysis
    engine = get_earnings_query_engine()
    earnings = engine.search_by_company(
        symbol,
        "Provide QoQ earnings trends, profit margins, and growth quality"
    )

    # 3. Combined decision
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE ANALYSIS: {symbol}")
    print(f"{'='*60}")

    # Technical
    signal_stage = vcp_result.get_stage("SignalGenerator")
    if signal_stage:
        print(f"\n📊 Technical Analysis:")
        print(f"  Signal: {signal_stage.data.get('signal')}")
        print(f"  VCP Detected: {vcp_result.get_stage('PatternDetector').data.get('vcp_detected')}")
        print(f"  Entry: ₹{signal_stage.data.get('entry_price'):.2f}")
        print(f"  Target: ₹{signal_stage.data.get('target_price'):.2f}")
        print(f"  Risk/Reward: {signal_stage.data.get('risk_reward_ratio'):.2f}")

    # Fundamental
    print(f"\n📈 Fundamental Analysis:")
    if earnings:
        print(f"  {earnings.response}")
    else:
        print("  No earnings data available")

    # Final
    print(f"\n💡 Final Recommendation:")
    print(f"  Confidence: {vcp_result.confidence_score:.1%}")
    print(f"  {vcp_result.final_recommendation}")

# Run
asyncio.run(deep_analysis("TCS"))
```

### Example 4: Batch Analysis with CSV Export
```python
from agents.workflows.vcp_workflow import run_vcp_analysis
import pandas as pd

# Analyze multiple stocks
stocks = ["TCS", "INFY", "WIPRO", "TECHM", "HCLTECH"]
results = []

for stock in stocks:
    print(f"Analyzing {stock}...")
    result = run_vcp_analysis(stock, "NSE")

    if result.success:
        signal_stage = result.get_stage("SignalGenerator")
        results.append({
            "Symbol": stock,
            "Signal": signal_stage.data.get("signal"),
            "Confidence": f"{result.confidence_score:.1%}",
            "Entry": signal_stage.data.get("entry_price"),
            "Target": signal_stage.data.get("target_price"),
            "Stop Loss": signal_stage.data.get("stop_loss"),
            "Risk/Reward": signal_stage.data.get("risk_reward_ratio"),
            "VCP Detected": result.get_stage("PatternDetector").data.get("vcp_detected")
        })

# Export to CSV
df = pd.DataFrame(results)
df.to_csv("vcp_analysis_results.csv", index=False)
print(f"\nResults saved to vcp_analysis_results.csv")
print(df.to_string(index=False))
```

---

## 📚 Documentation Reference

### Quick Start
- **File**: `QUICK_START_RAG_WORKFLOW.md`
- **Purpose**: Get started in 5 minutes
- **Contains**: Installation, basic usage, troubleshooting

### Complete Technical Guide
- **File**: `INTEGRATION_COMPLETE_PHASE_1_2.md`
- **Purpose**: Deep technical documentation
- **Contains**: Architecture, API reference, integration examples

### RAG-Specific Documentation
- **File**: `src/rag/README.md`
- **Purpose**: RAG system details
- **Contains**: Vector store config, ingestion pipeline, query engine

### Session Summary
- **File**: `SESSION_SUMMARY_RAG_WORKFLOW.md`
- **Purpose**: High-level overview of what was built
- **Contains**: Achievements, test results, file listing

### Completion Summary
- **File**: `PHASES_1_2_COMPLETE.md`
- **Purpose**: Production readiness checklist
- **Contains**: Acceptance criteria, performance benchmarks

---

## 🐛 Common Issues & Solutions

### Issue: "OPENAI_API_KEY environment variable not set"
**Solution**:
```bash
export OPENAI_API_KEY='sk-...'
# Or add to ~/.bashrc or ~/.zshrc for persistence
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
```

### Issue: "Table doesn't exist" when querying RAG
**Solution**:
```bash
# First ingest some PDFs
mkdir -p data/earnings_pdfs
# Add your PDFs with naming: COMPANY_QUARTER_*.pdf
python3 src/rag/earnings_ingestion.py data/earnings_pdfs
```

### Issue: "No OHLCV data available for symbol"
**Possible Causes**:
1. Invalid symbol format (use "TCS" not "TCS.NS" for NSE)
2. No internet connection (Yahoo Finance is online)
3. Market holiday / weekend (no live data)

**Solution**:
```python
# Test with a known working symbol
from src.data.yahoo_finance_fetcher import YahooFinanceFetcher
fetcher = YahooFinanceFetcher()
data = fetcher.fetch_ohlcv("TCS.NS", "1y")
print(f"Got {len(data)} data points")
```

### Issue: Import errors
**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific packages
pip install lancedb llama-index llama-index-embeddings-openai
pip install llama-index-vector-stores-lancedb
```

### Issue: Tests failing
**Solution**:
```bash
# Check Python version (needs 3.9+)
python3 --version

# Run tests with verbose output
python3 -m pytest tests/unit/test_earnings_rag.py -v --tb=short

# Check for missing dependencies
pip list | grep -E 'lancedb|llama-index|openai'
```

---

## 🎯 Integration with Existing System

### Use with Dexter Agent
```python
from dexter import DexterAgent
from agents.workflows.vcp_workflow import run_vcp_analysis

# Get VCP analysis
vcp_result = run_vcp_analysis("TCS", "NSE")

# Feed to Dexter for deeper research
agent = DexterAgent()
research = await agent.research(
    f"Deep research on TCS. VCP confidence: {vcp_result.confidence_score:.1%}. "
    f"Signal: {vcp_result.get_stage('SignalGenerator').data.get('signal')}"
)
print(research.answer)
```

### Use with Existing Earnings Scraper
```python
from agents.earnings_data_scraper import get_earnings_scraper
from agents.workflows.vcp_workflow import run_vcp_analysis

# Get today's earnings announcements
scraper = get_earnings_scraper()
earnings_today = await scraper.fetch_today_announcements()

# Analyze each company
for announcement in earnings_today:
    symbol = announcement.get("symbol")
    result = run_vcp_analysis(symbol, "NSE")

    if result.success and result.confidence_score > 0.7:
        print(f"{symbol}: Strong candidate!")
        print(result.final_recommendation)
```

---

## ⏭️ What's Next (Optional)

### Phase 3: Real-Time Intelligence
**When to implement**: If you need web search and parallel analysis
**Dependencies**: ✅ Already installed (exa-py, agentops)
**Estimated time**: 3-5 days

**Will add**:
- Hybrid RAG (local DB + web search for latest news)
- Parallel analysis (fundamental + technical + sentiment simultaneously)
- Real-time Indian market news integration

### Phase 4: Observability
**When to implement**: When you need monitoring and debugging tools
**Dependencies**: ✅ Already installed (arize-phoenix-otel, agentops)
**Estimated time**: 2-3 days

**Will add**:
- Phoenix monitoring for RAG queries
- AgentOps tracking for multi-agent workflows
- System health dashboard

---

## 💡 Tips for Best Results

### 1. PDF Naming Convention
Use this format for best metadata extraction:
```
COMPANY_QUARTER_Description.pdf

Examples:
✅ TCS_Q4FY24_Results.pdf
✅ INFY_Q3FY24_Earnings_Call.pdf
✅ WIPRO_Q2FY25_Investor_Presentation.pdf

❌ tcs-results.pdf (missing quarter)
❌ Q4_2024_TCS.pdf (wrong order)
```

### 2. Query Best Practices
```python
# Good queries (specific, actionable)
"Which companies showed QoQ revenue growth above 10%?"
"Find companies with improving profit margins in Q4FY24"
"Compare TCS and INFY operating efficiency"

# Less effective queries (too vague)
"Tell me about earnings"
"Good companies"
```

### 3. Workflow Usage
```python
# For real-time analysis
result = run_vcp_analysis("TCS", "NSE")  # Synchronous, simple

# For batch processing (faster)
workflow = get_vcp_workflow(use_memory=True)
results = await asyncio.gather(*[
    workflow.run(symbol, "NSE") for symbol in symbols
])
```

---

## 📊 Performance Expectations

| Operation | Expected Time |
|-----------|---------------|
| RAG Query | < 2 seconds |
| VCP Workflow (all 4 stages) | 4-6 seconds |
| PDF Ingestion | 6-12 seconds per file |
| Memory Search | < 0.5 seconds |

---

## ✅ Quick Verification Checklist

Before using in production, verify:

- [ ] OpenAI API key is set: `echo $OPENAI_API_KEY`
- [ ] All tests pass: `python3 -m pytest tests/unit/test_earnings_rag.py tests/unit/test_vcp_workflow.py -v`
- [ ] RAG system initializes: `python3 -c "from src.rag.earnings_query import get_earnings_query_engine; get_earnings_query_engine()"`
- [ ] Workflow works: `python3 -c "from agents.workflows.vcp_workflow import run_vcp_analysis; print(run_vcp_analysis('TCS', 'NSE').success)"`
- [ ] Dependencies installed: `pip list | grep -E 'lancedb|llama-index'`

---

## 🎉 You're Ready!

Everything is set up and tested. Start with the quick examples above, then explore the comprehensive documentation for advanced usage.

**Need help?** Check the documentation files:
- Quick start: `QUICK_START_RAG_WORKFLOW.md`
- Technical guide: `INTEGRATION_COMPLETE_PHASE_1_2.md`
- RAG details: `src/rag/README.md`

**Happy trading with AI-enhanced VCP analysis!** 🚀
