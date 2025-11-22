# Backtesting & Strategy Consultant Agent System

## Overview

A comprehensive autonomous agent system that acts as a **professional trading strategy consultant**, providing the same level of analysis you'd get from a top-tier quantitative research firm.

## What It Does

This system will:
1. ✅ **Run comprehensive backtests** with walk-forward analysis
2. ✅ **Analyze strategy complexity** and detect overfitting
3. ✅ **Assess risk** (drawdowns, tail risk, position sizing)
4. ✅ **Generate professional reports** with actionable recommendations
5. ✅ **Make Go/No-Go decisions** with clear reasoning

## Key Features

### 🎯 Research-Backed Analysis
- All thresholds based on quantitative finance research
- No arbitrary decisions - everything is evidence-based
- References provided for all recommendations

### 🤖 Multi-Agent Architecture
- **Master Agent**: Strategy Consultant (orchestrates everything)
- **Specialist Agents**:
  - Backtesting Specialist
  - Strategy Analyzer
  - Risk Assessor
- **Tools & Skills**: Reusable capabilities (walk-forward, overfitting detection, etc.)

### 📊 Comprehensive Metrics
- Performance: Sharpe, Sortino, Calmar, Profit Factor
- Risk: Max DD, VaR, CVaR, Recovery Time
- Robustness: Parameter sensitivity, regime testing
- Statistical: Significance tests, confidence intervals

### 🚦 Traffic Light Ratings
Every analysis includes clear verdicts:
- 🟢 **GREEN**: Production ready
- 🟡 **YELLOW**: Needs improvement
- 🔴 **RED**: High risk / Not recommended

---

## Quick Start

### Option 1: Analyze Your Current Strategy

```python
from agents.backtesting.strategy_consultant import StrategyConsultant

# Initialize consultant
consultant = StrategyConsultant()

# Analyze your strategy
report = consultant.analyze_strategy(
    strategy_file="strategies/multi_timeframe_breakout.py",
    start_date="2023-01-01",
    end_date="2024-11-01",
    symbols=["TATAMOTORS", "RELIANCE", "TCS"]
)

# Get recommendations
print(report.executive_summary)
print(report.recommendations)
print(report.go_no_go_decision)
```

### Option 2: Interactive CLI

```bash
python agents/backtesting/cli.py analyze \
    --strategy strategies/multi_timeframe_breakout.py \
    --start-date 2023-01-01 \
    --end-date 2024-11-01
```

---

## What You Get

### Executive Summary Report

```markdown
================================================================================
STRATEGY ANALYSIS REPORT
================================================================================
Strategy: Multi-Timeframe Breakout with S/R Integration
Analysis Date: 2024-11-19
Analyst: Strategy Consultant Agent v1.0

Overall Rating: 🟡 NEEDS IMPROVEMENT
Confidence: 85%

================================================================================
TOP 3 STRENGTHS
================================================================================
1. 🟢 Strong risk-adjusted returns (Sharpe: 2.35)
2. 🟢 Consistent across market regimes (works in bull/bear/sideways)
3. 🟢 Good parameter robustness (low sensitivity)

================================================================================
TOP 3 CRITICAL ISSUES
================================================================================
1. 🔴 Insufficient trades (12 trades < 30 minimum threshold)
   → Recommendation: Expand universe to 20-30 stocks

2. 🟡 High complexity (8 rules, complexity score: 55/100)
   → Recommendation: Consider simplifying S/R confluence logic

3. 🟡 OOS performance degradation (OOS Sharpe: 1.85 vs In-Sample: 2.35)
   → Recommendation: Add walk-forward validation

================================================================================
RECOMMENDED ACTIONS (Prioritized)
================================================================================
Priority 1 (Critical):
- Expand stock universe to 20-30 symbols
- Run 2+ years of out-of-sample testing

Priority 2 (Important):
- Simplify confluence detection (reduce from 8 to 5 indicators)
- Implement walk-forward validation (5 splits)

Priority 3 (Nice-to-Have):
- Add Monte Carlo simulation
- Test parameter sensitivity in different regimes

================================================================================
GO / NO-GO DECISION
================================================================================
Decision: 🟡 CONDITIONAL GO

Proceed to paper trading with following conditions:
1. Expand to 20+ stock universe
2. Monitor first 30 trades closely
3. Implement automated kill-switch if drawdown > 15%

Do NOT proceed to live trading until:
- Minimum 30 trades completed in paper trading
- Out-of-sample Sharpe ≥ 1.5
- Maximum drawdown < 20%

================================================================================
```

### Detailed Analysis Reports

1. **Backtest Report**:
   - Full performance metrics
   - Walk-forward analysis results
   - Statistical significance tests
   - Trade-by-trade breakdown

2. **Strategy Analysis Report**:
   - Complexity scoring
   - Parameter sensitivity analysis
   - Overfitting detection
   - Market regime performance

3. **Risk Assessment Report**:
   - Drawdown analysis
   - Value at Risk (VaR)
   - Stress testing
   - Position sizing validation

---

## How It Works

### Phase 1: Data Collection
```
Consultant Agent → Data Fetcher Tool
- Fetch multi-timeframe data
- Validate data quality
- Handle missing data
```

