# Full Backtest Status - Stage 1 Relaxed Parameters

**Started**: November 20, 2025 at 7:00 PM
**Status**: 🟢 RUNNING

---

## Current Progress

- **Stocks Analyzed**: ~318 of 5,574 (5.7%)
- **Estimated Time Remaining**: ~2.8 hours
- **Rate**: ~2 seconds per stock (with Angel One rate limiting)

## Parameters (Stage 1 Relaxation)

- **Beta Threshold**: 0.9 (relaxed from 1.0)
- **ADX Threshold**: 18 (relaxed from 20)
- **S/R Quality**: 50 (relaxed from 60)
- **Min Confluences**: 2 of 7

## Expected Results

Based on NIFTY 50 test (6% hit rate):
- **Expected Signals**: ~330 signals
- **Expected Improvement**: 330x over original parameters

## Quick Test Results (Already Completed)

NIFTY 50 test found 3 signals:
1. **EICHERMOT** - Beta 1.00, ADX 28.2
2. **HEROMOTOCO** - Beta 0.99, ADX 31.3
3. **RELIANCE** - Beta 1.17, ADX 58.3

## How to Monitor

The backtest is running in the background. To check progress:

```bash
# Check latest progress
tail -10 /tmp/backtest_stage1_log.txt

# Check if any signals found yet
cat /tmp/backtest_signals.json 2>/dev/null || echo "No signals yet"

# Check checkpoint (saves every 10 stocks)
cat /tmp/backtest_checkpoint.json 2>/dev/null || echo "No checkpoint yet"
```

## Notes

- Angel One API requires 2-second delays between requests
- Backtest will automatically resume from checkpoint if interrupted
- Results will be saved to `/tmp/backtest_signals.json`
- Full log available at `/tmp/backtest_stage1_log.txt`

---

**Next Update**: Will check again in 30 minutes