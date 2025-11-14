# Epic 6: Backtesting & Validation

**Epic ID**: EPIC-6
**Priority**: P0 (Critical Path)
**Status**: Ready to Start
**Estimated Effort**: 11 days (13 days with buffer)
**Dependencies**: EPIC-3 (Model Training), EPIC-4 (Production Deployment) - COMPLETE ✅

---

## Epic Goal

Validate ML model performance through comprehensive backtesting on historical data (2022-2025), walk-forward validation to simulate real trading conditions, risk metrics calculation (Sharpe ratio, max drawdown), and strategy comparison framework. Target: Demonstrate consistent F1 ≥ 0.70 across multiple time periods, positive risk-adjusted returns in simulated trading.

---

## Success Criteria

1. **Historical Accuracy**: F1 ≥ 0.70 on 2022, 2023, 2024 data separately
2. **Walk-forward Validation**: 12 monthly retrain cycles, F1 ≥ 0.65 average
3. **Risk Metrics**: Sharpe ratio ≥ 1.5, max drawdown ≤ 20%
4. **Strategy Performance**: Backtest returns >15% annualized (if used for trading)
5. **Comprehensive Reports**: HTML reports with charts, tables, insights

---

## Stories (5 total)

### Story 6.1: Historical Performance Analysis
- Backtest on 2022, 2023, 2024 data separately
- Calculate F1, precision, recall per year/quarter
- Identify temporal performance patterns
- **Effort**: 2 days

### Story 6.2: Walk-forward Validation
- Monthly retrain-predict cycles
- Simulate production deployment timeline
- Track performance degradation over time
- **Effort**: 3 days

### Story 6.3: Risk Metrics Calculation
- Sharpe ratio, Sortino ratio
- Maximum drawdown, volatility
- Win rate, profit factor (if trading simulation)
- **Effort**: 2 days

### Story 6.4: Backtesting Report Generation
- HTML report with interactive charts
- Performance summary tables
- Trade-by-trade analysis (if applicable)
- **Effort**: 2 days

### Story 6.5: Strategy Comparison Framework
- Compare baseline vs advanced models
- Compare different feature sets
- A/B testing framework
- **Effort**: 2 days

---

## File Structure

```
agents/ml/backtesting/
├── historical_analyzer.py           # Story 6.1
├── walk_forward_validator.py        # Story 6.2
├── risk_calculator.py               # Story 6.3
├── report_generator.py              # Story 6.4
└── strategy_comparator.py           # Story 6.5

data/backtesting/
├── historical_results/
│   ├── 2022_performance.json
│   ├── 2023_performance.json
│   └── 2024_performance.json
├── walk_forward_results/
│   └── walk_forward_2022_2025.json
├── risk_metrics/
│   └── risk_report.json
└── reports/
    ├── backtest_report.html
    └── strategy_comparison.html

tests/unit/
├── test_historical_analyzer.py
├── test_walk_forward_validator.py
├── test_risk_calculator.py
├── test_report_generator.py
└── test_strategy_comparator.py
```

---

## Story 6.1: Historical Performance Analysis

**Story ID:** EPIC6-S1
**Priority:** P0
**Estimated Effort:** 2 days
**Dependencies:** EPIC-3 (Model Training)

### User Story

**As a** ML Engineer,
**I want** to analyze model performance across different time periods,
**so that** I can validate model consistency and identify temporal biases.

### Acceptance Criteria

**AC6.1.1:** HistoricalAnalyzer class for time-based backtesting
- File: `/Users/srijan/Desktop/aksh/agents/ml/backtesting/historical_analyzer.py`
- Class: `HistoricalAnalyzer` with method: `analyze_period(start_date: str, end_date: str) -> PeriodPerformance`
- Split data by year: 2022, 2023, 2024, 2025 (partial)
- For each period: Train model, predict, evaluate

**AC6.1.2:** Train-test split by time period
- Training: All data before period start
- Testing: Data within period
- Example for 2024:
  - Training: 2022-01-01 to 2023-12-31
  - Testing: 2024-01-01 to 2024-12-31
