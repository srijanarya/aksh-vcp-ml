# Backtest Infrastructure Crisis - Critical Analysis

**Date**: 2025-11-20
**Status**: 🔴 CRITICAL - Cannot execute backtest at scale
**Root Cause**: Data infrastructure rate limits + Strategy over-complexity

---

## 🚨 The Problem

We have a **chicken-and-egg infrastructure crisis**:

1. **Strategy needs validation** → Requires backtesting 5,575 stocks
2. **Yahoo Finance rate limits** → Failed after ~4,700 stocks (429 errors)
3. **Switched to Angel One** → ALSO hits rate limits immediately
4. **Strategy is too complex** → Requires 3-4 API calls per stock (Beta, RS, OHLCV)
5. **Result**: **Cannot validate strategy at scale**

---

## 📊 Failed Backtest Attempts

### Attempt 1: Yahoo Finance (2022-01-01 to 2024-11-01)
- **Universe**: 5,575 NSE+BSE stocks
- **Stocks Analyzed**: ~4,700 (84%)
- **Signals Found**: 0
- **Failure Reason**: `429 Too Many Requests` (Yahoo Finance rate limit)
- **API Calls Made**: ~14,000+ (4,700 stocks × 3+ calls each)
- **Decision**: NO GO (0% confidence from Strategy Consultant)

### Attempt 2: Angel One NIFTY 50 (2022-01-01 to 2024-11-01)
- **Universe**: 50 NIFTY 50 stocks
- **Stocks Analyzed**: 50 (100%)
- **Signals Found**: 0
- **Failure Reason**: `Access denied because of exceeding access rate` (Angel One rate limit)
- **API Calls Made**: ~100+ (50 stocks × 2+ symbol lookups each)
- **Additional Issues**:
  - Symbol format wrong (need "-EQ" suffix)
  - Rate limit hit on symbol lookups BEFORE data fetching
  - 4 symbol lookup failures (RELIANCE, BHARTIARTL, NTPC, APOLLOHOSP not found)

---

## 🔍 Root Cause Analysis

### Issue 1: Strategy Over-Complexity (Primary Issue)

**Current Strategy Parameters**: 14 total
- **Hard Filters**: 2 (Beta > 1.0, S/R quality >= 60)
- **Confluence Factors**: 7 (need 2 of 7)
- **Technical Indicators**: Beta, ADX, RS (3 separate calculations)
- **Multi-timeframe**: Daily + Weekly + 4H (removed for performance)

**API Calls Per Stock**:
1. Symbol token lookup (Angel One)
2. Daily OHLCV data
3. Weekly OHLCV data (or resample from daily)
4. Nifty index data (for Beta calculation)
5. Nifty index data (for RS calculation)

**Total**: ~5 API calls per stock minimum

**For 5,575 stocks**: 27,875+ API calls needed

### Issue 2: Data Infrastructure Limitations

**Yahoo Finance**:
- Rate limit: ~2,000 requests/hour
- Time needed: 27,875 / 2,000 = **14+ hours** at maximum throughput
- Reality: Hit limit after ~4,700 stocks (3 hours)

**Angel One**:
- Rate limit: Unknown, but VERY aggressive
- Hit limit on symbol lookups alone (first 50 stocks)
- Internal rate limiter (3 req/sec) insufficient
- Response: "Access denied because of exceeding access rate"

### Issue 3: Symbol Lookup Complexity (Angel One Specific)

**Angel One Symbol Format**:
- NSE equity symbols need "-EQ" suffix
- Examples:
  - ❌ "RELIANCE" (our input)
  - ✅ "RELIANCE-EQ" (Angel One format)

**Symbol Lookup API Calls**:
- `searchScrip()` API call for EACH stock
- No bulk lookup endpoint
- Hits rate limit before data fetching begins

### Issue 4: Strategy Selectivity (Secondary Issue)

**Results from partial backtest**:
- 4,700 stocks analyzed
- 0 trades found
- Indicates strategy is **too strict**

**Possible Reasons**:
1. Beta > 1.0 still filters ~60-65% of universe
2. ADX > 20 removes weak trends
3. S/R quality >= 60 is untested threshold
4. Need 2 of 7 confluences (30% confluence rate needed)
5. 2022-2024 period includes bear markets

