# Comprehensive Backtest Progress Report

**Started**: 2025-11-20 09:33 AM
**Running Duration**: ~1 hour
**Process ID**: 17540

## Progress Summary

- **Total symbols**: 5,575
- **Analysis attempts**: 102,894
- **Log lines**: 1,161,834
- **Beta rejections**: 78,482 (76%)
- **Symbols passing beta filter**: ~24,412 (24%)

## Rejection Breakdown

Most common rejection reason:
```
❌ Beta too low (< 1.2). Skipping.
```

**This is EXPECTED** - The strategy is designed as a "sniper rifle" to find 5-10 high-quality setups from thousands of stocks.

## Current Criteria (from [STOCK_DATABASE_REFERENCE.md](STOCK_DATABASE_REFERENCE.md:83-98))

- Beta > 1.2 vs Nifty
- Weekly strong uptrend (20 SMA > 50 SMA, price > both)
- Daily breakout (20-day high or consolidation)
- Volume > 1.5x average
- S/R quality score > 60
- Minimum 3 of 6+ confluences

## Trade Count So Far

**0 trades found** across all analyzed symbols.

## Next Steps

1. Wait for backtest completion (~2-3 more hours estimated)
2. Analyze final results
3. Determine if:
   - Strategy validated (found 10-25 trades over 3 years)
   - Strategy invalidated (0 or very few trades)

## Data Quality Notes

- Many delisted/invalid BSE symbols (bonds, old scrips) fail fast
- This actually improves performance (1-2 sec fails vs 5+ sec valid analysis)
- Effective sample size: ~40% of symbols have valid data

---
**Generated**: 2025-11-20 10:35 AM
**Status**: RUNNING