- No data leakage: Strict temporal ordering

**AC6.1.3:** Calculate metrics per period
- Metrics: F1, precision, recall, ROC-AUC
- Confusion matrix
- Classification report
- Store in `historical_results/{YEAR}_performance.json`

**AC6.1.4:** Quarterly breakdown within each year
- Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)
- Identify if performance varies by quarter
- Example: "Q4 historically has lower F1 (0.65) vs Q2 (0.75)"

**AC6.1.5:** Performance comparison across years
- Table format:
```
Year | Samples | F1    | Precision | Recall | ROC-AUC | Upper Circuit Rate
-----|---------|-------|-----------|--------|---------|-------------------
2022 | 45,230  | 0.71  | 0.67      | 0.76   | 0.78    | 8.3%
2023 | 52,140  | 0.73  | 0.70      | 0.77   | 0.80    | 7.5%
2024 | 48,890  | 0.69  | 0.65      | 0.74   | 0.76    | 6.8%
2025 | 12,450  | 0.72  | 0.68      | 0.77   | 0.79    | 9.1%
-----|---------|-------|-----------|--------|---------|-------------------
Avg  | 158,710 | 0.71  | 0.68      | 0.76   | 0.78    | 7.9%
```

**AC6.1.6:** Identify temporal patterns
- Detect: Year-over-year performance trends
- Statistical test: Are differences significant? (chi-square test)
- Insights: "F1 decreased in 2024 due to market regime change (bear market)"

**AC6.1.7:** Feature importance per period
- Calculate SHAP values for each year
- Compare: Which features mattered most in 2022 vs 2024?
- Identify: Stable features (important across all years) vs volatile features

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/backtesting/historical_analyzer.py`

**Key Components:**
```python
from dataclasses import dataclass
from typing import Dict, List
import pandas as pd
from sklearn.metrics import f1_score, classification_report

@dataclass
class PeriodPerformance:
    period: str  # "2022", "2023Q1", etc.
    start_date: str
    end_date: str
    n_samples: int
    f1: float
    precision: float
    recall: float
    roc_auc: float
    confusion_matrix: List[List[int]]
    classification_report: str
    upper_circuit_rate: float

class HistoricalAnalyzer:
    def __init__(
        self,
        feature_dbs: Dict[str, str],
        labels_db: str,
        model_registry_path: str
    ):
        """Initialize historical analyzer"""
        
    def analyze_period(
        self,
        start_date: str,
        end_date: str,
        period_name: str = None
    ) -> PeriodPerformance:
        """
        Backtest model on specific time period.
        
        Args:
            start_date: Period start (ISO format)
            end_date: Period end (ISO format)
            period_name: Human-readable name (e.g., "2024Q1")
            
        Returns:
            PeriodPerformance with metrics
        """
        
    def analyze_all_years(
        self,
        years: List[int] = [2022, 2023, 2024, 2025]
    ) -> Dict[int, PeriodPerformance]:
        """Backtest on multiple years"""
        
    def analyze_quarterly(
        self,
        year: int
    ) -> Dict[str, PeriodPerformance]:
        """Backtest on quarterly basis for given year"""
        
    def compare_periods(
        self,
        performances: Dict[str, PeriodPerformance]
    ) -> pd.DataFrame:
        """Generate comparison table"""
        
    def detect_temporal_patterns(
        self,
        performances: Dict[str, PeriodPerformance]
    ) -> List[str]:
        """Identify trends and patterns"""
        
    def save_results(
        self,
        performances: Dict[str, PeriodPerformance],
        output_dir: str
    ):
        """Save results to JSON files"""
```

**Dependencies:**
- `scikit-learn` - Metrics
- `pandas` - Data manipulation
- `shap` - Feature importance

**Test File:** `tests/unit/test_historical_analyzer.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Backtest on 2022-2024 data
- [ ] Manual test: Verify metrics match manual calculation
- [ ] Results saved to JSON files
- [ ] Documentation: Backtesting methodology

---

## Story 6.2: Walk-forward Validation