---

## 💡 Solutions (Ranked by Feasibility)

### Option A: 🎯 SIMPLIFY STRATEGY + USE PROVEN ADX APPROACH (RECOMMENDED)

**Reference**: `agents/trading/adx_dma_scanner.py` (proven +265% return, 12-year backtest)

**Simplified Strategy**:
```python
# ENTRY CRITERIA (4 filters only)
1. Close > 50 DMA
2. Close > 100 DMA
3. Close > 200 DMA
4. ADX > 20

# EXIT CRITERIA
1. Close < 50 DMA OR
2. ADX < 10

# SIGNAL STRENGTH (5 factors for position sizing)
1. Close > all DMAs by >2%
2. ADX > 25
3. Volume > 2x average
4. DMAs aligned (50>100>200)
5. +DI > -DI by >5
```

**API Calls Per Stock**: 2 (symbol lookup + daily OHLCV)
**Total API Calls**: 11,150 (5,575 stocks × 2)
**Estimated Time**: ~5.6 hours at Yahoo Finance limits

**Pros**:
✅ Proven strategy (12-year backtest, +265% return)
✅ Simple (only 4 entry parameters)
✅ No Beta calculation (saves Nifty API calls)
✅ No RS calculation (saves more Nifty API calls)
✅ Single timeframe (daily only)
✅ Likely to generate trades (32/year historically)

**Cons**:
❌ Abandons current multi-timeframe analysis
❌ Abandons Beta/RS insights
❌ Still requires large-scale data fetching

---

### Option B: 🔧 FIX ANGEL ONE INTEGRATION + BATCH PROCESSING

**Fixes Needed**:
1. **Pre-download master symbol list** from Angel One
   - One-time bulk download
   - Cache all NSE-EQ symbols + tokens
   - No per-stock lookups

2. **Fix symbol format** (add "-EQ" suffix)
   - Map NSE symbols to Angel One format
   - Use BSE-NSE mapping JSON

3. **Implement aggressive rate limiting**
   - 1 request every 2 seconds (instead of 3/sec)
   - Add exponential backoff on failures
   - Batch processing with checkpoints

4. **Run backtest in batches**
   - Process 50 stocks at a time
   - Save intermediate results
   - Resume on failure

**API Calls**: Still 27,875+ calls
**Estimated Time**: 15+ hours with 1 req/2sec rate limiting

**Pros**:
✅ Uses existing strategy (no code changes)
✅ Angel One has better Indian market data
✅ Can resume from failures

**Cons**:
❌ Still 15+ hours to complete
❌ May still hit Angel One rate limits
❌ Complex infrastructure work
❌ Strategy still likely to find 0 trades (too strict)

---

### Option C: 🎲 SAMPLE-BASED VALIDATION (FASTEST PATH)

**Approach**:
1. **Select representative sample** (200-300 stocks)
   - Top 100 by market cap
   - Top 100 by liquidity (volume)
   - 100 random mid/small caps

2. **Run backtest on sample**
   - Can complete in 1-2 hours
   - Validates if strategy generates ANY trades

3. **If signals found**, scale to full universe slowly
4. **If no signals**, simplify strategy before scaling

**API Calls**: ~600-900 (300 stocks × 3)
**Estimated Time**: 1-2 hours

**Pros**:
✅ Fast validation (1-2 hours vs 15+ hours)
✅ Can iterate quickly on strategy parameters
✅ Reduces infrastructure risk
✅ Statistically significant sample

**Cons**:
❌ Not comprehensive (misses long-tail opportunities)
❌ Sample bias risk
❌ Still may hit rate limits if too frequent

---

### Option D: 💾 PRE-CACHE ALL HISTORICAL DATA (NUCLEAR OPTION)

**Approach**:
1. **Download all historical data upfront** (one-time)
   - 5,575 stocks × 3 years daily data
   - Store in local SQLite database
   - Take 24-48 hours to download (with rate limiting)

2. **Run backtests locally** (no API calls)
   - Query local database
   - Instant backtests
   - Can iterate on strategy parameters freely

