# Backtesting & Strategy Consultant Agent System

## Architecture Overview

A comprehensive multi-agent system for autonomous backtesting and strategy consulting, designed to provide professional-grade analysis and actionable insights.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STRATEGY CONSULTANT AGENT                         │
│                     (Master Orchestrator)                            │
│  - Coordinates all sub-agents                                       │
│  - Generates final recommendations                                  │
│  - Creates executive summary reports                                │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   BACKTESTING │  │   STRATEGY    │  │   RISK        │
│     AGENT     │  │   ANALYZER    │  │   ASSESSOR    │
│               │  │    AGENT      │  │    AGENT      │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        │                  │                  │
   ┌────┴────┐        ┌────┴────┐       ┌────┴────┐
   │ Tools:  │        │ Tools:  │       │ Tools:  │
   │         │        │         │       │         │
   │ • Data  │        │ • Rule  │       │ • DD    │
   │   Fetch │        │   Count │       │   Calc  │
   │ • Walk  │        │ • Param │       │ • Risk  │
   │   Fwd   │        │   Sens  │       │   Mgmt  │
   │ • Stats │        │ • Simple│       │ • Monte │
   │   Calc  │        │   Check │       │   Carlo │
   └─────────┘        └─────────┘       └─────────┘
```

## Agent Hierarchy

### Level 1: Master Agent

**Strategy Consultant Agent**
- Role: Senior trading strategist / quantitative analyst
- Responsibilities:
  - Orchestrates all analysis
  - Reviews all sub-agent reports
  - Identifies red flags and opportunities
  - Generates actionable recommendations
  - Provides strategic guidance

### Level 2: Specialist Agents

#### 1. Backtesting Specialist Agent
- **Purpose**: Execute backtests and validate results
- **Skills**:
  - Walk-forward analysis
  - Out-of-sample testing
  - Monte Carlo simulation
  - Statistical validation
- **Tools**:
  - `data_fetcher`: Get historical data
  - `walk_forward_tester`: Split data and validate
  - `performance_calculator`: Calculate all metrics
  - `significance_tester`: Statistical tests
- **Output**: Detailed backtest report with metrics

#### 2. Strategy Analyzer Agent
- **Purpose**: Analyze strategy design and complexity
- **Skills**:
  - Rule counting and categorization
  - Parameter sensitivity analysis
  - Simplicity scoring
  - Overfitting detection
- **Tools**:
  - `rule_parser`: Extract strategy rules
  - `parameter_analyzer`: Test parameter variations
  - `complexity_scorer`: Calculate complexity metrics
  - `robustness_tester`: Test across market regimes
- **Output**: Strategy analysis report with recommendations

#### 3. Risk Assessor Agent
- **Purpose**: Evaluate risk and drawdown characteristics
- **Skills**:
  - Maximum drawdown analysis
  - Risk-adjusted returns
  - Position sizing validation
  - Tail risk assessment
- **Tools**:
  - `drawdown_calculator`: DD metrics
  - `var_calculator`: Value at Risk
  - `stress_tester`: Extreme scenarios
  - `correlation_analyzer`: Portfolio correlation
- **Output**: Risk assessment report

### Level 3: Tools & Skills

Each specialist agent has access to specific tools:

#### Backtesting Tools
1. **DataFetcherTool**: Fetch multi-timeframe data
2. **WalkForwardTool**: Implement walk-forward analysis
3. **MetricsCalculatorTool**: All performance metrics
4. **MonteCarloTool**: Randomization testing
5. **BiasDetectorTool**: Detect look-ahead, survivorship bias

#### Strategy Analysis Tools
1. **RuleCounterTool**: Count and categorize rules
2. **ParameterSensitivityTool**: Test parameter ranges
3. **ComplexityScorerTool**: Score strategy complexity
4. **OverfittingDetectorTool**: Detect curve-fitting
5. **RegimeTesterTool**: Test across market regimes

#### Risk Assessment Tools
1. **DrawdownCalculatorTool**: Max DD, recovery time
2. **VaRCalculatorTool**: Value at Risk, CVaR
3. **StressTesterTool**: Black swan scenarios
4. **PositionSizerTool**: Validate position sizing
5. **CorrelationTool**: Multi-asset correlation

---

## Agent Behaviors & Decision Logic

### Strategy Consultant Agent (Master)

**Decision Tree**:
```
1. Receive strategy for analysis
2. Delegate to specialist agents in parallel:
   - Backtesting Agent
   - Strategy Analyzer Agent
   - Risk Assessor Agent
3. Wait for all reports
4. Synthesize findings:
   - Identify contradictions
   - Prioritize issues by severity
   - Generate recommendations