**Story ID:** EPIC6-S2
**Priority:** P0
**Estimated Effort:** 3 days
**Dependencies:** EPIC6-S1 (Historical Analyzer)

### User Story

**As a** Quantitative Analyst,
**I want** walk-forward validation to simulate production deployment,
**so that** I can estimate real-world model performance with periodic retraining.

### Acceptance Criteria

**AC6.2.1:** WalkForwardValidator class for rolling validation
- File: `/Users/srijan/Desktop/aksh/agents/ml/backtesting/walk_forward_validator.py`
- Class: `WalkForwardValidator` with method: `run_walk_forward(start_date: str, end_date: str, retrain_freq: str) -> WalkForwardResults`
- Retrain frequencies: "monthly", "quarterly", "yearly"
- Default: Monthly (simulate production retraining schedule)

**AC6.2.2:** Rolling window training strategy
- Window size: 365 days (1 year of training data)
- Prediction period: 30 days (1 month)
- Example for Jan 2023:
  - Training: 2022-01-01 to 2022-12-31 (365 days)
  - Testing: 2023-01-01 to 2023-01-31 (30 days)
- Next iteration (Feb 2023):
  - Training: 2022-02-01 to 2023-01-31 (rolling forward)
  - Testing: 2023-02-01 to 2023-02-28

**AC6.2.3:** Retrain model each iteration
- For each period:
  1. Load training data from rolling window
  2. Retrain model (or load pre-trained if available)
  3. Predict on test period
  4. Evaluate metrics
  5. Store results
- Total iterations: ~36 months (2022-2025) = 36 retrain cycles

**AC6.2.4:** Track performance over time
- Store: `(period, f1, precision, recall, n_samples, training_time)`
- Detect: Performance degradation trends
- Example: "F1 decreased from 0.72 (Jan 2023) to 0.65 (Dec 2024)"
- Identify: Periods with low performance (retrain needed)

**AC6.2.5:** Cumulative performance metrics
- Average F1 across all periods
- Standard deviation of F1 (measure consistency)
- Minimum F1 (worst period)
- Maximum F1 (best period)
- Expected: Avg F1 ≥ 0.65, StdDev ≤ 0.08

**AC6.2.6:** Feature stability analysis
- Track: Which features remain important across retrains?
- Calculate: Feature importance correlation between periods
- Identify: Stable features (high correlation) vs unstable features

**AC6.2.7:** Walk-forward results report
- Report format:
```
========================================
WALK-FORWARD VALIDATION REPORT
========================================
Period: 2022-01-01 to 2025-10-31
Retrain Frequency: Monthly
Total Iterations: 46

SUMMARY:
- Average F1: 0.69 (± 0.07)
- Minimum F1: 0.58 (2024-09, bear market period)
- Maximum F1: 0.78 (2023-04, bull market period)
- Consistency: 85% of periods have F1 ≥ 0.65

PERFORMANCE OVER TIME:
Period     | F1    | Precision | Recall | Samples | Training Time
-----------|-------|-----------|--------|---------|---------------
2022-01    | 0.70  | 0.67      | 0.74   | 1,234   | 2m 15s
2022-02    | 0.72  | 0.69      | 0.76   | 1,189   | 2m 18s
...
2024-12    | 0.68  | 0.64      | 0.73   | 1,567   | 2m 32s

INSIGHTS:
1. Performance stable in 2022-2023 (F1 = 0.71 ± 0.05)
2. Performance degraded in 2024 (F1 = 0.65 ± 0.08)
   - Likely cause: Market regime change (bull → bear)
   - Affected features: rsi_14, macd_signal
3. Recovery in 2025 (F1 = 0.72 ± 0.06)

RECOMMENDATIONS:
1. Retrain monthly to adapt to market changes
2. Monitor drift in rsi_14, macd_signal features
3. Consider shorter training window (180 days) for faster adaptation

========================================
```
- Save to: `/Users/srijan/Desktop/aksh/data/backtesting/walk_forward_results/report.txt`

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/backtesting/walk_forward_validator.py`

**Key Components:**
```python
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd

