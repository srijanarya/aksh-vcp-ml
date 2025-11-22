# Backtesting Agent System - Quick Start

## Overview

The Backtesting Agent System is a comprehensive, multi-agent platform for autonomous strategy validation and consulting. It provides professional-grade analysis with Go/No-Go decisions.

## Installation

No additional dependencies needed beyond the main project requirements.

```bash
# Ensure you're in the project root
cd /Users/srijan/Desktop/aksh

# Install dependencies if not already done
pip install -r requirements.txt
```

## Quick Start

### 1. Basic Analysis

Analyze a single strategy on one symbol:

```bash
python agents/backtesting/cli.py analyze \
    --strategy strategies/multi_timeframe_breakout.py \
    --start-date 2023-01-01 \
    --end-date 2024-11-01 \
    --symbols TATAMOTORS.NS
```

### 2. Multiple Symbols

Test across multiple symbols:

```bash
python agents/backtesting/cli.py analyze \
    --strategy strategies/multi_timeframe_breakout.py \
    --start-date 2023-01-01 \
    --end-date 2024-11-01 \
    --symbols "TATAMOTORS.NS,RELIANCE.NS,TCS.NS"
```

### 3. Save Reports

Generate and save detailed reports:

```bash
python agents/backtesting/cli.py analyze \
    --strategy strategies/multi_timeframe_breakout.py \
    --start-date 2023-01-01 \
    --end-date 2024-11-01 \
    --symbols TATAMOTORS.NS \
    --output reports/my_strategy \
    --detailed
```

This creates:
- `reports/my_strategy_summary.md` - Executive summary
- `reports/my_strategy_detailed.md` - Full analysis report

## Strategy Requirements

Your strategy must implement this interface:

```python
class YourStrategy:
    def generate_signal(self, data: Dict[str, pd.DataFrame], current_date: datetime) -> Optional[Dict]:
        """
        Generate trading signal

        Args:
            data: Multi-timeframe data dict with 'daily', 'weekly' keys
            current_date: Current bar date

        Returns:
            Signal dict with:
            - entry_price: Entry price
            - stop_loss: Stop loss price
            - target: Target price

        Returns None if no signal
        """
        # Your logic here
        pass
```

## Output Interpretation

### Traffic Lights

- 🟢 **GREEN**: Passed - meets all requirements
- 🟡 **YELLOW**: Warning - acceptable but needs monitoring
- 🔴 **RED**: Failed - critical issues found

### Categories

1. **Performance**: Returns and risk-adjusted metrics
2. **Risk**: Drawdown and volatility analysis
3. **Robustness**: Walk-forward validation and consistency
4. **Complexity**: Overfitting risk assessment

### Decisions

- **GO**: Strategy approved for live trading
- **PROCEED WITH CAUTION**: Shows promise but has warnings
- **NO GO**: Not recommended for live trading

## What Gets Analyzed

### 1. Backtesting (BacktestingSpecialistAgent)
- Full backtest execution
- Walk-forward analysis (5 windows, 80/20 split)
- Statistical significance testing
- Minimum requirements:
  - 30+ trades
  - 2+ years of data

### 2. Strategy Analysis (StrategyAnalyzerAgent)
- Complexity assessment
- Overfitting detection
- Parameter sensitivity testing
- Market regime testing

### 3. Risk Assessment (RiskAssessorAgent)
- Maximum drawdown analysis
- Value at Risk (VaR) and CVaR
- Recovery time analysis
- Underwater period tracking

## Research-Backed Thresholds

The system uses industry-standard thresholds:

| Metric | Acceptable | Warning | Critical |
|--------|-----------|---------|----------|
| Max Drawdown | <20% | 20-30% | >30% |
| Sharpe Ratio | >1.5 | 1.0-1.5 | <1.0 |
| Win Rate | 40-60% | <40% or >85% | >90% (overfit) |
| Sample Size | 30+ trades | 20-29 | <20 |
| Time Period | 2+ years | 1-2 years | <1 year |
| OOS Degradation | <20% | 20-30% | >30% |
| Parameter Count | ≤6 | 7-10 | >10 |

## Programmatic Usage

You can also use the system programmatically:

```python
from agents.backtesting import StrategyConsultantAgent, ReportGenerator
from strategies.multi_timeframe_breakout import MultiTimeframeBreakoutStrategy

# Create consultant
consultant = StrategyConsultantAgent()

# Load your strategy
strategy = MultiTimeframeBreakoutStrategy()

# Run analysis
report = consultant.analyze_strategy(
    strategy=strategy,
    symbols=['TATAMOTORS.NS', 'RELIANCE.NS'],
    start_date='2023-01-01',
    end_date='2024-11-01'
)

# Access results
summary = report['executive_summary']
print(f"Decision: {summary.decision}")
print(f"Confidence: {summary.confidence_score:.0f}%")

# Generate markdown report
report_gen = ReportGenerator()
markdown = report_gen.generate_executive_summary(report)
print(markdown)

# Save to file
report_gen.save_report(report, 'my_report.md', detailed=True)
```

## Troubleshooting

### "No data available"
- Check symbol format (NSE: "SYMBOL.NS", BSE: "SYMBOL.BO")
- Verify date range (Yahoo Finance may not have all data)
- Try a longer date range

### "Insufficient trades"
- Strategy may be too selective
- Extend date range
- Test on more volatile symbols

### "Strategy file not found"
- Use absolute path or path relative to project root
- Ensure strategy file has a class ending in "Strategy"

### "Module import errors"
- Ensure you're running from project root
- Check that all dependencies are installed
- Try: `export PYTHONPATH=/Users/srijan/Desktop/aksh:$PYTHONPATH`

## Next Steps

1. **Review Reports**: Read the executive summary carefully
2. **Address Issues**: Fix any critical issues identified
3. **Iterate**: Re-run analysis after making changes
4. **Paper Trade**: Test approved strategies in paper trading
5. **Monitor**: Track live performance vs backtest

## Support

For issues or questions:
- Review `/Users/srijan/Desktop/aksh/agents/backtesting/AGENT_ARCHITECTURE.md`
- Check `/Users/srijan/Desktop/aksh/agents/backtesting/README.md`
- Examine example strategy: `/Users/srijan/Desktop/aksh/strategies/multi_timeframe_breakout.py`

---

**Remember**: Backtest results are not guarantees of future performance. Always use proper risk management in live trading.