5. Create executive summary:
   - Traffic light rating (🟢🟡🔴)
   - Top 3 strengths
   - Top 3 weaknesses
   - Specific action items
6. Return final report
```

**Prompting Strategy**:
```
You are a senior quantitative strategist with 20 years of experience.
Your role is to review trading strategies and provide honest, critical feedback.

Review the following reports from specialist analysts:
- Backtest Report: {backtest_report}
- Strategy Analysis: {strategy_analysis}
- Risk Assessment: {risk_assessment}

Provide:
1. Overall Rating: 🟢 Production Ready / 🟡 Needs Improvement / 🔴 High Risk
2. Top 3 Strengths
3. Top 3 Critical Issues (if any)
4. Recommended Actions (prioritized)
5. Go/No-Go Decision

Be direct and honest. If the strategy has problems, explain them clearly.
```

### Backtesting Specialist Agent

**Decision Logic**:
```python
def analyze_backtest(strategy, data):
    results = {}

    # 1. Run full backtest
    full_backtest = run_backtest(strategy, data, start, end)
    results['full'] = full_backtest

    # 2. Walk-forward analysis
    wf_results = walk_forward_test(strategy, data, n_splits=5)
    results['walk_forward'] = wf_results

    # 3. Out-of-sample validation
    train_end = "2023-01-01"
    oos_results = run_backtest(strategy, data, start=train_end, end=now)
    results['out_of_sample'] = oos_results

    # 4. Statistical significance
    significance = test_significance(full_backtest, n_permutations=1000)
    results['significance'] = significance

    # 5. Check minimum thresholds
    issues = []
    if full_backtest.num_trades < 30:
        issues.append("⚠️ Insufficient trades (< 30)")
    if full_backtest.time_period < 365:
        issues.append("⚠️ Insufficient time period (< 1 year)")
    if significance.p_value > 0.05:
        issues.append("🔴 Not statistically significant (p > 0.05)")

    # 6. Compare in-sample vs out-of-sample
    if oos_results.sharpe < full_backtest.sharpe * 0.5:
        issues.append("🔴 Severe degradation in OOS (Sharpe drop > 50%)")

    results['issues'] = issues
    return results
```

**Minimum Requirements** (Research-Based):
- Trades: ≥ 30 (minimum for statistical significance)
- Time Period: ≥ 2 years (covers multiple market conditions)
- P-value: < 0.05 (95% confidence)
- OOS Sharpe: ≥ 50% of in-sample Sharpe

### Strategy Analyzer Agent

**Simplicity Scoring**:
```python
def score_simplicity(strategy):
    score = 100  # Start at perfect

    # Count rules
    num_rules = count_rules(strategy)
    if num_rules > 5:
        score -= (num_rules - 5) * 10  # -10 per extra rule

    # Count parameters
    num_params = count_parameters(strategy)
    if num_params > 6:
        score -= (num_params - 6) * 5  # -5 per extra parameter

    # Check complexity of calculations
    if uses_complex_math(strategy):  # Neural nets, genetic algos, etc.
        score -= 20

    # Check explanation simplicity
    explanation_time = estimate_explanation_time(strategy)
    if explanation_time > 60:  # > 1 minute to explain
        score -= 15

    # Final rating
    if score >= 80:
        return "🟢 SIMPLE (score: {score})"
    elif score >= 60:
        return "🟡 MODERATE (score: {score})"
    else:
        return "🔴 TOO COMPLEX (score: {score})"
```

**Guidelines** (Research-Based):
- Max Rules: 5-7 (beyond this = overfitting risk)
- Max Parameters: 4-6 (more = curve-fitting)
- Explanation: < 60 seconds (if you can't explain it, you don't understand it)

**Parameter Sensitivity Test**:
```python
def test_parameter_sensitivity(strategy, data):
    """
    Vary each parameter ±20% and measure impact on Sharpe ratio
    """
    baseline_sharpe = backtest(strategy, data).sharpe
    sensitivities = {}

    for param in strategy.parameters:
        results = []
        for variation in [-20%, -10%, 0%, +10%, +20%]:
            modified_strategy = modify_parameter(strategy, param, variation)
            sharpe = backtest(modified_strategy, data).sharpe
            results.append(sharpe)

        # Calculate sensitivity
        sharpe_range = max(results) - min(results)
        sensitivity = sharpe_range / baseline_sharpe

        sensitivities[param] = {
            'sensitivity': sensitivity,
            'rating': get_sensitivity_rating(sensitivity)
        }

    return sensitivities