@dataclass
class WalkForwardIteration:
    period: str
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    f1: float
    precision: float
    recall: float
    n_samples: int
    training_time_seconds: float

@dataclass
class WalkForwardResults:
    iterations: List[WalkForwardIteration]
    avg_f1: float
    std_f1: float
    min_f1: float
    max_f1: float
    consistency_rate: float  # % periods with F1 >= threshold

class WalkForwardValidator:
    def __init__(
        self,
        feature_dbs: Dict[str, str],
        labels_db: str,
        model_type: str = "XGBoost"
    ):
        """Initialize walk-forward validator"""
        
    def run_walk_forward(
        self,
        start_date: str,
        end_date: str,
        retrain_freq: str = "monthly",
        training_window_days: int = 365,
        test_window_days: int = 30
    ) -> WalkForwardResults:
        """
        Run walk-forward validation.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            retrain_freq: "monthly", "quarterly", "yearly"
            training_window_days: Size of rolling training window
            test_window_days: Size of test period
            
        Returns:
            WalkForwardResults with performance per iteration
        """
        
    def generate_date_ranges(
        self,
        start_date: str,
        end_date: str,
        retrain_freq: str,
        training_window_days: int,
        test_window_days: int
    ) -> List[Dict[str, str]]:
        """Generate train/test date ranges for each iteration"""
        
    def train_and_evaluate_period(
        self,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str
    ) -> WalkForwardIteration:
        """Train model and evaluate on test period"""
        
    def analyze_consistency(
        self,
        iterations: List[WalkForwardIteration],
        threshold_f1: float = 0.65
    ) -> float:
        """Calculate % of periods meeting F1 threshold"""
        
    def generate_report(
        self,
        results: WalkForwardResults
    ) -> str:
        """Generate walk-forward report"""
```

**Dependencies:**
- `scikit-learn` - Model training
- `pandas` - Date range generation

**Test File:** `tests/unit/test_walk_forward_validator.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Run 12-month walk-forward
- [ ] Performance test: Complete 36 iterations in <2 hours
- [ ] Manual test: Verify F1 consistency
- [ ] Report generated and saved
- [ ] Documentation: Walk-forward methodology

---

## Story 6.3: Risk Metrics Calculation

**Story ID:** EPIC6-S3
**Priority:** P1
**Estimated Effort:** 2 days
**Dependencies:** EPIC6-S1 (Historical Analyzer)

### User Story

**As a** Risk Manager,
**I want** risk-adjusted performance metrics for the ML model,
**so that** I can assess if the model is suitable for production trading.

### Acceptance Criteria

**AC6.3.1:** RiskCalculator class for financial metrics
- File: `/Users/srijan/Desktop/aksh/agents/ml/backtesting/risk_calculator.py`
- Class: `RiskCalculator` with methods for Sharpe, Sortino, drawdown
- Input: Prediction results + actual outcomes
- Simulate: Trading strategy based on predictions

**AC6.3.2:** Simulate trading strategy
- Strategy: Buy stocks predicted to hit upper circuit (label=1, probability ≥0.7)
- Position size: Equal weight across all signals
- Holding period: 1 day (sell next day)
- Calculate: Daily returns, cumulative returns

**AC6.3.3:** Sharpe ratio calculation
- Formula: `Sharpe = (mean_return - risk_free_rate) / std_return`
- Risk-free rate: 7% annualized (India 10-year bond yield)
- Annualization: `Sharpe_annual = Sharpe_daily * sqrt(252)`
- Target: Sharpe ≥ 1.5

**AC6.3.4:** Sortino ratio calculation
- Formula: `Sortino = (mean_return - risk_free_rate) / downside_std`
- Downside std: Only negative returns
- More relevant than Sharpe for asymmetric strategies
- Target: Sortino ≥ 2.0

**AC6.3.5:** Maximum drawdown calculation
- Formula: `MDD = max((peak - trough) / peak)`
- Track: Rolling peak equity, current equity
- Drawdown periods: Start-to-trough dates
- Target: MDD ≤ 20%

