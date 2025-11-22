"""
Data Models for Backtesting System

Foundation classes for trades, backtest results, and performance metrics.
Following research-backed thresholds from BMAD architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd


@dataclass
class Trade:
    """Individual trade record"""
    symbol: str
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    position_size: int = 1
    pnl: float = 0.0
    pnl_pct: float = 0.0
    trade_duration_days: int = 0
    max_favorable_excursion: float = 0.0  # MFE - max profit during trade
    max_adverse_excursion: float = 0.0    # MAE - max loss during trade
    exit_reason: str = "signal"  # signal, stop_loss, target, time_exit

    def __post_init__(self):
        """Calculate derived fields"""
        if self.pnl == 0.0:
            self.pnl = (self.exit_price - self.entry_price) * self.position_size
        if self.pnl_pct == 0.0:
            self.pnl_pct = ((self.exit_price - self.entry_price) / self.entry_price) * 100
        if self.trade_duration_days == 0:
            self.trade_duration_days = (self.exit_date - self.entry_date).days


@dataclass
class BacktestResult:
    """Complete backtest results"""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Basic metrics (calculated on demand)
    total_return_pct: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    def __post_init__(self):
        """Calculate basic metrics"""
        if self.total_return_pct == 0.0:
            self.total_return_pct = ((self.final_capital - self.initial_capital) /
                                    self.initial_capital) * 100
        if self.total_trades == 0:
            self.total_trades = len(self.trades)
        if self.winning_trades == 0:
            self.winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        if self.losing_trades == 0:
            self.losing_trades = sum(1 for t in self.trades if t.pnl < 0)


@dataclass
class PerformanceMetrics:
    """Performance analysis metrics"""
    # Returns
    total_return_pct: float = 0.0
    annualized_return_pct: float = 0.0
    cagr_pct: float = 0.0

    # Risk-adjusted returns
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Win/Loss statistics
    win_rate_pct: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0  # Average $ per trade
    expectancy_pct: float = 0.0  # Average % per trade

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    largest_win_pct: float = 0.0
    largest_loss_pct: float = 0.0

    # Duration
    avg_trade_duration_days: float = 0.0
    avg_winning_duration_days: float = 0.0
    avg_losing_duration_days: float = 0.0

    # Consecutive stats
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0

    # Statistical significance
    is_statistically_significant: bool = False
    sample_size_adequate: bool = False  # >= 30 trades
    time_period_adequate: bool = False  # >= 2 years


@dataclass
class RiskMetrics:
    """Risk assessment metrics"""
    # Drawdown
    max_drawdown_pct: float = 0.0
    max_drawdown_duration_days: int = 0
    avg_drawdown_pct: float = 0.0
    current_drawdown_pct: float = 0.0

    # Volatility
    daily_volatility_pct: float = 0.0
    annualized_volatility_pct: float = 0.0
    downside_volatility_pct: float = 0.0

    # Value at Risk
    var_95_pct: float = 0.0  # 95% confidence
    var_99_pct: float = 0.0  # 99% confidence
    cvar_95_pct: float = 0.0  # Conditional VaR (expected shortfall)

    # Risk levels (based on research thresholds)
    drawdown_risk_level: str = "unknown"  # low, moderate, high, critical
    volatility_risk_level: str = "unknown"

    def assess_drawdown_risk(self) -> str:
        """
        Assess drawdown risk level
        Thresholds: <10% = low, 10-20% = moderate, 20-30% = high, >30% = critical
        """
        if self.max_drawdown_pct < 10:
            return "low"
        elif self.max_drawdown_pct < 20:
            return "moderate"
        elif self.max_drawdown_pct < 30:
            return "high"
        else:
            return "critical"

    def __post_init__(self):
        """Calculate risk levels"""
        if self.drawdown_risk_level == "unknown":
            self.drawdown_risk_level = self.assess_drawdown_risk()


@dataclass
class StrategyComplexity:
    """Strategy complexity analysis"""
    total_rules: int = 0
    total_parameters: int = 0
    parameter_names: List[str] = field(default_factory=list)

    # Complexity assessment
    is_too_complex: bool = False
    complexity_score: float = 0.0  # 0-100
    complexity_warning: str = ""

    def __post_init__(self):
        """Assess complexity"""
        # Research: >5-7 rules or >4-6 parameters = warning
        if self.total_rules > 7 or self.total_parameters > 6:
            self.is_too_complex = True
            self.complexity_warning = (
                f"High complexity: {self.total_rules} rules, "
                f"{self.total_parameters} parameters. Risk of overfitting."
            )

        # Complexity score (lower is better)
        rule_score = min(100, (self.total_rules / 7) * 50)
        param_score = min(100, (self.total_parameters / 6) * 50)
        self.complexity_score = rule_score + param_score


@dataclass
class OverfittingAssessment:
    """Overfitting detection results"""
    is_likely_overfit: bool = False
    risk_score: float = 0.0  # 0-100, higher = more risk
    issues_found: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Specific checks
    excessive_parameters: bool = False
    suspicious_win_rate: bool = False  # >85%
    in_sample_oos_degradation_pct: float = 0.0
    parameter_sensitivity_high: bool = False

    def add_issue(self, issue: str):
        """Add overfitting issue"""
        self.issues_found.append(issue)
        self.is_likely_overfit = True

    def add_warning(self, warning: str):
        """Add warning"""
        self.warnings.append(warning)


@dataclass
class WalkForwardResult:
    """Walk-forward analysis result"""
    window_number: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime

    # In-sample (training)
    in_sample_return_pct: float = 0.0
    in_sample_sharpe: float = 0.0
    in_sample_max_dd_pct: float = 0.0
    in_sample_trades: int = 0

    # Out-of-sample (testing)
    oos_return_pct: float = 0.0
    oos_sharpe: float = 0.0
    oos_max_dd_pct: float = 0.0
    oos_trades: int = 0

    # Degradation
    return_degradation_pct: float = 0.0
    sharpe_degradation_pct: float = 0.0

    def __post_init__(self):
        """Calculate degradation"""
        if self.in_sample_return_pct != 0:
            self.return_degradation_pct = (
                ((self.oos_return_pct - self.in_sample_return_pct) /
                 abs(self.in_sample_return_pct)) * 100
            )

        if self.in_sample_sharpe != 0:
            self.sharpe_degradation_pct = (
                ((self.oos_sharpe - self.in_sample_sharpe) /
                 abs(self.in_sample_sharpe)) * 100
            )


@dataclass
class WalkForwardAnalysis:
    """Complete walk-forward analysis"""
    num_windows: int
    window_results: List[WalkForwardResult] = field(default_factory=list)

    # Aggregate metrics
    avg_return_degradation_pct: float = 0.0
    avg_sharpe_degradation_pct: float = 0.0
    consistency_score: float = 0.0  # 0-100

    # Pass/fail
    is_robust: bool = False
    degradation_acceptable: bool = False  # <30%

    def calculate_consistency(self):
        """Calculate consistency across windows"""
        if not self.window_results:
            return

        # Average degradation
        self.avg_return_degradation_pct = sum(
            w.return_degradation_pct for w in self.window_results
        ) / len(self.window_results)

        self.avg_sharpe_degradation_pct = sum(
            w.sharpe_degradation_pct for w in self.window_results
        ) / len(self.window_results)

        # Check if acceptable (<30% degradation)
        self.degradation_acceptable = (
            abs(self.avg_return_degradation_pct) < 30 and
            abs(self.avg_sharpe_degradation_pct) < 30
        )

        # Consistency score (based on variance of OOS results)
        oos_returns = [w.oos_return_pct for w in self.window_results]
        if oos_returns:
            import statistics
            avg = statistics.mean(oos_returns)
            if avg != 0:
                cv = (statistics.stdev(oos_returns) / abs(avg)) if len(oos_returns) > 1 else 0
                # Lower CV = more consistent
                self.consistency_score = max(0, 100 - (cv * 100))

        # Robust if degradation acceptable and consistency high
        self.is_robust = (
            self.degradation_acceptable and
            self.consistency_score > 60
        )


@dataclass
class ExecutiveSummary:
    """Final go/no-go decision with recommendations"""
    strategy_name: str
    analyzed_date: datetime

    # Overall decision
    decision: str = "NO GO"  # GO, NO GO, PROCEED WITH CAUTION
    confidence_score: float = 0.0  # 0-100

    # Key metrics
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate_pct: float = 0.0

    # Traffic lights
    performance_status: str = "red"  # green, yellow, red
    risk_status: str = "red"
    robustness_status: str = "red"
    complexity_status: str = "red"

    # Issues and recommendations
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Supporting data
    sample_size: int = 0
    backtest_period_years: float = 0.0

    def determine_decision(self):
        """Determine final go/no-go decision"""
        green_count = sum([
            self.performance_status == "green",
            self.risk_status == "green",
            self.robustness_status == "green",
            self.complexity_status == "green"
        ])

        red_count = sum([
            self.performance_status == "red",
            self.risk_status == "red",
            self.robustness_status == "red",
            self.complexity_status == "red"
        ])

        if red_count > 0 or len(self.critical_issues) > 0:
            self.decision = "NO GO"
            self.confidence_score = 100 - (red_count * 15) - (len(self.critical_issues) * 10)
        elif green_count >= 3:
            self.decision = "GO"
            self.confidence_score = 70 + (green_count * 7.5)
        else:
            self.decision = "PROCEED WITH CAUTION"
            self.confidence_score = 50 + (green_count * 10)

        self.confidence_score = max(0, min(100, self.confidence_score))