### Phase 2: Parallel Analysis
```
Consultant Agent delegates to 3 specialists in parallel:

Backtesting Agent:
├── Run full backtest
├── Walk-forward analysis (5 splits)
├── Out-of-sample testing
├── Statistical significance tests
└── Generate backtest report

Strategy Analyzer Agent:
├── Count rules and parameters
├── Calculate complexity score
├── Test parameter sensitivity
├── Detect overfitting
└── Generate analysis report

Risk Assessor Agent:
├── Calculate max drawdown
├── Compute VaR/CVaR
├── Stress test scenarios
├── Validate position sizing
└── Generate risk report
```

### Phase 3: Synthesis
```
Consultant Agent:
├── Review all 3 reports
├── Identify contradictions
├── Prioritize issues
├── Generate recommendations
├── Make Go/No-Go decision
└── Create executive summary
```

---

## Research Foundation

All analysis criteria are based on quantitative finance research:

### Minimum Backtest Requirements
- **Trades**: ≥ 30 (Source: Statistical significance studies)
- **Time Period**: ≥ 2 years (Source: Market cycle coverage)
- **P-value**: < 0.05 (Source: 95% confidence standard)
- **OOS Sharpe**: ≥ 50% of in-sample (Source: Overfitting studies)

### Strategy Complexity Limits
- **Max Rules**: 5-7 (Source: Occam's Razor, overfitting research)
- **Max Parameters**: 4-6 (Source: Curve-fitting studies)
- **Explanation Time**: < 60 seconds (Source: Professional trader guidelines)

### Risk Thresholds
- **Max Drawdown**: < 20% acceptable, < 30% critical (Source: Professional risk management)
- **Recovery Time**: < 6 months acceptable, < 1 year critical
- **Calmar Ratio**: ≥ 2.0 good, ≥ 1.0 acceptable (Source: Hedge fund standards)

### Parameter Sensitivity
- **Sharpe Variation**: < 20% robust, > 40% fragile (Source: Robustness testing research)

---

## File Structure

```
/agents/backtesting/
├── README.md                        # This file
├── AGENT_ARCHITECTURE.md            # Detailed architecture
├── __init__.py
├── strategy_consultant.py           # Master agent
├── cli.py                           # Command-line interface
│
├── specialists/                     # Specialist agents
│   ├── __init__.py
│   ├── backtesting_agent.py
│   ├── strategy_analyzer.py
│   └── risk_assessor.py
│
├── tools/                           # Core tools
│   ├── __init__.py
│   ├── data_tools.py
│   ├── backtest_tools.py
│   ├── analysis_tools.py
│   └── risk_tools.py
│
├── skills/                          # Reusable skills
│   ├── __init__.py
│   ├── walk_forward.py
│   ├── overfitting_detection.py
│   ├── regime_testing.py
│   └── parameter_sensitivity.py
│
└── reports/                         # Report generation
    ├── __init__.py
    ├── report_generator.py
    └── templates/
        ├── executive_summary.md
        ├── backtest_report.md
        └── risk_report.md
```

---

## Implementation Status

- [x] Architecture designed
- [ ] Core tools (data, backtest, analysis, risk)
- [ ] Reusable skills (walk-forward, overfitting, regime testing)
- [ ] Specialist agents (backtesting, analyzer, risk)
- [ ] Master consultant agent
- [ ] Report generation system
- [ ] CLI interface
- [ ] End-to-end testing

---

## Next Steps

1. **Implement Core Tools** (Foundation) - IN PROGRESS
2. **Implement Skills** (Reusable capabilities)
3. **Implement Specialist Agents**
4. **Implement Master Consultant Agent**
5. **Create Report Templates**
6. **End-to-End Testing** with your current strategy

---

## Benefits

### For You
- **Time Saving**: Automated analysis that would take hours manually
- **Objective Feedback**: Unbiased assessment of strategy strengths/weaknesses
- **Actionable Insights**: Specific recommendations, not vague advice
- **Risk Mitigation**: Catch problems before live trading

### For Your Mentor
- **Professional Reports**: Share consultant-grade analysis
- **Validation**: Independent verification of strategy robustness
- **Decision Support**: Clear Go/No-Go recommendations

---

## Example Usage

```python
# Analyze existing strategy
consultant = StrategyConsultant()

# Full analysis
analysis = consultant.analyze_strategy(
    strategy_file="strategies/multi_timeframe_breakout.py",
    start_date="2023-01-01",
    end_date="2024-11-01",
    symbols=["TATAMOTORS", "RELIANCE", "TCS", "INFY", "HDFCBANK"]
)

# Print executive summary
print(analysis.executive_summary())

# Get specific recommendations
for recommendation in analysis.get_critical_issues():
    print(f"\n{recommendation.severity}: {recommendation.issue}")
    print(f"Action: {recommendation.recommendation}")

# Check Go/No-Go decision
if analysis.is_production_ready():
    print("✅ Strategy approved for paper trading")
else:
    print("❌ Strategy needs work before deployment")
    print(f"Blockers: {analysis.get_blockers()}")
```

---

**Status**: Architecture Complete, Implementation In Progress
**Date**: November 19, 2024
**Version**: 1.0.0-alpha