**AC6.3.6:** Additional risk metrics
- **Volatility**: Annualized standard deviation of daily returns
- **Win rate**: % of trades that are profitable
- **Profit factor**: Gross profit / Gross loss
- **Average win/loss ratio**: Avg profit on wins / Avg loss on losses
- **Max consecutive losses**: Longest losing streak

**AC6.3.7:** Risk report generation
- Report format:
```
========================================
RISK METRICS REPORT
========================================
Backtest Period: 2022-01-01 to 2024-12-31
Strategy: Upper Circuit Prediction (Prob ≥ 0.7)

RETURN METRICS:
- Total Return: 47.3%
- Annualized Return: 14.6%
- Cumulative Return: $10,000 → $14,730
- Benchmark (Nifty 50): 12.8%
- Excess Return: +1.8%

RISK METRICS:
- Sharpe Ratio: 1.68 (Target: ≥1.5) ✓
- Sortino Ratio: 2.34 (Target: ≥2.0) ✓
- Maximum Drawdown: -16.2% (Target: ≤20%) ✓
- Volatility (Annualized): 18.7%

TRADING STATISTICS:
- Total Trades: 1,245
- Winning Trades: 823 (66.1%)
- Losing Trades: 422 (33.9%)
- Average Win: +3.2%
- Average Loss: -1.8%
- Win/Loss Ratio: 1.78
- Profit Factor: 2.12
- Max Consecutive Losses: 7

DRAWDOWN ANALYSIS:
Rank | Start Date | Trough Date | Recovery Date | MDD
-----|------------|-------------|---------------|-------
1    | 2024-03-15 | 2024-05-20  | 2024-07-10    | -16.2%
2    | 2023-08-01 | 2023-09-15  | 2023-11-01    | -12.8%
3    | 2022-06-10 | 2022-07-22  | 2022-09-05    | -9.5%

ASSESSMENT: PASS
All risk metrics within acceptable thresholds.
Model suitable for production deployment with risk management.

========================================
```
- Save to: `/Users/srijan/Desktop/aksh/data/backtesting/risk_metrics/risk_report.txt`

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/backtesting/risk_calculator.py`

**Key Components:**
```python
import numpy as np
import pandas as pd
from dataclasses import dataclass

@dataclass
class RiskMetrics:
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_consecutive_losses: int

class RiskCalculator:
    def __init__(self, risk_free_rate: float = 0.07):
        """
        Initialize risk calculator.
        
        Args:
            risk_free_rate: Annualized risk-free rate (default: 7%)
        """
        
    def simulate_trading_strategy(
        self,
        predictions: pd.DataFrame,
        min_probability: float = 0.7
    ) -> pd.DataFrame:
        """
        Simulate trading based on predictions.
        
        Args:
            predictions: DataFrame with (date, bse_code, probability, actual_return)
            min_probability: Minimum probability to take position
            
        Returns:
            DataFrame with (date, position, daily_return, cumulative_return)
        """
        
    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = None
    ) -> float:
        """Calculate annualized Sharpe ratio"""
        
    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = None
    ) -> float:
        """Calculate annualized Sortino ratio"""
        
    def calculate_max_drawdown(
        self,
        cumulative_returns: pd.Series
    ) -> float:
        """Calculate maximum drawdown"""
        
    def calculate_all_metrics(
        self,
        returns: pd.Series
    ) -> RiskMetrics:
        """Calculate all risk metrics"""
        
    def generate_risk_report(
        self,
        metrics: RiskMetrics,
        start_date: str,
        end_date: str
    ) -> str:
        """Generate risk report"""
```

**Dependencies:**
- `numpy` - Calculations
- `pandas` - Time series

**Test File:** `tests/unit/test_risk_calculator.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Calculate metrics on backtest data
- [ ] Validation: Sharpe/Sortino formulas verified
- [ ] Manual test: Compare with industry benchmarks
- [ ] Risk report generated
- [ ] Documentation: Risk metrics methodology

---

## Story 6.4: Backtesting Report Generation

**Story ID:** EPIC6-S4
**Priority:** P1
**Estimated Effort:** 2 days
**Dependencies:** EPIC6-S1, EPIC6-S2, EPIC6-S3

