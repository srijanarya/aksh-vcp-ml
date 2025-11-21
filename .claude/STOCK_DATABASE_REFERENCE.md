# Stock Database Reference

## Master Stock Lists

### Location: `/Users/srijan/Desktop/aksh/agents/backtesting/symbol_lists/`

**All Stocks File**: `nse_bse_all_stocks.txt`
- Total unique symbols: **5,575 stocks**
- Format: Comma-separated, Yahoo Finance compatible (.NS suffix)
- Last updated: 2025-11-20

**Individual List File**: `nse_bse_all_stocks_list.txt`
- Same symbols, one per line
- Easier for viewing/browsing

### Source Files

1. **NSE Equity List**: `/Users/srijan/Desktop/aksh/nse_equity_list.csv`
   - Symbols: 2,189 NSE stocks
   - Format: CSV with SYMBOL, NAME, SERIES, etc.
   - All major NSE-listed equities

2. **BSE Bhav Copy**: `/Users/srijan/Desktop/aksh/data/cache/bhav_copy/BSE_EQ241224.CSV`
   - Symbols: 4,474 BSE stocks (from daily equity report)
   - Format: CSV with SC_CODE, SC_NAME, OPEN, HIGH, LOW, CLOSE, etc.
   - Complete BSE equity universe (much better than the 850-stock GSM list)

3. **Overlap**: 1,088 stocks appear in both NSE and BSE lists

### Generation Script

**Location**: `/Users/srijan/Desktop/aksh/tools/create_comprehensive_symbol_list.py`

```bash
# Regenerate symbol lists
python3 tools/create_comprehensive_symbol_list.py
```

## Usage in Backtesting

### Full Universe Backtest
```bash
python3 agents/backtesting/cli.py analyze \
  --strategy strategies/multi_timeframe_breakout.py \
  --start-date 2022-01-01 \
  --end-date 2024-11-01 \
  --symbols "$(cat agents/backtesting/symbol_lists/nse_bse_all_stocks.txt)"
```

### Custom Subset
```bash
# Use head/tail to select subsets
python3 agents/backtesting/cli.py analyze \
  --strategy strategies/multi_timeframe_breakout.py \
  --start-date 2022-01-01 \
  --end-date 2024-11-01 \
  --symbols "$(head -100 agents/backtesting/symbol_lists/nse_bse_all_stocks_list.txt | tr '\n' ',')"
```

## Data Sources Integration

### Yahoo Finance (Current Default)
- Free API
- Good for daily/weekly data
- Rate limits on intraday (1H/4H) data
- Reliable for NSE stocks with .NS suffix

### Angel One (Now Available - Account Active)
- **Status**: Account is NO LONGER dormant
- **Capability**: Can fetch and pull historical data
- **Advantage**: No rate limits on Indian market data
- **Coverage**: All NSE/BSE stocks
- **Data Quality**: Exchange-grade, official data
- **Integration Location**: TBD - to be implemented

### Next Steps for Angel One Integration
1. Set up Angel One API credentials
2. Create data fetcher wrapper in `agents/backtesting/tools/data_tools.py`
3. Add fallback logic: Try Angel One first, fallback to Yahoo Finance
4. This will eliminate rate limiting issues completely

## Strategy Universe Requirements

The multi-timeframe breakout strategy is designed as a **"sniper rifle"**:
- Designed to find 5-10 high-quality setups
- Out of 5,000-7,000 stocks
- Per year or per quarter
- Rejection rate: 99%+

**DO NOT relax strategy criteria** - instead, increase the stock universe.

Current criteria (strict by design):
- Beta > 1.2 vs Nifty
- Weekly strong uptrend (20 SMA > 50 SMA, price > both)
- Daily breakout (20-day high or consolidation)
- Volume > 1.5x average
- S/R quality score > 60
- Minimum 3 of 6+ confluences

## Historical Backtest Results

### Small Sample (80 stocks, 2022-2024)
- Result: 0 trades
- Expected: Too small sample for sniper strategy

### Expected with Full Universe (5,575 stocks)
- Estimated: 10-25 high-quality setups over 3 years
- Will validate strategy effectiveness
- Much closer to the 5,000-7,000 target universe

## Important Notes

1. **Never relax strategy criteria** without explicit user approval
2. **Always use full universe** (2,907 stocks) for meaningful results
3. **Symbol format**: Always use .NS suffix for Yahoo Finance
4. **Angel One integration**: Preferred data source when implemented
5. **This file exists** so Claude remembers the stock database location and structure

---
**Maintained by**: Claude Code
**Last Updated**: 2025-11-20