def get_sensitivity_rating(sensitivity):
    """
    Low sensitivity = robust
    High sensitivity = fragile
    """
    if sensitivity < 0.20:  # < 20% Sharpe variation
        return "🟢 ROBUST"
    elif sensitivity < 0.40:  # 20-40% variation
        return "🟡 MODERATE"
    else:  # > 40% variation
        return "🔴 FRAGILE"
```

### Risk Assessor Agent

**Drawdown Analysis**:
```python
def assess_drawdown_risk(backtest_results):
    max_dd = backtest_results.max_drawdown
    avg_dd = backtest_results.avg_drawdown
    recovery_time = backtest_results.max_recovery_days

    issues = []

    # Check max drawdown
    if max_dd > 0.30:  # > 30%
        issues.append("🔴 CRITICAL: Max DD > 30%")
    elif max_dd > 0.20:  # > 20%
        issues.append("🟡 WARNING: Max DD > 20%")
    else:
        issues.append("🟢 Max DD acceptable (< 20%)")

    # Check recovery time
    if recovery_time > 365:  # > 1 year
        issues.append("🔴 CRITICAL: Recovery time > 1 year")
    elif recovery_time > 180:  # > 6 months
        issues.append("🟡 WARNING: Recovery time > 6 months")

    # Risk-adjusted returns
    calmar_ratio = backtest_results.returns / max_dd
    if calmar_ratio < 1.0:
        issues.append("🔴 Poor risk-adjusted returns (Calmar < 1.0)")
    elif calmar_ratio < 2.0:
        issues.append("🟡 Moderate risk-adjusted returns (Calmar 1-2)")
    else:
        issues.append("🟢 Good risk-adjusted returns (Calmar > 2)")

    return issues
```

---

## Skills (Reusable Capabilities)

### Skill 1: Walk-Forward Analysis
```python
class WalkForwardSkill:
    """
    Implements walk-forward testing to prevent overfitting
    """

    def execute(self, strategy, data, n_splits=5, train_pct=0.8):
        """
        Split data into N windows:
        - Train on 80%
        - Test on 20%
        - Roll forward
        """
        results = []

        window_size = len(data) // n_splits

        for i in range(n_splits):
            # Define train/test split
            train_start = i * window_size
            train_end = train_start + int(window_size * train_pct)
            test_end = train_start + window_size

            train_data = data[train_start:train_end]
            test_data = data[train_end:test_end]

            # Optionally optimize parameters on train
            # (skip this for now to avoid overfitting)

            # Test on out-of-sample data
            oos_results = backtest(strategy, test_data)
            results.append(oos_results)

        return {
            'n_splits': n_splits,
            'avg_sharpe': mean([r.sharpe for r in results]),
            'std_sharpe': std([r.sharpe for r in results]),
            'consistency': self.calculate_consistency(results)
        }

    def calculate_consistency(self, results):
        """
        Strategy is consistent if it works across all periods
        """
        positive_periods = sum(1 for r in results if r.returns > 0)
        consistency = positive_periods / len(results)

        if consistency >= 0.80:  # 80%+ periods profitable
            return "🟢 CONSISTENT"
        elif consistency >= 0.60:
            return "🟡 MODERATE"
        else:
            return "🔴 INCONSISTENT"
```

### Skill 2: Overfitting Detection
```python
class OverfittingDetectorSkill:
    """
    Detect if strategy is overfit to historical data
    """

    def execute(self, strategy, data):
        red_flags = []

        # 1. Too many parameters
        if len(strategy.parameters) > 6:
            red_flags.append({
                'severity': 'HIGH',
                'issue': f'Too many parameters ({len(strategy.parameters)} > 6)',
                'recommendation': 'Simplify strategy'
            })

        # 2. Perfect or near-perfect backtest
        full_results = backtest(strategy, data)
        if full_results.win_rate > 0.85:
            red_flags.append({
                'severity': 'HIGH',
                'issue': f'Suspiciously high win rate ({full_results.win_rate:.1%})',
                'recommendation': 'Likely overfit - add out-of-sample testing'
            })

        # 3. In-sample vs OOS degradation
        train_data = data[:int(len(data) * 0.7)]
        test_data = data[int(len(data) * 0.7):]

        train_sharpe = backtest(strategy, train_data).sharpe
        test_sharpe = backtest(strategy, test_data).sharpe

        degradation = (train_sharpe - test_sharpe) / train_sharpe
        if degradation > 0.30:  # > 30% drop
            red_flags.append({
                'severity': 'CRITICAL',
                'issue': f'Severe OOS degradation ({degradation:.1%})',
                'recommendation': 'Strategy likely overfit to training data'
            })

        # 4. Parameter sensitivity
        sensitivities = test_parameter_sensitivity(strategy, data)
        fragile_params = [p for p, s in sensitivities.items() if s['rating'] == '🔴 FRAGILE']
        if len(fragile_params) > 0:
            red_flags.append({
                'severity': 'MEDIUM',
                'issue': f'Fragile parameters: {fragile_params}',
                'recommendation': 'Use round numbers or remove these parameters'
            })

        return {
            'overfit_risk': 'HIGH' if any(f['severity'] == 'CRITICAL' for f in red_flags) else 'MODERATE' if red_flags else 'LOW',
            'red_flags': red_flags
        }