### User Story

**As a** Stakeholder,
**I want** comprehensive HTML backtesting reports with visualizations,
**so that** I can understand model performance and make informed decisions.

### Acceptance Criteria

**AC6.4.1:** ReportGenerator class for HTML reports
- File: `/Users/srijan/Desktop/aksh/agents/ml/backtesting/report_generator.py`
- Class: `ReportGenerator` with method: `generate_html_report(results: Dict) -> str`
- Template engine: Jinja2
- Charts: Plotly.js for interactive visualizations

**AC6.4.2:** Performance summary section
- Key metrics table: F1, precision, recall, ROC-AUC
- Comparison: Train vs Test vs Production performance
- Confusion matrix heatmap
- Classification report table

**AC6.4.3:** Time-based performance charts
- Line chart: F1 score over time (monthly)
- Bar chart: Predictions per month
- Stacked bar: True positives, False positives, True negatives, False negatives
- Trend line: Performance degradation/improvement

**AC6.4.4:** Risk metrics visualization
- Equity curve: Cumulative returns over time
- Drawdown chart: Underwater plot
- Returns distribution histogram
- Rolling Sharpe ratio chart

**AC6.4.5:** Feature importance analysis
- Bar chart: Top 20 features by SHAP value
- Heatmap: Feature importance over time (walk-forward)
- Feature correlation matrix

**AC6.4.6:** Trade-by-trade analysis (if applicable)
- Table: All trades with entry/exit dates, returns
- Win/loss distribution chart
- Calendar heatmap: Returns by day/month
- Export to CSV button

**AC6.4.7:** Interactive report features
- Collapsible sections for detailed analysis
- Hover tooltips on charts
- Date range filter for charts
- Export report as PDF button
- Responsive design (mobile-friendly)

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/backtesting/report_generator.py`

**Key Components:**
```python
from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

class ReportGenerator:
    def __init__(self, template_path: str = None):
        """Initialize report generator with HTML template"""
        
    def generate_html_report(
        self,
        historical_results: Dict,
        walk_forward_results: Dict,
        risk_metrics: Dict,
        output_path: str
    ) -> str:
        """
        Generate comprehensive HTML report.
        
        Args:
            historical_results: From Story 6.1
            walk_forward_results: From Story 6.2
            risk_metrics: From Story 6.3
            output_path: Where to save HTML
            
        Returns:
            Path to generated HTML file
        """
        
    def create_performance_summary_table(
        self,
        results: Dict
    ) -> str:
        """Generate HTML table for performance summary"""
        
    def create_f1_over_time_chart(
        self,
        walk_forward_results: List[Dict]
    ) -> go.Figure:
        """Create interactive Plotly chart"""
        
    def create_equity_curve_chart(
        self,
        cumulative_returns: pd.Series
    ) -> go.Figure:
        """Create equity curve chart"""
        
    def create_feature_importance_chart(
        self,
        shap_values: pd.DataFrame
    ) -> go.Figure:
        """Create feature importance bar chart"""
        
    def render_template(
        self,
        template: Template,
        context: Dict
    ) -> str:
        """Render Jinja2 template with context"""
```

**HTML Template (snippet):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>VCP ML Backtesting Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary-table { border-collapse: collapse; width: 100%; }
        .summary-table td, .summary-table th { border: 1px solid #ddd; padding: 8px; }
        .pass { color: green; font-weight: bold; }
        .fail { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>VCP ML Backtesting Report</h1>
    <p>Generated: {{ timestamp }}</p>
    
    <h2>Performance Summary</h2>
    {{ performance_table | safe }}
    
    <h2>Performance Over Time</h2>
    <div id="f1-chart"></div>
    <script>
        var data = {{ f1_chart_data | tojson }};
        Plotly.newPlot('f1-chart', data);
    </script>
    
    <h2>Risk Metrics</h2>
    {{ risk_metrics_table | safe }}
    
    <h2>Equity Curve</h2>
    <div id="equity-chart"></div>
    
    <!-- More sections -->
</body>
</html>
```

