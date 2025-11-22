# TEST_STRATEGY.md - Test-Driven Development Strategy

**Project**: BMAD Portfolio Management System
**Capital**: ₹1,00,000
**Max Drawdown**: 2%
**Created**: November 19, 2025
**Version**: 1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [TDD Philosophy](#tdd-philosophy)
3. [Test Pyramid](#test-pyramid)
4. [Coverage Goals](#coverage-goals)
5. [Test Framework & Tools](#test-framework--tools)
6. [TDD Workflow](#tdd-workflow)
7. [Test Categories](#test-categories)
8. [Component Test Specifications](#component-test-specifications)
9. [Test Data Management](#test-data-management)
10. [CI/CD Integration](#cicd-integration)
11. [Quality Gates](#quality-gates)

---

## Executive Summary

### Why TDD for This Project?

**User Requirement**: *"Make sure everything that you are creating has a test driven development approach ingrained"*

This portfolio management system handles REAL MONEY (₹1,00,000). A single bug in position sizing, cost calculation, or risk management could:
- Violate the 2% max drawdown constraint
- Execute incorrect trades
- Miscalculate Kelly fractions
- Miss stop-loss exits

**TDD ensures**:
✅ Every component works BEFORE deployment
✅ Risk management logic is provably correct
✅ Backtesting is realistic (catches bugs early)
✅ Paper trading validates production readiness
✅ Refactoring doesn't break existing behavior

### Coverage Targets

| Layer | Coverage Target | Rationale |
|-------|----------------|-----------|
| **Critical Components** | 100% | Risk manager, Kelly sizer, cost calculator |
| **Core Logic** | 95%+ | Signal generators, regime detector, execution |
| **Integration** | 90%+ | End-to-end workflows |
| **Utilities** | 85%+ | Data fetchers, formatters |

### Test Count Targets

- **Unit Tests**: 150+ tests (fast, isolated)
- **Integration Tests**: 30+ tests (multi-component)
- **System Tests**: 10+ tests (end-to-end scenarios)
- **Total**: 190+ automated tests

---

## TDD Philosophy

### The Red-Green-Refactor Cycle

```
┌─────────────────────────────────────────┐
│  1. RED: Write Failing Test             │
│     - Define expected behavior          │
│     - Test fails (code doesn't exist)   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  2. GREEN: Make Test Pass               │
│     - Write minimal code                │
│     - Test passes                       │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  3. REFACTOR: Improve Code              │
│     - Clean up implementation           │
│     - Tests still pass                  │
└─────────────────────────────────────────┘
              ↓
         (Repeat)
```

### Example: Kelly Position Sizer (TDD Style)

#### Step 1: RED - Write Failing Test

```python
# tests/unit/test_kelly_sizer.py
import pytest
from position_sizing.kelly_sizer import KellyPositionSizer

def test_kelly_calculation_basic():
    """Test basic Kelly fraction calculation"""
    sizer = KellyPositionSizer()

    # Given: Strategy with known win rate and payoffs
    win_rate = 0.55
    avg_win = 0.05  # 5% avg win
    avg_loss = 0.03  # 3% avg loss

    # When: Calculate Kelly fraction
    kelly = sizer.calculate_kelly_fraction(win_rate, avg_win, avg_loss)

    # Then: Kelly = (0.55 * 0.05 - 0.45 * 0.03) / 0.05 = 0.28
    assert kelly == pytest.approx(0.28, abs=0.01)

def test_kelly_half_sizing():
    """Test that we use Half-Kelly for safety"""
    sizer = KellyPositionSizer(use_half_kelly=True)

    kelly_full = sizer.calculate_kelly_fraction(0.55, 0.05, 0.03)
    kelly_half = kelly_full / 2

    position_size = sizer.get_position_size(
        capital=100000,
        win_rate=0.55,
        avg_win=0.05,
        avg_loss=0.03
    )

    expected_position = 100000 * kelly_half
    assert position_size == pytest.approx(expected_position, abs=100)

def test_kelly_20_percent_cap():
    """Test that position size is capped at 20% of capital"""
    sizer = KellyPositionSizer(max_position_pct=0.20)

    # Given: Very high Kelly fraction (unrealistic, but tests cap)
    win_rate = 0.80
    avg_win = 0.10
    avg_loss = 0.02

    position_size = sizer.get_position_size(
        capital=100000,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss
    )

    # Then: Never exceed 20% = ₹20,000
    assert position_size <= 20000
```

**Result**: Tests FAIL (KellyPositionSizer doesn't exist yet)

#### Step 2: GREEN - Make Tests Pass

```python
# position_sizing/kelly_sizer.py
class KellyPositionSizer:
    """Kelly Criterion position sizing with safety constraints"""

    def __init__(self, use_half_kelly=True, max_position_pct=0.20):
        self.use_half_kelly = use_half_kelly
        self.max_position_pct = max_position_pct

    def calculate_kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Calculate Kelly fraction

        Formula: Kelly = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
        """
        loss_rate = 1 - win_rate
        kelly = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        return kelly

    def get_position_size(self, capital: float, win_rate: float,
                         avg_win: float, avg_loss: float) -> float:
        """Calculate position size in rupees"""
        kelly = self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)

        if self.use_half_kelly:
            kelly = kelly / 2

        position_size = capital * kelly

        # Cap at max_position_pct
        max_position = capital * self.max_position_pct
        return min(position_size, max_position)
```

**Result**: Tests PASS

#### Step 3: REFACTOR - Add Dynamic Scaling

Now add profit scaling with tests first:

```python
# tests/unit/test_kelly_sizer.py (additional test)
def test_kelly_profit_scaling():
    """Test that Kelly scales up with profit"""
    sizer = KellyPositionSizer()

    # At ₹1L: Standard Kelly
    base_capital = 100000
    base_position = sizer.get_position_size(base_capital, 0.55, 0.05, 0.03)

    # At ₹1.05L (+5%): 1.2× Kelly
    profit_5pct = 105000
    scaled_position_5 = sizer.get_position_size(
        profit_5pct, 0.55, 0.05, 0.03,
        initial_capital=100000
    )
    assert scaled_position_5 == pytest.approx(base_position * 1.2, abs=100)

    # At ₹1.10L (+10%): 1.5× Kelly
    profit_10pct = 110000
    scaled_position_10 = sizer.get_position_size(
        profit_10pct, 0.55, 0.05, 0.03,
        initial_capital=100000
    )
    assert scaled_position_10 == pytest.approx(base_position * 1.5, abs=100)

    # At ₹1.20L (+20%): 2.0× Kelly
    profit_20pct = 120000
    scaled_position_20 = sizer.get_position_size(
        profit_20pct, 0.55, 0.05, 0.03,
        initial_capital=100000
    )
    assert scaled_position_20 == pytest.approx(base_position * 2.0, abs=100)
```

Then implement:

```python
# position_sizing/kelly_sizer.py (refactored)
def get_position_size(self, capital: float, win_rate: float,
                     avg_win: float, avg_loss: float,
                     initial_capital: float = None) -> float:
    """Calculate position size with profit scaling"""
    kelly = self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)

    if self.use_half_kelly:
        kelly = kelly / 2

    # Apply profit scaling
    if initial_capital:
        profit_pct = (capital - initial_capital) / initial_capital
        scale_factor = self._get_profit_scale_factor(profit_pct)
        kelly = kelly * scale_factor

    position_size = capital * kelly

    # Cap at max_position_pct
    max_position = capital * self.max_position_pct
    return min(position_size, max_position)

def _get_profit_scale_factor(self, profit_pct: float) -> float:
    """Get Kelly scaling factor based on profit level"""
    if profit_pct >= 0.20:
        return 2.0
    elif profit_pct >= 0.10:
        return 1.5
    elif profit_pct >= 0.05:
        return 1.2
    else:
        return 1.0
```

**Result**: Tests still PASS, code is cleaner

---

## Test Pyramid

```
                  ╱╲
                 ╱  ╲
                ╱    ╲
               ╱ E2E  ╲           10 tests
              ╱────────╲          (Slow, expensive, high-value)
             ╱          ╲
            ╱ Integration╲        30 tests
           ╱──────────────╲       (Medium speed, multi-component)
          ╱                ╲
         ╱   Unit Tests     ╲     150 tests
        ╱────────────────────╲    (Fast, isolated, thorough)
```

### Unit Tests (150+)
**Purpose**: Test individual functions/methods in isolation
**Speed**: <1ms per test
**Coverage**: 95%+ of all code

**Examples**:
- Kelly fraction calculation
- Cost calculator for Indian markets
- Slippage estimation
- ADX indicator calculation
- DMA crossover detection
- Regime feature extraction
- Sentiment score calculation

### Integration Tests (30+)
**Purpose**: Test multiple components working together
**Speed**: <100ms per test
**Coverage**: Critical workflows

**Examples**:
- Signal → Position Size → Cost → Order
- Market Data → Regime Detection → Strategy Selection
- News → Sentiment → Signal Adjustment
- Backtest → Metrics → Report
- Paper Trade → Virtual Execution → PnL Update

### System Tests (10+)
**Purpose**: Test complete end-to-end scenarios
**Speed**: <5s per test
**Coverage**: Real-world use cases

**Examples**:
- Full backtest (2 years, 500 trades)
- 30-day paper trading simulation
- Live execution dry-run
- Portfolio rebalancing
- Risk limit breach handling

---

## Coverage Goals

### Critical Components (100% Coverage)

These handle MONEY and RISK - no bugs allowed:

```python
# Must have 100% line, branch, and path coverage
CRITICAL_COMPONENTS = [
    "position_sizing/kelly_sizer.py",
    "risk_management/risk_manager.py",
    "execution/cost_calculator.py",
    "execution/slippage_simulator.py",
    "risk_management/drawdown_monitor.py",
]
```

**Enforcement**:
```bash
pytest --cov=position_sizing/kelly_sizer --cov-fail-under=100
pytest --cov=risk_management/risk_manager --cov-fail-under=100
```

### Core Logic (95%+ Coverage)

```python
CORE_COMPONENTS = [
    "signals/adx_dma_scanner.py",
    "signals/camarilla_scanner.py",
    "intelligence/regime_detector.py",
    "intelligence/sentiment_analyzer.py",
    "execution/order_executor.py",
    "backtesting/backtest_engine.py",
    "backtesting/paper_trading_engine.py",
]
```

### Integration & Utilities (90%+ Coverage)

```python
INTEGRATION_COMPONENTS = [
    "data/angel_one_client.py",
    "data/trium_finance_client.py",
    "orchestration/portfolio_manager.py",
    "monitoring/dashboard_api.py",
]
```

### Overall Project Coverage: **93%+**

---

## Test Framework & Tools

### Primary Framework: pytest

**Why pytest?**
- Pythonic and readable
- Excellent fixture support
- Parametrized testing
- Great coverage integration
- Industry standard

### Installation

```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio freezegun
```

### Key Plugins

| Plugin | Purpose | Example |
|--------|---------|---------|
| `pytest-cov` | Code coverage | `pytest --cov=position_sizing` |
| `pytest-mock` | Mocking/stubbing | Mock Angel One API calls |
| `pytest-asyncio` | Async testing | Test async functions |
| `freezegun` | Time manipulation | Freeze time for date-based tests |

### Directory Structure

```
tests/
├── unit/                        # Unit tests (fast, isolated)
│   ├── test_kelly_sizer.py
│   ├── test_cost_calculator.py
│   ├── test_slippage_simulator.py
│   ├── test_risk_manager.py
│   ├── test_adx_dma_scanner.py
│   ├── test_regime_detector.py
│   ├── test_sentiment_analyzer.py
│   └── ...
│
├── integration/                 # Integration tests (multi-component)
│   ├── test_signal_to_order.py
│   ├── test_backtest_pipeline.py
│   ├── test_paper_trading.py
│   ├── test_angel_one_integration.py
│   └── ...
│
├── system/                      # End-to-end tests (full scenarios)
│   ├── test_full_backtest.py
│   ├── test_30day_paper_trading.py
│   ├── test_live_execution_dryrun.py
│   └── ...
│
├── fixtures/                    # Shared test data
│   ├── market_data.py          # Sample OHLCV data
│   ├── news_samples.py         # Sample news for sentiment
│   ├── trade_history.py        # Sample trades for Kelly calc
│   └── ...
│
└── conftest.py                  # pytest configuration
```

---

## TDD Workflow

### Daily Development Cycle

```bash
# 1. Start with failing test
vim tests/unit/test_new_feature.py
# Write test that defines expected behavior

# 2. Run test (watch it fail)
pytest tests/unit/test_new_feature.py -v
# ✗ test_new_feature FAILED

# 3. Implement minimal code
vim src/new_feature.py
# Write just enough to pass

# 4. Run test (watch it pass)
pytest tests/unit/test_new_feature.py -v
# ✓ test_new_feature PASSED

# 5. Refactor if needed
vim src/new_feature.py
# Clean up code

# 6. Run ALL tests (ensure no regressions)
pytest tests/ -v
# All tests still pass

# 7. Check coverage
pytest --cov=src/new_feature --cov-report=term-missing
# Ensure 95%+ coverage

# 8. Commit
git add tests/unit/test_new_feature.py src/new_feature.py
git commit -m "feat: Add new_feature with 100% coverage"
```

### Pre-Commit Checklist

Before every commit:

```bash
# 1. Run all unit tests (fast)
pytest tests/unit/ -v

# 2. Run integration tests
pytest tests/integration/ -v

# 3. Check overall coverage
pytest --cov=src --cov-fail-under=93

# 4. Run linter
flake8 src/ tests/

# 5. Run type checker
mypy src/

# 6. Format code
black src/ tests/
```

---

## Test Categories

### 1. Calculation Tests

**Purpose**: Verify mathematical correctness

**Examples**:
```python
def test_kelly_fraction_calculation():
    """Test Kelly = (p×w - q×l) / w"""
    # Test with known inputs/outputs

def test_indian_cost_calculation():
    """Test brokerage + STT + GST + stamp duty"""
    # Verify against manual calculation

def test_slippage_percentage():
    """Test slippage based on liquidity/size"""
    # Compare to real trade data

def test_adx_calculation():
    """Test ADX formula (Wilder's smoothing)"""
    # Compare to TA-Lib output
```

### 2. Edge Case Tests

**Purpose**: Handle boundary conditions

**Examples**:
```python
def test_kelly_negative_expectancy():
    """Test Kelly returns 0 when strategy has negative edge"""
    # Win rate too low → Kelly should be 0

def test_zero_capital():
    """Test position sizing with zero capital"""
    # Should return 0, not crash

def test_missing_market_data():
    """Test ADX calculation with gaps in data"""
    # Should handle gracefully

def test_extreme_slippage():
    """Test cost when liquidity is very low"""
    # Should warn, not allow trade
```

### 3. Integration Tests

**Purpose**: Test workflows across components

**Examples**:
```python
def test_signal_to_order_workflow():
    """Test: ADX signal → Kelly size → Cost calc → Order"""
    # 1. Generate BUY signal
    # 2. Calculate position size
    # 3. Calculate total cost
    # 4. Create order
    # 5. Verify order details

def test_backtest_with_costs():
    """Test backtest calculates realistic PnL"""
    # 1. Run 100-trade backtest
    # 2. Verify costs deducted each trade
    # 3. Compare to hand-calculated PnL

def test_paper_trading_execution():
    """Test paper trade simulates real execution"""
    # 1. Generate signal
    # 2. Execute virtually
    # 3. Track PnL
    # 4. Verify matches backtest prediction
```

### 4. Mock Tests

**Purpose**: Test external API integration without live calls

**Examples**:
```python
def test_angel_one_order_placement(mocker):
    """Test order placement (mocked)"""
    # Mock SmartAPI.placeOrder
    mock_api = mocker.patch('smartapi.SmartConnect.placeOrder')
    mock_api.return_value = {'orderid': '12345', 'status': 'success'}

    executor = OrderExecutor()
    result = executor.place_order('RELIANCE', 'BUY', 10, 2500)

    assert result['orderid'] == '12345'
    mock_api.assert_called_once()

def test_trium_news_fetch(mocker):
    """Test news fetching (mocked)"""
    mock_response = mocker.patch('requests.get')
    mock_response.return_value.json.return_value = {
        'articles': [{'title': 'Good news', 'sentiment': 'positive'}]
    }

    sentiment = SentimentAnalyzer()
    score = sentiment.analyze_symbol('RELIANCE')

    assert score > 0  # Positive sentiment
```

### 5. Regression Tests

**Purpose**: Prevent bugs from reoccurring

**Examples**:
```python
def test_kelly_doesnt_exceed_capital():
    """Regression: Kelly once returned position > capital"""
    # Bug found in v0.1: Kelly returned 150% position
    # This test prevents recurrence
    sizer = KellyPositionSizer()
    position = sizer.get_position_size(100000, 0.90, 0.10, 0.01)
    assert position <= 100000

def test_cost_includes_all_fees():
    """Regression: Forgot to include stamp duty in v0.2"""
    # Bug: Cost calculator missed stamp duty
    # Test ensures all 6 cost components present
    calc = CostCalculator()
    breakdown = calc.calculate_costs('BUY', 100000)

    assert 'brokerage' in breakdown
    assert 'stt' in breakdown
    assert 'gst' in breakdown
    assert 'stamp_duty' in breakdown
    assert 'exchange_charges' in breakdown
    assert 'sebi_fees' in breakdown
```

---

## Component Test Specifications

### FR-2: Kelly Criterion Position Sizer

#### Unit Tests (15 tests)

```python
# tests/unit/test_kelly_sizer.py

def test_kelly_basic_calculation():
    """Test basic Kelly fraction formula"""

def test_kelly_half_sizing():
    """Test Half-Kelly for safety"""

def test_kelly_20_percent_cap():
    """Test 20% position cap"""

def test_kelly_profit_scaling_5pct():
    """Test 1.2× Kelly at +5% profit"""

def test_kelly_profit_scaling_10pct():
    """Test 1.5× Kelly at +10% profit"""

def test_kelly_profit_scaling_20pct():
    """Test 2.0× Kelly at +20% profit"""

def test_kelly_negative_expectancy():
    """Test Kelly returns 0 for losing strategy"""

def test_kelly_zero_win_rate():
    """Test Kelly with 0% win rate"""

def test_kelly_100_win_rate():
    """Test Kelly with 100% win rate"""

def test_kelly_strategy_performance_update():
    """Test updating strategy stats after trades"""

def test_kelly_insufficient_trade_history():
    """Test Kelly with <30 trades (use conservative default)"""

def test_kelly_fno_4pct_limit():
    """Test F&O positions capped at 4%"""

def test_kelly_equity_higher_limit():
    """Test equity can exceed 4% (up to 20%)"""

def test_kelly_total_risk_constraint():
    """Test total risk never exceeds 2% of peak"""

def test_kelly_drawdown_scaling():
    """Test Kelly reduces when in drawdown"""
```

#### Integration Tests (3 tests)

```python
# tests/integration/test_kelly_integration.py

def test_kelly_with_real_strategy_performance():
    """Test Kelly using real backtest results"""
    # 1. Run ADX+DMA backtest
    # 2. Extract win rate, avg win/loss
    # 3. Calculate Kelly
    # 4. Verify position sizes match expectations

def test_kelly_multi_strategy():
    """Test Kelly for multiple strategies simultaneously"""
    # 1. Strategy A: 55% win, 5%/3% payoffs → Kelly X
    # 2. Strategy B: 40% win, 8%/2% payoffs → Kelly Y
    # 3. Verify total allocation <= 100%

def test_kelly_dynamic_adjustment():
    """Test Kelly adjusts as strategy performance changes"""
    # 1. Start with 50% win rate → Kelly X
    # 2. Simulate 10 wins in a row → Win rate increases → Kelly increases
    # 3. Simulate 10 losses → Win rate decreases → Kelly decreases
```

---

### FR-4: Indian Market Cost Calculator

#### Unit Tests (12 tests)

```python
# tests/unit/test_cost_calculator.py

def test_brokerage_flat_20():
    """Test ₹20 flat brokerage per order"""

def test_brokerage_percentage_0_03():
    """Test 0.03% brokerage (whichever is lower)"""

def test_stt_0_1_percent_sell():
    """Test 0.1% STT on sell side"""

def test_stt_zero_on_buy():
    """Test no STT on buy side"""

def test_gst_18_percent_on_brokerage():
    """Test 18% GST on brokerage"""

def test_stamp_duty_0_015_percent_buy():
    """Test 0.015% stamp duty on buy side"""

def test_exchange_charges_nse():
    """Test NSE exchange charges"""

def test_sebi_fees():
    """Test SEBI turnover fees"""

def test_total_cost_buy_order():
    """Test total cost for BUY order (all components)"""

def test_total_cost_sell_order():
    """Test total cost for SELL order (includes STT)"""

def test_cost_round_trip():
    """Test total cost for BUY + SELL (full trade)"""

def test_cost_percentage_of_capital():
    """Test cost as % of order value"""
```

#### Example Test Implementation:

```python
def test_total_cost_buy_order():
    """Test total cost for ₹1,00,000 BUY order"""
    calc = CostCalculator()

    order_value = 100000
    breakdown = calc.calculate_costs('BUY', order_value)

    # Brokerage: min(₹20, 0.03% of 100k) = ₹20
    assert breakdown['brokerage'] == 20

    # STT: ₹0 (buy side)
    assert breakdown['stt'] == 0

    # GST: 18% of ₹20 = ₹3.60
    assert breakdown['gst'] == pytest.approx(3.60, abs=0.01)

    # Stamp duty: 0.015% of 100k = ₹15
    assert breakdown['stamp_duty'] == pytest.approx(15, abs=0.01)

    # Exchange charges: ~0.00325% of 100k = ₹3.25
    assert breakdown['exchange_charges'] == pytest.approx(3.25, abs=0.5)

    # SEBI fees: 0.0001% of 100k = ₹0.10
    assert breakdown['sebi_fees'] == pytest.approx(0.10, abs=0.01)

    # Total: ₹20 + ₹3.60 + ₹15 + ₹3.25 + ₹0.10 = ₹41.95
    total = sum(breakdown.values())
    assert total == pytest.approx(41.95, abs=1)

    # As % of order: 0.042%
    cost_pct = total / order_value * 100
    assert cost_pct == pytest.approx(0.042, abs=0.01)
```

---

### FR-5: Slippage Simulator

#### Unit Tests (10 tests)

```python
# tests/unit/test_slippage_simulator.py

def test_slippage_high_liquidity():
    """Test minimal slippage for liquid stocks (Nifty 50)"""
    # Reliance, TCS → 0.01-0.02% slippage

def test_slippage_low_liquidity():
    """Test higher slippage for illiquid stocks"""
    # Small-cap → 0.1-0.5% slippage

def test_slippage_large_order():
    """Test slippage increases with order size"""
    # ₹10k order → 0.02%
    # ₹1L order → 0.05%
    # ₹10L order → 0.20%

def test_slippage_high_volatility():
    """Test slippage higher during volatile periods"""
    # VIX < 15 → 0.02%
    # VIX 15-25 → 0.05%
    # VIX > 25 → 0.10%

def test_slippage_market_hours():
    """Test slippage at market open vs mid-day"""
    # 9:15-9:30 AM → Higher slippage
    # 11:00 AM-2:00 PM → Lower slippage

def test_slippage_bid_ask_spread():
    """Test slippage based on bid-ask spread"""
    # Tight spread (₹0.05) → Low slippage
    # Wide spread (₹5) → High slippage

def test_slippage_market_order():
    """Test market orders have higher slippage than limit"""

def test_slippage_limit_order():
    """Test limit orders have zero slippage (by definition)"""

def test_slippage_total_cost():
    """Test slippage adds to transaction cost"""
    # Entry slippage + Exit slippage = Total slippage cost

def test_slippage_realistic_vs_backtest():
    """Test backtest vs paper trading slippage matches"""
```

---

### FR-7: Regime Detector

#### Unit Tests (15 tests)

```python
# tests/unit/test_regime_detector.py

def test_feature_extraction_gap_percentage():
    """Test gap % calculation (open vs prev close)"""

def test_feature_extraction_volume_ratio():
    """Test volume ratio (current vs 20-day avg)"""

def test_feature_extraction_vix_level():
    """Test VIX fetch and classification"""

def test_feature_extraction_nifty_adx():
    """Test Nifty 50 ADX calculation"""

def test_feature_extraction_sentiment_score():
    """Test sentiment integration from Trium Finance"""

def test_regime_classification_expansion():
    """Test expansion day detection (gap up, high volume, high ADX)"""

def test_regime_classification_contraction():
    """Test contraction day (gap down, low volume, low ADX)"""

def test_regime_classification_trending():
    """Test trending day (steady movement, high ADX)"""

def test_regime_classification_choppy():
    """Test choppy day (low ADX, narrow range)"""

def test_regime_classification_volatile():
    """Test volatile day (high VIX, wide range)"""

def test_regime_model_training():
    """Test Random Forest training on historical data"""

def test_regime_model_prediction_confidence():
    """Test prediction returns confidence score"""

def test_regime_strategy_mapping():
    """Test: expansion → ADX+DMA, choppy → range trading"""

def test_regime_fallback_default():
    """Test: if model fails, use default conservative strategy"""

def test_regime_feature_importance():
    """Test: verify VIX and ADX are top features"""
```

#### Integration Tests (3 tests)

```python
# tests/integration/test_regime_integration.py

def test_regime_to_strategy_selection():
    """Test: Regime → Strategy → Signal"""
    # 1. Detect expansion day
    # 2. Select ADX+DMA strategy
    # 3. Generate signals
    # 4. Verify appropriate signals generated

def test_regime_retraining_weekly():
    """Test: Model retrains every Monday with last week's data"""

def test_regime_prediction_morning():
    """Test: Predict day type at 9:15 AM, validate at 3:30 PM"""
```

---

### FR-8: Sentiment Analyzer

#### Unit Tests (12 tests)

```python
# tests/unit/test_sentiment_analyzer.py

def test_news_fetch_trium_finance():
    """Test fetching news from Trium Finance API"""

def test_sentiment_llm_prompt():
    """Test LLM prompt for sentiment scoring"""

def test_sentiment_score_positive():
    """Test positive news → score > 0"""

def test_sentiment_score_negative():
    """Test negative news → score < 0"""

def test_sentiment_score_neutral():
    """Test neutral news → score ≈ 0"""

def test_sentiment_aggregation():
    """Test: Multiple articles → Average sentiment"""

def test_sentiment_recency_weighting():
    """Test: Recent news weighted higher"""

def test_sentiment_source_credibility():
    """Test: ET/Mint weighted higher than blogs"""

def test_sentiment_stock_specific():
    """Test: Filter news for specific symbol"""

def test_sentiment_caching():
    """Test: Cache sentiment for 1 hour"""

def test_sentiment_api_failure():
    """Test: Fallback to neutral if API fails"""

def test_sentiment_position_adjustment():
    """Test: Positive sentiment → Increase position by 10%"""
```

---

### FR-9: Backtesting Engine

#### Unit Tests (20 tests)

```python
# tests/unit/test_backtest_engine.py

def test_backtest_load_historical_data():
    """Test loading 2 years of data"""

def test_backtest_generate_signals():
    """Test signal generation on historical data"""

def test_backtest_calculate_position_sizes():
    """Test Kelly sizing for each trade"""

def test_backtest_apply_costs():
    """Test costs deducted on each trade"""

def test_backtest_apply_slippage():
    """Test slippage applied to entry/exit"""

def test_backtest_track_capital():
    """Test capital updates after each trade"""

def test_backtest_track_drawdown():
    """Test max drawdown calculation"""

def test_backtest_enforce_risk_limits():
    """Test: Block trade if risk > 2%"""

def test_backtest_enforce_position_limits():
    """Test: Block trade if position > 20%"""

def test_backtest_multiple_positions():
    """Test: Hold multiple positions simultaneously"""

def test_backtest_exit_stop_loss():
    """Test: Exit at stop loss price"""

def test_backtest_exit_target():
    """Test: Exit at target price"""

def test_backtest_exit_time():
    """Test: Exit after N days"""

def test_backtest_pyramiding():
    """Test: Add to winning position"""

def test_backtest_metrics_calculation():
    """Test: Win rate, Calmar, Sharpe, max DD"""

def test_backtest_trade_log():
    """Test: Log every trade with details"""

def test_backtest_daily_equity_curve():
    """Test: Track equity daily"""

def test_backtest_compare_to_buy_hold():
    """Test: Benchmark against Nifty buy & hold"""

def test_backtest_realistic_vs_optimistic():
    """Test: Realistic costs vs zero costs difference"""

def test_backtest_deterministic():
    """Test: Same data → Same results (no randomness)"""
```

#### Integration Tests (5 tests)

```python
# tests/integration/test_backtest_integration.py

def test_backtest_adx_dma_strategy_2_years():
    """Test: 2-year backtest of ADX+DMA strategy"""
    # 1. Load 2 years data (2023-2025)
    # 2. Run backtest
    # 3. Verify:
    #    - Win rate > 40%
    #    - Calmar > 2.0
    #    - Max DD < 10%
    #    - Final capital > ₹1.2L (+20%)

def test_backtest_regime_adaptive_strategy():
    """Test: Backtest with regime-based strategy selection"""
    # 1. Train regime model on 2023 data
    # 2. Backtest 2024-2025 with adaptive strategies
    # 3. Compare to single-strategy backtest
    # 4. Verify adaptive is better

def test_backtest_sentiment_enhanced():
    """Test: Backtest with sentiment adjustments"""
    # 1. Load news data
    # 2. Calculate sentiment scores
    # 3. Adjust position sizes
    # 4. Compare to no-sentiment backtest

def test_backtest_walk_forward():
    """Test: Walk-forward optimization"""
    # 1. Train on 2023 → Test on Jan-Jun 2024
    # 2. Train on 2023+H1-2024 → Test on Jul-Dec 2024
    # 3. Train on all 2024 → Test on 2025
    # 4. Verify no overfitting

def test_backtest_monte_carlo():
    """Test: Monte Carlo simulation (random trade order)"""
    # 1. Shuffle trade order 1000 times
    # 2. Calculate DD distribution
    # 3. Verify 95th percentile DD < 10%
```

---

### FR-10: Paper Trading Engine

#### Unit Tests (15 tests)

```python
# tests/unit/test_paper_trading.py

def test_paper_trading_virtual_capital():
    """Test: Track virtual capital separately"""

def test_paper_trading_signal_generation():
    """Test: Generate signals in real-time"""

def test_paper_trading_virtual_execution():
    """Test: Execute trades virtually (no real orders)"""

def test_paper_trading_track_positions():
    """Test: Track open positions"""

def test_paper_trading_track_pnl():
    """Test: Calculate PnL daily"""

def test_paper_trading_apply_costs():
    """Test: Deduct realistic costs"""

def test_paper_trading_apply_slippage():
    """Test: Apply realistic slippage"""

def test_paper_trading_risk_limits():
    """Test: Enforce 2% max DD"""

def test_paper_trading_position_limits():
    """Test: Enforce 20% max position"""

def test_paper_trading_stop_loss():
    """Test: Virtual stop loss execution"""

def test_paper_trading_target_exit():
    """Test: Virtual target exit"""

def test_paper_trading_daily_report():
    """Test: Generate daily report"""

def test_paper_trading_telegram_alerts():
    """Test: Send Telegram notifications"""

def test_paper_trading_vs_backtest_comparison():
    """Test: Paper trading matches backtest predictions"""

def test_paper_trading_30_day_validation():
    """Test: 30-day simulation passes criteria"""
```

---

## Test Data Management

### Mock Data Structure

```
tests/fixtures/
├── market_data/
│   ├── nifty_50_2023.csv           # 1 year OHLCV
│   ├── nifty_50_2024.csv
│   ├── reliance_2023_2024.csv
│   ├── tcs_2023_2024.csv
│   └── ...
│
├── news_data/
│   ├── reliance_positive.json      # Positive news samples
│   ├── reliance_negative.json
│   ├── tcs_neutral.json
│   └── ...
│
├── trade_history/
│   ├── adx_dma_100_trades.json     # Known trade results
│   ├── regime_based_trades.json
│   └── ...
│
└── regime_labels/
    ├── 2023_labeled_days.csv       # Manually labeled days
    ├── 2024_labeled_days.csv
    └── ...
```

### Sample Market Data Fixture

```python
# tests/fixtures/market_data.py
import pandas as pd
import pytest

@pytest.fixture
def nifty_50_sample_data():
    """Sample Nifty 50 data for testing"""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=100),
        'open': [22000 + i*10 for i in range(100)],
        'high': [22100 + i*10 for i in range(100)],
        'low': [21900 + i*10 for i in range(100)],
        'close': [22050 + i*10 for i in range(100)],
        'volume': [1000000 + i*1000 for i in range(100)],
    })

@pytest.fixture
def reliance_buy_signal_day():
    """Day when Reliance has BUY signal"""
    # Close > all 3 DMAs, ADX > 20
    return {
        'date': '2024-11-19',
        'close': 2500,
        'dma_50': 2450,
        'dma_100': 2400,
        'dma_200': 2350,
        'adx': 25,
        'volume_ratio': 1.5,
    }
```

### Sample Trade History Fixture

```python
# tests/fixtures/trade_history.py
import pytest

@pytest.fixture
def adx_dma_known_performance():
    """Known performance for ADX+DMA strategy"""
    return {
        'total_trades': 100,
        'wins': 55,
        'losses': 45,
        'win_rate': 0.55,
        'avg_win_pct': 0.05,
        'avg_loss_pct': 0.03,
        'kelly_fraction': 0.28,  # Pre-calculated
        'half_kelly': 0.14,
    }
```

### Real Data Sources

For integration/system tests, use REAL data:

```python
# tests/integration/conftest.py
import yfinance as yf
import pytest

@pytest.fixture(scope="session")
def real_nifty_data():
    """Download real Nifty 50 data (cached per session)"""
    nifty = yf.Ticker("^NSEI")
    df = nifty.history(period="2y")
    return df

@pytest.fixture(scope="session")
def real_reliance_data():
    """Download real Reliance data"""
    reliance = yf.Ticker("RELIANCE.NS")
    df = reliance.history(period="2y")
    return df
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock pytest-asyncio

    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src --cov-report=xml

    - name: Check critical component coverage
      run: |
        pytest --cov=position_sizing/kelly_sizer --cov-fail-under=100
        pytest --cov=risk_management/risk_manager --cov-fail-under=100
        pytest --cov=execution/cost_calculator --cov-fail-under=100

    - name: Run integration tests
      run: |
        pytest tests/integration/ -v

    - name: Run system tests
      run: |
        pytest tests/system/ -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']

  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest tests/unit/ -v
        language: system
        pass_filenames: false
        always_run: true
```

---

## Quality Gates

### Gate 1: Pre-Commit (Developer Machine)

**Requirements**:
- ✅ All unit tests pass
- ✅ Code coverage ≥ 93%
- ✅ Critical components 100% coverage
- ✅ Flake8 linting passes
- ✅ Black formatting applied

**Command**:
```bash
pytest tests/unit/ --cov=src --cov-fail-under=93 && \
pytest --cov=position_sizing/kelly_sizer --cov-fail-under=100 && \
flake8 src/ && \
black src/ tests/
```

### Gate 2: Pull Request (GitHub Actions)

**Requirements**:
- ✅ All unit tests pass (150+ tests)
- ✅ All integration tests pass (30+ tests)
- ✅ Coverage ≥ 93%
- ✅ No new linting errors
- ✅ Code review approved

### Gate 3: Backtest Validation

**Requirements**:
- ✅ 2-year backtest completes
- ✅ Win rate ≥ 40%
- ✅ Calmar ratio ≥ 2.0
- ✅ Max drawdown < 10%
- ✅ Realistic costs applied
- ✅ Results match hand-calculated sample

**Command**:
```bash
pytest tests/system/test_full_backtest.py -v
```

### Gate 4: Paper Trading Validation

**Requirements**:
- ✅ 30-day paper trading completes
- ✅ Virtual capital never breaches 2% DD
- ✅ Win rate matches backtest (±5%)
- ✅ Daily reports generated
- ✅ No execution errors

**Command**:
```bash
pytest tests/system/test_30day_paper_trading.py -v
```

### Gate 5: Soft Launch Validation

**Requirements**:
- ✅ All tests pass
- ✅ Backtest successful
- ✅ Paper trading successful
- ✅ Live execution dry-run successful
- ✅ ₹25,000 capital test (1 week)
- ✅ Manual review of first 5 trades

### Gate 6: Full Launch

**Requirements**:
- ✅ Soft launch successful
- ✅ No critical bugs found
- ✅ Drawdown < 1% during soft launch
- ✅ Win rate matches predictions
- ✅ User approval for full ₹1L deployment

---

## Example: Full TDD Cycle for Cost Calculator

### Step 1: Write Tests First

```python
# tests/unit/test_cost_calculator.py
import pytest
from execution.cost_calculator import CostCalculator

class TestCostCalculator:
    """Test Indian market cost calculations"""

    def test_buy_order_100k(self):
        """Test costs for ₹1,00,000 BUY order"""
        calc = CostCalculator()
        costs = calc.calculate_costs('BUY', 100000)

        # Brokerage: min(₹20, 0.03% of 100k) = ₹20
        assert costs['brokerage'] == 20

        # STT: ₹0 (buy side)
        assert costs['stt'] == 0

        # GST: 18% of ₹20 = ₹3.60
        assert costs['gst'] == pytest.approx(3.60, abs=0.01)

        # Stamp duty: 0.015% of 100k = ₹15
        assert costs['stamp_duty'] == pytest.approx(15, abs=0.01)

        # Total ≈ ₹42
        total = sum(costs.values())
        assert 40 <= total <= 45

    def test_sell_order_100k(self):
        """Test costs for ₹1,00,000 SELL order"""
        calc = CostCalculator()
        costs = calc.calculate_costs('SELL', 100000)

        # STT: 0.1% of 100k = ₹100
        assert costs['stt'] == pytest.approx(100, abs=1)

        # No stamp duty on sell
        assert costs['stamp_duty'] == 0

        # Total ≈ ₹123 (brokerage + STT + GST + exchange + SEBI)
        total = sum(costs.values())
        assert 120 <= total <= 130

    def test_round_trip_costs(self):
        """Test BUY + SELL round-trip cost"""
        calc = CostCalculator()

        buy_costs = calc.calculate_costs('BUY', 100000)
        sell_costs = calc.calculate_costs('SELL', 100000)

        total_round_trip = sum(buy_costs.values()) + sum(sell_costs.values())

        # Round trip ≈ ₹165 (₹42 buy + ₹123 sell)
        assert 160 <= total_round_trip <= 170

        # As % of capital: ~0.165%
        cost_pct = total_round_trip / 100000 * 100
        assert 0.16 <= cost_pct <= 0.17
```

**Run tests**: `pytest tests/unit/test_cost_calculator.py -v`
**Result**: ❌ All FAIL (CostCalculator doesn't exist)

### Step 2: Implement to Pass Tests

```python
# execution/cost_calculator.py
class CostCalculator:
    """Calculate all Indian market transaction costs"""

    def __init__(self):
        self.brokerage_flat = 20  # ₹20 per order
        self.brokerage_pct = 0.0003  # 0.03%
        self.stt_sell_pct = 0.001  # 0.1% on sell
        self.gst_pct = 0.18  # 18% on brokerage
        self.stamp_duty_buy_pct = 0.00015  # 0.015% on buy
        self.exchange_charges_pct = 0.0000325  # ~0.00325%
        self.sebi_fees_pct = 0.000001  # 0.0001%

    def calculate_costs(self, side: str, order_value: float) -> dict:
        """
        Calculate all costs for Indian market trade

        Args:
            side: 'BUY' or 'SELL'
            order_value: Total order value in ₹

        Returns:
            Dictionary with cost breakdown
        """
        costs = {}

        # 1. Brokerage (lower of flat or percentage)
        brokerage_pct_amount = order_value * self.brokerage_pct
        costs['brokerage'] = min(self.brokerage_flat, brokerage_pct_amount)

        # 2. STT (only on sell side)
        if side == 'SELL':
            costs['stt'] = order_value * self.stt_sell_pct
        else:
            costs['stt'] = 0

        # 3. GST (on brokerage)
        costs['gst'] = costs['brokerage'] * self.gst_pct

        # 4. Stamp duty (only on buy side)
        if side == 'BUY':
            costs['stamp_duty'] = order_value * self.stamp_duty_buy_pct
        else:
            costs['stamp_duty'] = 0

        # 5. Exchange charges
        costs['exchange_charges'] = order_value * self.exchange_charges_pct

        # 6. SEBI fees
        costs['sebi_fees'] = order_value * self.sebi_fees_pct

        return costs
```

**Run tests**: `pytest tests/unit/test_cost_calculator.py -v`
**Result**: ✅ All PASS

### Step 3: Refactor & Add Features

Now add more tests and features:

```python
# tests/unit/test_cost_calculator.py (add more tests)
def test_cost_as_percentage():
    """Test get total cost as percentage"""
    calc = CostCalculator()
    cost_pct = calc.get_cost_percentage('BUY', 100000)
    assert 0.04 <= cost_pct <= 0.05

def test_net_proceeds_after_costs():
    """Test net proceeds after selling"""
    calc = CostCalculator()

    # Buy at ₹1L, sell at ₹1.05L (+5%)
    buy_costs = calc.get_total_cost('BUY', 100000)
    sell_costs = calc.get_total_cost('SELL', 105000)

    gross_profit = 105000 - 100000  # ₹5,000
    net_profit = gross_profit - buy_costs - sell_costs

    # Net profit ≈ ₹5,000 - ₹42 - ₹128 = ₹4,830
    assert 4800 <= net_profit <= 4900
```

Implement:

```python
# execution/cost_calculator.py (add methods)
def get_total_cost(self, side: str, order_value: float) -> float:
    """Get total cost as single number"""
    costs = self.calculate_costs(side, order_value)
    return sum(costs.values())

def get_cost_percentage(self, side: str, order_value: float) -> float:
    """Get total cost as percentage of order value"""
    total = self.get_total_cost(side, order_value)
    return (total / order_value) * 100
```

**Run tests**: `pytest tests/unit/test_cost_calculator.py -v`
**Result**: ✅ All PASS

### Step 4: Integration Test

```python
# tests/integration/test_cost_in_backtest.py
def test_backtest_applies_costs():
    """Test backtest deducts realistic costs"""
    from backtesting.backtest_engine import BacktestEngine
    from execution.cost_calculator import CostCalculator

    # Create simple backtest: 1 trade
    engine = BacktestEngine(initial_capital=100000)

    # Simulate: BUY ₹1L, SELL at ₹1.05L
    engine.execute_trade('BUY', 100000, entry_price=2500, shares=40)
    engine.execute_trade('SELL', 105000, exit_price=2625, shares=40)

    # Gross profit: ₹5,000
    # Costs: ~₹170
    # Net profit: ₹4,830

    net_pnl = engine.get_net_pnl()
    assert 4800 <= net_pnl <= 4900

    # Verify cost calculator was used
    assert engine.total_costs_paid > 160
    assert engine.total_costs_paid < 180
```

---

## Summary

### TDD Ensures Quality

1. **Write tests FIRST** → Define expected behavior
2. **Implement code** → Make tests pass
3. **Refactor** → Improve without breaking tests
4. **Repeat** → Build robust system incrementally

### Coverage Targets

- **Critical components**: 100% (Kelly, Risk Manager, Costs)
- **Core logic**: 95%+ (Signals, Regime, Execution)
- **Overall project**: 93%+

### Test Pyramid

- **150+ Unit tests**: Fast, isolated, thorough
- **30+ Integration tests**: Multi-component workflows
- **10+ System tests**: End-to-end scenarios

### Quality Gates

1. Pre-commit: All tests pass, 93%+ coverage
2. Pull request: CI/CD validates
3. Backtest: 2-year validation
4. Paper trading: 30-day validation
5. Soft launch: ₹25K test
6. Full launch: User approval

### Why This Matters

**User said**: *"Make sure everything that you are creating has a test driven development approach ingrained"*

This portfolio manages **₹1,00,000** of REAL MONEY. TDD ensures:
- ✅ Risk management never fails (2% max DD enforced)
- ✅ Position sizing is correct (Kelly + caps)
- ✅ Costs are realistic (no false profits)
- ✅ Backtesting is trustworthy (realistic simulation)
- ✅ Paper trading validates predictions
- ✅ Live trading is production-ready

**No shortcuts. No bugs. No losses due to code errors.**

---

**Next Steps**:
1. ✅ PRD.md created
2. ✅ ARCHITECTURE.md created
3. ✅ TEST_STRATEGY.md created
4. ⏳ Create FX documents (8 functional specs)
5. ⏳ Create STORY documents (user stories)
6. ⏳ Create SHORT tasks (implementation tasks)
7. ⏳ Initialize test suite structure
8. ⏳ Begin TDD implementation

**Created**: November 19, 2025
**Author**: Portfolio Management System Team
**Review Status**: Ready for User Review