```

### Skill 3: Market Regime Testing
```python
class MarketRegimeSkill:
    """
    Test strategy across different market conditions
    """

    def execute(self, strategy, data):
        """
        Split data into bull/bear/sideways periods and test separately
        """
        # Identify regimes (simple: based on market trend)
        regimes = self.identify_regimes(data)

        results = {}
        for regime_name, regime_data in regimes.items():
            regime_results = backtest(strategy, regime_data)
            results[regime_name] = {
                'returns': regime_results.returns,
                'sharpe': regime_results.sharpe,
                'max_dd': regime_results.max_drawdown,
                'num_trades': regime_results.num_trades
            }

        # Check consistency across regimes
        sharpe_values = [r['sharpe'] for r in results.values()]
        sharpe_std = std(sharpe_values)

        if sharpe_std < 0.5:
            consistency = "🟢 WORKS IN ALL REGIMES"
        elif sharpe_std < 1.0:
            consistency = "🟡 WORKS IN MOST REGIMES"
        else:
            consistency = "🔴 REGIME-DEPENDENT"

        # Identify best/worst regimes
        best_regime = max(results, key=lambda k: results[k]['sharpe'])
        worst_regime = min(results, key=lambda k: results[k]['sharpe'])

        return {
            'regime_results': results,
            'consistency': consistency,
            'best_regime': best_regime,
            'worst_regime': worst_regime,
            'recommendation': self.get_regime_recommendation(results)
        }

    def identify_regimes(self, data):
        """
        Simple regime identification:
        - Bull: Market up > 10% over 6 months
        - Bear: Market down > 10% over 6 months
        - Sideways: Otherwise
        """
        # Implementation details...
        pass
```

---

## Implementation Files

### Directory Structure
```
/agents/backtesting/
├── __init__.py
├── AGENT_ARCHITECTURE.md          # This file
├── strategy_consultant.py          # Master agent
├── specialists/
│   ├── __init__.py
│   ├── backtesting_agent.py        # Backtesting specialist
│   ├── strategy_analyzer.py        # Strategy analysis specialist
│   └── risk_assessor.py            # Risk assessment specialist
├── tools/
│   ├── __init__.py
│   ├── data_tools.py               # Data fetching, preparation
│   ├── backtest_tools.py           # Backtesting execution
│   ├── analysis_tools.py           # Strategy analysis
│   └── risk_tools.py               # Risk calculations
├── skills/
│   ├── __init__.py
│   ├── walk_forward.py             # Walk-forward testing
│   ├── overfitting_detection.py    # Overfit detection
│   ├── regime_testing.py           # Market regime testing
│   └── parameter_sensitivity.py    # Parameter analysis
└── reports/
    ├── __init__.py
    ├── report_generator.py         # Generate formatted reports
    └── templates/
        ├── executive_summary.md
        ├── backtest_report.md
        └── risk_report.md
```

---

## Next Steps

1. **Implement Core Tools** (Foundation)
   - Data fetcher
   - Backtest executor
   - Metrics calculator

2. **Implement Skills** (Reusable capabilities)
   - Walk-forward analysis
   - Overfitting detection
   - Regime testing

3. **Implement Specialist Agents**
   - Backtesting agent
   - Strategy analyzer
   - Risk assessor

4. **Implement Master Agent**
   - Strategy consultant (orchestrator)

5. **Create Report Templates**
   - Executive summary
   - Detailed reports

6. **Integration & Testing**
   - Test with your current strategy
   - Iterate based on results

---

## Success Criteria

The system is successful if it can:

1. ✅ Run a backtest autonomously
2. ✅ Identify strategy weaknesses (overfitting, complexity, risk)
3. ✅ Provide specific, actionable recommendations
4. ✅ Generate professional reports (like a consulting firm would)
5. ✅ Make Go/No-Go decisions with clear reasoning

---

**Status**: Architecture Complete - Ready for Implementation
**Date**: November 19, 2024