**Dependencies:**
- `jinja2` - Template engine
- `plotly` - Interactive charts
- `pandas` - Data manipulation

**Test File:** `tests/unit/test_report_generator.py`

**Test Coverage Requirements:** ≥85%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥85% coverage
- [ ] Integration test: Generate report with real data
- [ ] Manual test: View report in browser
- [ ] Verify charts are interactive
- [ ] Report saved to HTML file
- [ ] Documentation: Report sections explained

---

## Story 6.5: Strategy Comparison Framework

**Story ID:** EPIC6-S5
**Priority:** P1
**Estimated Effort:** 2 days
**Dependencies:** EPIC6-S1, EPIC6-S3

### User Story

**As a** Research Team,
**I want** a framework to compare different ML strategies,
**so that** I can identify the best model/features/parameters for production.

### Acceptance Criteria

**AC6.5.1:** StrategyComparator class for A/B testing
- File: `/Users/srijan/Desktop/aksh/agents/ml/backtesting/strategy_comparator.py`
- Class: `StrategyComparator` with method: `compare_strategies(strategies: List[Strategy]) -> ComparisonResults`
- Support: Compare models, feature sets, hyperparameters

**AC6.5.2:** Define strategies to compare
- Strategy 1: Baseline (Logistic Regression, 25 features)
- Strategy 2: XGBoost (25 features)
- Strategy 3: LightGBM (25 features)
- Strategy 4: XGBoost (20 features, top importance)
- Strategy 5: XGBoost (30 features, all candidates)
- Each strategy: Train, predict, evaluate independently

**AC6.5.3:** Head-to-head performance comparison
- Metrics: F1, Sharpe ratio, max drawdown, training time
- Table format:
```
Strategy                    | F1    | Sharpe | MDD    | Train Time | Rank
----------------------------|-------|--------|--------|------------|------
XGBoost (25 features)       | 0.72  | 1.68   | -16.2% | 2m 30s     | 1
LightGBM (25 features)      | 0.71  | 1.62   | -17.5% | 1m 45s     | 2
XGBoost (20 features)       | 0.70  | 1.55   | -18.1% | 2m 10s     | 3
Baseline (Logistic Reg)     | 0.65  | 1.32   | -22.3% | 0m 45s     | 4
XGBoost (30 features)       | 0.71  | 1.60   | -16.8% | 3m 15s     | 5
```

**AC6.5.4:** Statistical significance testing
- Test: Are F1 differences statistically significant?
- Use: McNemar's test (paired predictions)
- Report: p-value, confidence interval
- Example: "XGBoost vs Baseline: p=0.003 (significant)"

**AC6.5.5:** Rank strategies by composite score
- Composite score: `0.5*F1 + 0.3*Sharpe + 0.2*(1 - MDD/100)`
- Weights: Prioritize accuracy, then risk-adjusted returns
- Rank: 1 (best) to N (worst)

**AC6.5.6:** Feature set comparison
- Compare: Performance with different feature subsets
- Test: Technical only vs Financial only vs Combined
- Identify: Which feature categories contribute most?

**AC6.5.7:** Comparison report generation
- Report format:
```
========================================
STRATEGY COMPARISON REPORT
========================================
Date: 2025-11-14
Strategies Compared: 5

OVERALL WINNER: XGBoost (25 features)
- F1: 0.72 (best)
- Sharpe: 1.68 (best)
- MDD: -16.2% (best)
- Composite Score: 0.89

PERFORMANCE COMPARISON:
[Table from AC6.5.3]

STATISTICAL SIGNIFICANCE:
- XGBoost vs LightGBM: p=0.12 (not significant)
- XGBoost vs Baseline: p=0.003 (significant)
- XGBoost (25) vs XGBoost (20): p=0.08 (borderline)

FEATURE SET ANALYSIS:
Feature Set                | F1    | Features Used
---------------------------|-------|---------------
Technical Only (15)        | 0.65  | RSI, MACD, Volume, etc.
Financial Only (10)        | 0.68  | Revenue Growth, NPM, etc.
Combined (25)              | 0.72  | All features

INSIGHTS:
1. XGBoost with 25 features is optimal balance
2. Adding 5 more features (30 total) doesn't improve F1
3. Financial features slightly more predictive than technical
4. LightGBM trains 40% faster but 1% lower F1

RECOMMENDATION:
Deploy XGBoost (25 features) to production.
Monitor performance and consider LightGBM if speed becomes critical.

========================================
```
- Save to: `/Users/srijan/Desktop/aksh/data/backtesting/reports/strategy_comparison.html`

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/backtesting/strategy_comparator.py`

**Key Components:**
```python
from dataclasses import dataclass
from typing import List, Dict
import pandas as pd
from scipy.stats import mcnemar

