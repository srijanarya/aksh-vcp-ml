# Portfolio Management System - System Architecture

**Version**: 1.0
**Date**: November 19, 2025
**Status**: Draft

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Diagram](#component-diagram)
4. [Data Flow](#data-flow)
5. [Component Specifications](#component-specifications)
6. [Database Schema](#database-schema)
7. [API Contracts](#api-contracts)
8. [Deployment Architecture](#deployment-architecture)
9. [Technology Stack](#technology-stack)

---

## System Overview

### High-Level Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      EXTERNAL DATA SOURCES                      │
├───────────────────────────────────────────────────────────────┤
│  - Angel One SmartAPI (live prices, orders, positions)        │
│  - Trium Finance API (news, sentiment)                        │
│  - Yahoo Finance (historical data for backtesting)            │
│  - NSE/BSE (market regime indicators - VIX, Nifty)           │
└───────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌───────────────────────────────────────────────────────────────┐
│                       DATA INGESTION LAYER                      │
├───────────────────────────────────────────────────────────────┤
│  agents/data/                                                  │
│  ├── angel_one_client.py        # Angel One API wrapper       │
│  ├── trium_news_fetcher.py      # News API client             │
│  └── market_data_provider.py    # Unified data interface      │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE & DECISION LAYER                │
├───────────────────────────────────────────────────────────────┤
│  agents/intelligence/                                          │
│  ├── regime_detector.py         # ML-based day type detection │
│  ├── sentiment_analyzer.py      # News sentiment scoring      │
│  ├── strategy_selector.py       # RL-based strategy choice    │
│  └── optimal_strategy_finder.py # Historical best strategy     │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                     SIGNAL GENERATION LAYER                     │
├───────────────────────────────────────────────────────────────┤
│  agents/signals/                                               │
│  ├── adx_dma_scanner.py         # ADX + 3-DMA strategy        │
│  ├── camarilla_scanner.py       # Camarilla pivot strategy    │
│  ├── volume_breakout_scanner.py # Volume breakout strategy    │
│  └── signal_aggregator.py       # Combines all signals        │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                   POSITION SIZING & RISK LAYER                  │
├───────────────────────────────────────────────────────────────┤
│  agents/risk/                                                  │
│  ├── kelly_position_sizer.py    # Kelly Criterion calculator  │
│  ├── diversification_manager.py # 20% per stock enforcer      │
│  ├── risk_manager.py            # 2% max DD enforcer          │
│  └── pyramid_manager.py         # Add to winners logic        │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                     EXECUTION & COST LAYER                      │
├───────────────────────────────────────────────────────────────┤
│  agents/execution/                                             │
│  ├── cost_calculator.py         # Indian market costs         │
│  ├── slippage_simulator.py      # Realistic fill modeling     │
│  ├── order_executor.py          # Angel One order placement   │
│  └── position_tracker.py        # Track open positions        │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                    BACKTESTING & VALIDATION LAYER               │
├───────────────────────────────────────────────────────────────┤
│  agents/validation/                                            │
│  ├── backtest_engine.py         # Historical validation       │
│  ├── paper_trading_engine.py    # Live simulation             │
│  └── performance_analyzer.py    # Metrics & reporting         │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                    MONITORING & REPORTING LAYER                 │
├───────────────────────────────────────────────────────────────┤
│  agents/monitoring/                                            │
│  ├── dashboard_api.py           # FastAPI web interface       │
│  ├── telegram_bot.py            # Alerts & notifications      │
│  ├── performance_logger.py      # Metrics tracking            │
│  └── rl_tracker.py              # Strategy performance DB     │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│                         DATA PERSISTENCE LAYER                  │
├───────────────────────────────────────────────────────────────┤
│  data/                                                         │
│  ├── portfolio.db               # SQLite: capital, positions  │
│  ├── trades.db                  # SQLite: trade history       │
│  ├── regime_training.db         # SQLite: ML training data    │
│  └── performance.db             # SQLite: strategy stats      │
└───────────────────────────────────────────────────────────────┘
```

---

## Architecture Principles

### 1. **Modularity**
- Each component is independent and testable
- Clear interfaces between components (API contracts)
- Can swap implementations without affecting others

### 2. **Test-Driven Development**
- Write tests BEFORE implementation
- Unit tests for each component (90%+ coverage)
- Integration tests for workflows
- System tests for end-to-end scenarios

### 3. **Data-Driven Decisions**
- Every trading decision backed by data
- ML models trained on historical data
- Continuous learning from live results

### 4. **Fail-Safe Design**
- Hard limits enforced in code (2% DD, 20% per stock)
- Multiple safety checks before orders
- Graceful degradation if external APIs fail

### 5. **Observability**
- Comprehensive logging (but mask sensitive data)
- Real-time monitoring dashboard
- Alerts for anomalies

---

## Component Diagram

### Layer 1: Data Ingestion

```python
# agents/data/market_data_provider.py

class MarketDataProvider:
    """
    Unified interface for all market data

    Abstracts:
    - Angel One (live data, orders)
    - Yahoo Finance (historical for backtest)
    - Trium Finance (news)
    """

    def get_live_price(self, symbol: str) -> float:
        """Get current market price from Angel One"""

    def get_historical_ohlcv(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        """Get historical OHLCV for backtesting"""

    def get_news(self, symbol: str, lookback_hours: int = 24) -> List[Dict]:
        """Get recent news from Trium Finance"""

    def get_vix(self) -> float:
        """Get current VIX (volatility index)"""
```

**Dependencies**: Angel One SmartAPI, yfinance, Trium Finance API

**Tests**:
- `tests/unit/test_market_data_provider.py`
- Mock external APIs, test data fetching logic

---

### Layer 2: Intelligence & Decision

#### Component 2.1: Regime Detector

```python
# agents/intelligence/regime_detector.py

class RegimeDetector:
    """
    ML-based market regime detection

    Classifies each day as:
    - Expansion (gap up + volume)
    - Contraction (narrow range)
    - Trending (strong ADX)
    - Choppy (low ADX)
    - High Volatility (VIX >20)
    """

    def __init__(self, model_path: str):
        self.model = self.load_model(model_path)  # Random Forest or XGBoost

    def extract_morning_features(self, date: str) -> Dict:
        """
        At 9:15 AM, extract features:
        - Gap %
        - Pre-market volume
        - VIX level
        - Nifty ADX
        - Sentiment score
        """

    def predict_day_type(self, features: Dict) -> Tuple[str, float]:
        """
        Predict today's regime

        Returns:
            (day_type, confidence)
        """

    def train_on_historical(self, labeled_data: pd.DataFrame):
        """
        Train ML model on past days
        Each row: [features] → optimal_strategy
        """
```

**Training Data Schema**:
```sql
CREATE TABLE regime_training (
    date DATE PRIMARY KEY,
    gap_pct REAL,
    range_pct REAL,
    volume_ratio REAL,
    vix REAL,
    nifty_adx REAL,
    sentiment REAL,
    day_type TEXT,  -- expansion, contraction, trending, choppy, volatile
    best_strategy TEXT  -- which strategy won that day
);
```

**Tests**:
- `tests/unit/test_regime_detector.py`
  - Test feature extraction
  - Test prediction with known model
  - Test training convergence

---

#### Component 2.2: Sentiment Analyzer

```python
# agents/intelligence/sentiment_analyzer.py

class SentimentAnalyzer:
    """
    News sentiment analysis using Trium Finance + LLM
    """

    def __init__(self, trium_api_key: str, llm_api_key: str):
        self.trium = TriumFinanceClient(trium_api_key)
        self.llm = LLMClient(llm_api_key)  # GPT-4 or Claude

    def get_stock_sentiment(self, symbol: str, lookback_hours: int = 24) -> Dict:
        """
        Returns:
        {
            'score': -1.0 to +1.0,  # bearish to bullish
            'confidence': 0.0 to 1.0,
            'article_count': int,
            'key_topics': List[str]
        }
        """
        articles = self.trium.fetch_news(symbol, lookback_hours)

        if not articles:
            return {'score': 0.0, 'confidence': 0.0, 'article_count': 0}

        sentiments = []
        for article in articles:
            sentiment = self.analyze_article(article)
            sentiments.append(sentiment)

        return {
            'score': np.mean([s['score'] for s in sentiments]),
            'confidence': np.mean([s['confidence'] for s in sentiments]),
            'article_count': len(articles),
            'key_topics': self.extract_topics(articles)
        }

    def analyze_article(self, article: Dict) -> Dict:
        """
        Use LLM to score sentiment

        Prompt: "Analyze this financial news. Score from -1 (bearish) to +1 (bullish)"
        """
        prompt = f"""
        Analyze the sentiment of this financial news article.

        Title: {article['title']}
        Summary: {article['summary']}

        Provide a sentiment score from -1 (very bearish) to +1 (very bullish).
        Also provide confidence from 0 (uncertain) to 1 (very confident).

        Return JSON: {{"score": float, "confidence": float, "reasoning": str}}
        """

        response = self.llm.complete(prompt)
        return json.loads(response)

    def should_adjust_trade(self, signal_type: str, sentiment: Dict) -> Tuple[bool, float]:
        """
        Decision logic:

        Returns:
            (should_trade, position_size_multiplier)
        """
        if signal_type == 'BUY':
            if sentiment['score'] < -0.3 and sentiment['confidence'] > 0.6:
                return (False, 0.0)  # Skip trade, bearish sentiment
            elif sentiment['score'] > 0.5 and sentiment['confidence'] > 0.6:
                return (True, 1.2)  # Increase size by 20%, bullish confirmation
            else:
                return (True, 1.0)  # Normal size, neutral sentiment
```

**Tests**:
- `tests/unit/test_sentiment_analyzer.py`
  - Test sentiment scoring with mock LLM
  - Test trade filtering logic
  - Test Trium API integration (mocked)

---

#### Component 2.3: Strategy Selector (RL)

```python
# agents/intelligence/strategy_selector.py

class StrategySelector:
    """
    Reinforcement Learning: Allocate capital to best-performing strategies
    """

    def __init__(self):
        self.strategy_stats = {
            'adx_dma_80_90': {'trades': 0, 'wins': 0, 'total_pnl': 0},
            'adx_dma_90_100': {'trades': 0, 'wins': 0, 'total_pnl': 0},
            'camarilla_long': {'trades': 0, 'wins': 0, 'total_pnl': 0},
            'volume_breakout': {'trades': 0, 'wins': 0, 'total_pnl': 0}
        }

    def get_allocation(self) -> Dict[str, float]:
        """
        Allocate capital based on recent Sharpe ratios

        Returns:
            {'adx_dma_90_100': 0.40, 'camarilla_long': 0.30, ...}
        """
        # Calculate Sharpe for each strategy (rolling 30 days)
        sharpes = {}
        for strategy, stats in self.strategy_stats.items():
            if stats['trades'] >= 10:  # Need minimum data
                sharpes[strategy] = self.calculate_sharpe(strategy)
            else:
                sharpes[strategy] = 0.0

        # Rank by Sharpe
        ranked = sorted(sharpes.items(), key=lambda x: x[1], reverse=True)

        # Allocate: 40%, 30%, 20%, 10%
        allocations = {}
        weights = [0.40, 0.30, 0.20, 0.10]
        for i, (strategy, _) in enumerate(ranked[:4]):
            allocations[strategy] = weights[i]

        return allocations

    def update_after_trade(self, strategy: str, pnl: float):
        """
        After each trade closes, update strategy stats
        """
        stats = self.strategy_stats[strategy]
        stats['trades'] += 1
        if pnl > 0:
            stats['wins'] += 1
        stats['total_pnl'] += pnl
```

**Tests**:
- `tests/unit/test_strategy_selector.py`
  - Test allocation calculation
  - Test stat updates
  - Test Sharpe calculation

---

### Layer 3: Signal Generation

All scanners implement common interface:

```python
# agents/signals/base_scanner.py

class BaseScanner(ABC):
    """Abstract base class for all scanners"""

    @abstractmethod
    def scan(self, symbols: List[str], date: str) -> List[Signal]:
        """
        Scan for signals

        Returns:
            List of Signal objects
        """
        pass

@dataclass
class Signal:
    symbol: str
    date: str
    signal_type: str  # 'BUY' or 'SELL'
    strategy_name: str
    entry_price: float
    stop_loss: float
    target: float
    signal_strength: float  # 0-100
    metadata: Dict  # Strategy-specific data
```

**Concrete Scanners**:
1. `ADXDMAScanner` - Already implemented at `agents/trading/adx_dma_scanner.py`
2. `CamarillaScanner` - To be implemented
3. `VolumeBreakoutScanner` - To be implemented

---

### Layer 4: Position Sizing & Risk

#### Component 4.1: Kelly Position Sizer

```python
# agents/risk/kelly_position_sizer.py

class KellyPositionSizer:
    """
    Calculate position size using Kelly Criterion
    """

    def __init__(self, capital: float):
        self.capital = capital
        self.peak_capital = capital
        self.strategy_stats = {}  # Loaded from database

    def calculate_position_size(self, signal: Signal, sentiment: Dict) -> int:
        """
        Returns: Number of shares to buy

        Steps:
        1. Get Kelly fraction for this strategy
        2. Adjust for signal strength
        3. Adjust for sentiment
        4. Scale with profit level
        5. Cap at 20% of capital
        6. Ensure total risk < 2% of peak
        """
        # Step 1: Kelly fraction
        kelly = self.get_kelly_fraction(signal.strategy_name)

        # Step 2: Adjust for signal strength
        strength_multiplier = signal.signal_strength / 100.0
        adjusted_kelly = kelly * strength_multiplier

        # Step 3: Adjust for sentiment
        _, sentiment_multiplier = self.sentiment_adjuster(signal, sentiment)
        adjusted_kelly *= sentiment_multiplier

        # Step 4: Profit scaling
        profit_pct = (self.capital - 100000) / 100000 * 100
        if profit_pct > 20:
            scale = 1.5
        elif profit_pct > 10:
            scale = 1.2
        else:
            scale = 1.0
        adjusted_kelly *= scale

        # Step 5: Cap at 20%
        final_fraction = min(adjusted_kelly, 0.20)

        # Step 6: Calculate shares
        position_value = self.capital * final_fraction
        shares = int(position_value / signal.entry_price)

        # Step 7: Verify risk constraint
        risk_per_share = abs(signal.entry_price - signal.stop_loss)
        total_risk = shares * risk_per_share
        max_risk = self.peak_capital * 0.02

        if total_risk > max_risk:
            # Reduce shares
            shares = int(max_risk / risk_per_share)

        return shares

    def get_kelly_fraction(self, strategy: str) -> float:
        """
        Kelly = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
        Use Half-Kelly for safety
        """
        stats = self.strategy_stats.get(strategy, None)

        if not stats or stats['num_trades'] < 20:
            return 0.05  # Conservative default until enough data

        win_rate = stats['wins'] / stats['num_trades']
        loss_rate = 1 - win_rate
        avg_win = stats['total_win_pct'] / max(stats['wins'], 1)
        avg_loss = stats['total_loss_pct'] / max(stats['losses'], 1)

        kelly = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        half_kelly = kelly / 2

        return max(0.0, min(half_kelly, 0.20))  # Clamp between 0-20%
```

**Tests**:
- `tests/unit/test_kelly_sizer.py`
  - Test Kelly calculation with known inputs
  - Test profit scaling
  - Test risk constraint enforcement
  - Test 20% cap

---

#### Component 4.2: Risk Manager

```python
# agents/risk/risk_manager.py

class RiskManager:
    """
    Enforces hard risk limits
    """

    def __init__(self, max_drawdown_pct: float = 2.0):
        self.max_drawdown_pct = max_drawdown_pct
        self.peak_capital = None
        self.current_capital = None

    def can_open_position(self, position_value: float) -> Tuple[bool, str]:
        """
        Check if new position violates any limits

        Returns:
            (allowed, reason)
        """
        # Check 1: Drawdown limit
        current_dd = self.get_current_drawdown()
        if current_dd >= self.max_drawdown_pct * 0.9:  # 90% of limit
            return (False, f"Drawdown {current_dd:.2f}% too close to {self.max_drawdown_pct}% limit")

        # Check 2: Position size (20% max)
        if position_value > self.current_capital * 0.20:
            return (False, f"Position {position_value} exceeds 20% of capital {self.current_capital}")

        # Check 3: Total capital available
        if position_value > self.current_capital:
            return (False, "Insufficient capital")

        return (True, "OK")

    def get_current_drawdown(self) -> float:
        """
        Returns: Drawdown % from peak
        """
        if self.peak_capital is None:
            return 0.0

        return ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
```

**Tests**:
- `tests/unit/test_risk_manager.py`
  - Test drawdown calculation
  - Test position size limits
  - Test capital checks

---

### Layer 5: Execution & Cost

#### Component 5.1: Cost Calculator

```python
# agents/execution/cost_calculator.py

class IndianMarketCostCalculator:
    """
    Calculate ALL costs for Indian equity/F&O trades
    """

    def calculate_equity_costs(self, buy_value: float, sell_value: float) -> Dict:
        """
        Returns:
        {
            'buy_costs': float,
            'sell_costs': float,
            'total_costs': float,
            'cost_percentage': float,
            'breakdown': {...}
        }
        """
        # Brokerage
        buy_brokerage = max(buy_value * 0.0003, 20.0)
        sell_brokerage = max(sell_value * 0.0003, 20.0)

        # STT (only on sell)
        stt = sell_value * 0.001

        # Exchange charges
        exchange = (buy_value + sell_value) * 0.0000325

        # GST on brokerage
        gst = (buy_brokerage + sell_brokerage) * 0.18

        # SEBI charges
        sebi = (buy_value + sell_value) * 0.000001

        # Stamp duty (only on buy)
        stamp = buy_value * 0.00015

        total = buy_brokerage + sell_brokerage + stt + exchange + gst + sebi + stamp

        return {
            'total_costs': total,
            'cost_percentage': (total / buy_value) * 100,
            'breakdown': {
                'brokerage': buy_brokerage + sell_brokerage,
                'stt': stt,
                'exchange': exchange,
                'gst': gst,
                'sebi': sebi,
                'stamp': stamp
            }
        }
```

**Tests**:
- `tests/unit/test_cost_calculator.py`
  - Test with known trade values
  - Compare to manual calculation
  - Test edge cases (very small/large trades)

---

#### Component 5.2: Slippage Simulator

```python
# agents/execution/slippage_simulator.py

class SlippageSimulator:
    """
    Model realistic order fills
    """

    def __init__(self):
        self.base_slippage = {
            'large_cap': 0.0005,   # 0.05%
            'mid_cap': 0.0010,     # 0.10%
            'small_cap': 0.0020    # 0.20%
        }

    def calculate_fill_price(self, signal_price: float, order_side: str,
                             symbol: str, order_size: int,
                             avg_daily_volume: int, vix: float) -> float:
        """
        Returns: Actual fill price (worse than signal price)
        """
        category = self.categorize_stock(avg_daily_volume)
        base = self.base_slippage[category]

        # Adjust for order size
        order_pct = order_size / avg_daily_volume
        size_multiplier = 1.0 if order_pct < 0.01 else 1 + (order_pct * 10)

        # Adjust for volatility
        vol_multiplier = 1 + (vix / 20)

        total_slippage = base * size_multiplier * vol_multiplier

        if order_side == 'BUY':
            return signal_price * (1 + total_slippage)
        else:
            return signal_price * (1 - total_slippage)
```

**Tests**:
- `tests/unit/test_slippage_simulator.py`
  - Test slippage calculation
  - Test categorization
  - Test adjustments for size/volatility

---

### Layer 6: Backtesting & Validation

#### Component 6.1: Backtest Engine

```python
# agents/validation/backtest_engine.py

class BacktestEngine:
    """
    Historical validation with realistic execution
    """

    def __init__(self, starting_capital: float = 100000):
        self.capital = starting_capital
        self.peak = starting_capital

        self.cost_calc = IndianMarketCostCalculator()
        self.slippage_sim = SlippageSimulator()
        self.kelly_sizer = KellyPositionSizer(starting_capital)

        self.positions = []
        self.trades = []

    def run(self, start_date: str, end_date: str) -> Dict:
        """
        Run backtest from start to end

        Returns: Performance report
        """
        dates = pd.date_range(start_date, end_date, freq='D')

        for date in dates:
            if not self.is_trading_day(date):
                continue

            # Step 1: Generate signals
            signals = self.generate_signals(date)

            # Step 2: Filter by regime & sentiment
            filtered = self.filter_signals(signals, date)

            # Step 3: Size positions
            for signal in filtered:
                shares = self.kelly_sizer.calculate_position_size(signal)

                # Simulate entry
                fill_price = self.slippage_sim.calculate_fill_price(...)

                # Calculate costs
                buy_value = shares * fill_price
                costs = self.cost_calc.calculate_equity_costs(buy_value, buy_value)

                # Open position
                self.open_position(signal, shares, fill_price, costs)

            # Step 4: Check exits
            self.check_exits(date)

            # Step 5: Update capital
            self.update_portfolio(date)

        return self.generate_report()
```

**Tests**:
- `tests/integration/test_backtest_engine.py`
  - Test full backtest pipeline
  - Test with known signals (expected outcomes)
  - Test metrics calculation

---

### Layer 7: Monitoring

#### Component 7.1: Dashboard API

```python
# agents/monitoring/dashboard_api.py

from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.get("/portfolio/summary")
def get_portfolio_summary():
    """
    Returns:
    {
        'capital': float,
        'peak': float,
        'drawdown_pct': float,
        'open_positions': int,
        'today_pnl': float
    }
    """

@app.get("/portfolio/positions")
def get_open_positions():
    """
    Returns: List of open positions
    """

@app.get("/portfolio/trades")
def get_recent_trades(limit: int = 20):
    """
    Returns: Recent closed trades
    """

@app.websocket("/ws/live")
async def websocket_live_updates(websocket: WebSocket):
    """
    WebSocket for real-time updates
    """
```

**Tests**:
- `tests/integration/test_dashboard_api.py`
  - Test API endpoints
  - Test WebSocket connection
  - Test data accuracy

---

## Database Schema

### portfolio.db

```sql
-- Current portfolio state
CREATE TABLE portfolio_state (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    capital REAL NOT NULL,
    peak_capital REAL NOT NULL,
    drawdown_pct REAL NOT NULL,
    num_positions INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Open positions
CREATE TABLE positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    entry_date DATE NOT NULL,
    entry_price REAL NOT NULL,
    shares INTEGER NOT NULL,
    stop_loss REAL NOT NULL,
    target REAL NOT NULL,
    entry_costs REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### trades.db

```sql
-- Closed trades
CREATE TABLE trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL NOT NULL,
    shares INTEGER NOT NULL,
    entry_costs REAL NOT NULL,
    exit_costs REAL NOT NULL,
    total_costs REAL NOT NULL,
    gross_pnl REAL NOT NULL,
    net_pnl REAL NOT NULL,
    return_pct REAL NOT NULL,
    exit_reason TEXT NOT NULL,  -- 'stop_loss', 'target', 'time_exit'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_strategy ON trades(strategy);
CREATE INDEX idx_trades_date ON trades(exit_date);
```

### performance.db

```sql
-- Strategy performance tracking (for RL)
CREATE TABLE strategy_performance (
    strategy TEXT PRIMARY KEY,
    num_trades INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    total_win_pct REAL DEFAULT 0,
    total_loss_pct REAL DEFAULT 0,
    total_pnl REAL DEFAULT 0,
    sharpe_ratio_30d REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### regime_training.db

```sql
-- Historical regime labels for ML training
CREATE TABLE regime_labels (
    date DATE PRIMARY KEY,
    gap_pct REAL,
    range_pct REAL,
    volume_ratio REAL,
    vix REAL,
    nifty_adx REAL,
    sentiment REAL,
    day_type TEXT,
    best_strategy TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Contracts

### External API: Angel One

**Base URL**: `https://apiconnect.angelbroking.com`

**Authentication**:
```python
POST /rest/auth/angelbroking/user/v1/loginByPassword
{
    "clientcode": "S692691",
    "password": "...",
    "totp": "..."
}
```

**Get LTP**:
```python
POST /rest/secure/angelbroking/order/v1/getLtpData
{
    "exchange": "NSE",
    "tradingsymbol": "TCS-EQ",
    "symboltoken": "11536"
}
```

**Place Order**:
```python
POST /rest/secure/angelbroking/order/v1/placeOrder
{
    "variety": "ROBO",  # Bracket order
    "tradingsymbol": "TCS-EQ",
    "quantity": "100",
    "squareoff": "50",  # Profit points
    "stoploss": "25",   # Loss points
    ...
}
```

---

### External API: Trium Finance

**Base URL**: To be confirmed from Trium project

**Get News**:
```python
GET /api/news/stock/{symbol}?lookback_hours=24&limit=10
Headers: {
    "Authorization": "Bearer {api_key}"
}
```

**Response**:
```json
{
    "articles": [
        {
            "title": "...",
            "summary": "...",
            "published_at": "2025-11-19T10:30:00Z",
            "source": "Economic Times",
            "url": "..."
        }
    ]
}
```

---

## Deployment Architecture

### Local Development
```
MacOS (your laptop)
├── Python 3.9+
├── SQLite databases
├── FastAPI (port 8003)
├── Telegram bot
└── Scheduled tasks (cron)
```

### Production (Future)
```
AWS LightSail or EC2
├── Same stack as local
├── Systemd services
├── Health monitoring
├── Backup to S3
└── Alerts to SNS
```

**For V1**: Run locally, deploy to cloud only if needed for uptime

---

## Technology Stack

### Core
- **Language**: Python 3.9+
- **ML**: scikit-learn, XGBoost, pandas, numpy
- **Data**: SQLite (V1), PostgreSQL (V2 if needed)
- **API**: FastAPI
- **Testing**: pytest, pytest-cov
- **Code Quality**: black, flake8, mypy

### External Services
- **Broker**: Angel One SmartAPI
- **News**: Trium Finance API
- **LLM**: OpenAI GPT-4 or Anthropic Claude
- **Notifications**: Telegram Bot API

### Development Tools
- **Version Control**: Git
- **CI/CD**: GitHub Actions (if using GitHub)
- **Monitoring**: Prometheus (optional)

---

## Next Steps

After architecture approval:
1. Create TEST_STRATEGY.md (TDD approach)
2. Create FX documents (detailed specs for each component)
3. Create STORY documents (user stories)
4. Create SHORT tasks (implementation checklist)
5. Begin TDD implementation

---

**END OF ARCHITECTURE**