**Pros**:
✅ One-time pain, infinite future backtests
✅ No rate limit issues after initial download
✅ Can test multiple strategies rapidly
✅ Local data = faster execution

**Cons**:
❌ 24-48 hours initial download time
❌ Data staleness (need periodic updates)
❌ Large disk space (several GB)
❌ Complex infrastructure setup

---

## 🚦 Recommendation: THREE-PHASE APPROACH

### Phase 1: IMMEDIATE (2 hours)
**Use Option A (Simplified ADX Strategy) + Option C (Sample)**

1. **Implement ADX+DMA strategy** from `adx_dma_scanner.py`
2. **Test on 300-stock sample** (Top 100 by mcap, top 100 by volume, 100 random)
3. **Use Yahoo Finance** (should stay under rate limits for 300 stocks)
4. **Evaluate results**:
   - If trades found → Proceed to Phase 2
   - If no trades → Strategy doesn't work, pivot to different approach

### Phase 2: VALIDATION (1-2 days)
**If Phase 1 finds signals:**

1. **Implement Option D** (Pre-cache all data)
   - Download 5,575 stocks historical data over 24-48 hours
   - Use Angel One with aggressive rate limiting
   - Store in SQLite database

2. **Run comprehensive backtest** on local data
   - Full universe (5,575 stocks)
   - Walk-forward analysis
   - In-sample/out-of-sample testing

### Phase 3: OPTIMIZATION (ongoing)
**If Phase 2 validates strategy:**

1. **Add back complexity gradually**
   - Test Beta filter (does it improve Sharpe?)
   - Test RS filter (does it improve win rate?)
   - Test multi-timeframe (does it reduce false signals?)

2. **Keep what works, remove what doesn't**
   - Use strategy consultant's traffic light system
   - Measure incremental improvement
   - Avoid overfitting

---

## 🎯 Immediate Next Step

I recommend **Phase 1** with the ADX+DMA strategy:

1. **Copy proven strategy** from [agents/trading/adx_dma_scanner.py](file:///Users/srijan/Desktop/aksh/agents/trading/adx_dma_scanner.py)
2. **Create sample stock list** (300 stocks: top 100 mcap + top 100 volume + 100 random)
3. **Run backtest** using Yahoo Finance (should work for 300 stocks)
4. **Evaluate in 2 hours**

**This gives us**:
- ✅ Fast answer (2 hours vs 15+ hours)
- ✅ Proven strategy (12-year backtest, +265%)
- ✅ Avoids rate limits (300 stocks is manageable)
- ✅ Decision point (proceed or pivot)

---

## ❓ Questions for User

1. **Do you want to simplify to ADX+DMA strategy** (proven +265% return)?
   - Pros: Simple, proven, fast to test
   - Cons: Abandons current multi-timeframe/Beta/RS work

2. **Do you want to fix Angel One integration** and run 15-hour backtest?
   - Pros: Uses current strategy
   - Cons: 15+ hours, may still find 0 trades

3. **Do you want to do sample-based testing first** (300 stocks)?
   - Pros: Fast validation (2 hours)
   - Cons: Not comprehensive

4. **Do you want to pre-cache all data** (24-48 hour setup)?
   - Pros: One-time pain, infinite future backtests
   - Cons: Initial time investment

---

## 📎 Related Files

- Current Strategy: [strategies/multi_timeframe_breakout.py](file:///Users/srijan/Desktop/aksh/strategies/multi_timeframe_breakout.py)
- Proven ADX Strategy: [agents/trading/adx_dma_scanner.py](file:///Users/srijan/Desktop/aksh/agents/trading/adx_dma_scanner.py)
- Parameter Analysis: [.claude/STRATEGY_PARAMETER_ANALYSIS.md](file:///Users/srijan/Desktop/aksh/.claude/STRATEGY_PARAMETER_ANALYSIS.md)
- Angel One Backtest: [backtest_with_angel.py](file:///Users/srijan/Desktop/aksh/backtest_with_angel.py)
- Strategy Consultant: [agents/backtesting/strategy_consultant.py](file:///Users/srijan/Desktop/aksh/agents/backtesting/strategy_consultant.py)

---

**Status**: ⏸️ AWAITING USER DECISION