@dataclass
class Strategy:
    name: str
    model_type: str
    features: List[str]
    hyperparameters: Dict

@dataclass
class StrategyPerformance:
    strategy: Strategy
    f1: float
    sharpe: float
    max_drawdown: float
    training_time_seconds: float
    composite_score: float
    rank: int

class StrategyComparator:
    def __init__(
        self,
        feature_dbs: Dict[str, str],
        labels_db: str
    ):
        """Initialize strategy comparator"""
        
    def compare_strategies(
        self,
        strategies: List[Strategy],
        start_date: str,
        end_date: str
    ) -> Dict[str, StrategyPerformance]:
        """
        Compare multiple strategies head-to-head.
        
        Args:
            strategies: List of strategies to compare
            start_date: Backtest start
            end_date: Backtest end
            
        Returns:
            Dict mapping strategy name to performance
        """
        
    def calculate_composite_score(
        self,
        f1: float,
        sharpe: float,
        max_drawdown: float
    ) -> float:
        """Calculate weighted composite score"""
        
    def test_statistical_significance(
        self,
        predictions1: pd.Series,
        predictions2: pd.Series,
        actuals: pd.Series
    ) -> float:
        """McNemar's test for paired predictions, returns p-value"""
        
    def rank_strategies(
        self,
        performances: Dict[str, StrategyPerformance]
    ) -> List[StrategyPerformance]:
        """Rank strategies by composite score"""
        
    def compare_feature_sets(
        self,
        feature_sets: Dict[str, List[str]]
    ) -> pd.DataFrame:
        """Compare performance with different feature subsets"""
        
    def generate_comparison_report(
        self,
        performances: Dict[str, StrategyPerformance],
        output_path: str
    ) -> str:
        """Generate HTML comparison report"""
```

**Dependencies:**
- `scipy` - Statistical tests
- `pandas` - Data manipulation

**Test File:** `tests/unit/test_strategy_comparator.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Compare 5 strategies
- [ ] Statistical test: McNemar's test verified
- [ ] Manual test: Review comparison report
- [ ] Report saved to HTML
- [ ] Documentation: Comparison methodology

---

## Epic Completion Criteria

All 5 stories (EPIC6-S1 through EPIC6-S5) must meet Definition of Done:

- [ ] All acceptance criteria passing for all stories
- [ ] ≥90% unit test coverage across backtesting code
- [ ] Integration tests passing: Full backtesting pipeline
- [ ] Performance validated: F1 ≥ 0.70 on historical data
- [ ] Risk metrics: Sharpe ≥ 1.5, MDD ≤ 20%
- [ ] Reports generated: HTML with interactive charts
- [ ] Deliverables exist:
  - `agents/ml/backtesting/historical_analyzer.py`
  - `agents/ml/backtesting/walk_forward_validator.py`
  - `agents/ml/backtesting/risk_calculator.py`
  - `agents/ml/backtesting/report_generator.py`
  - `agents/ml/backtesting/strategy_comparator.py`
  - `data/backtesting/reports/backtest_report.html`
  - `data/backtesting/reports/strategy_comparison.html`

**Ready for Epic 7:** Production Optimization

---

**Total Duration**: 11 days + 2 day buffer = 13 days
**Next Epic**: Epic 7 - Production Optimization

**Author**: VCP Financial Research Team
**Created**: 2025-11-14
