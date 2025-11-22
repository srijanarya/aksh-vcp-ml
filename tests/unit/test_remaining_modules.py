"""
Comprehensive tests for remaining modules
(Regime, Sentiment, Paper Trading, Order Executor)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime


# Regime Detection Tests
def test_regime_detector():
    """Test regime detection"""
    from src.regime.regime_detector import RegimeDetector, MarketRegime

    detector = RegimeDetector()

    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    df = pd.DataFrame({
        'close': 100 + np.arange(50),
        'high': 105 + np.arange(50),
        'low': 95 + np.arange(50)
    }, index=dates)

    adx = pd.Series(30.0, index=dates)  # Trending

    regime = detector.detect_regime(df, adx)
    assert regime in [MarketRegime.TRENDING, MarketRegime.RANGING, MarketRegime.VOLATILE]


def test_strategy_selection():
    """Test strategy selection based on regime"""
    from src.regime.regime_detector import RegimeDetector, MarketRegime

    detector = RegimeDetector()

    strategy = detector.select_strategy(MarketRegime.TRENDING)
    assert strategy == "trend_following"

    strategy = detector.select_strategy(MarketRegime.RANGING)
    assert strategy == "mean_reversion"


# Sentiment Analysis Tests
def test_sentiment_analyzer():
    """Test sentiment analysis"""
    from src.sentiment.sentiment_analyzer import SentimentAnalyzer, SentimentScore

    analyzer = SentimentAnalyzer()

    # Test sentiment scoring
    bullish_text = "Stock gains 10% on strong earnings"
    score = analyzer.score_sentiment(bullish_text)
    assert score == SentimentScore.BULLISH

    bearish_text = "Company reports losses"
    score = analyzer.score_sentiment(bearish_text)
    assert score == SentimentScore.BEARISH


def test_sentiment_aggregation():
    """Test sentiment aggregation"""
    from src.sentiment.sentiment_analyzer import SentimentAnalyzer

    analyzer = SentimentAnalyzer()

    result = analyzer.aggregate_sentiment("TCS")

    assert 'overall' in result
    assert 'bullish_count' in result
    assert 'bearish_count' in result
    assert 'total_articles' in result


# Paper Trading Tests
def test_virtual_account_buy():
    """Test virtual account buy order"""
    from src.paper_trading.virtual_account import VirtualAccount

    account = VirtualAccount(initial_capital=100000)

    success = account.buy("TCS", quantity=100, price=1000)
    assert success is True
    assert account.cash == 0  # 100000 - 100*1000
    assert "TCS" in account.positions


def test_virtual_account_sell():
    """Test virtual account sell order"""
    from src.paper_trading.virtual_account import VirtualAccount

    account = VirtualAccount(initial_capital=100000)

    account.buy("TCS", quantity=100, price=1000)
    account.update_prices({"TCS": 1100})

    success = account.sell("TCS", price=1100)
    assert success is True
    assert "TCS" not in account.positions
    assert account.cash > 100000  # Profit made


def test_virtual_account_performance():
    """Test performance tracking"""
    from src.paper_trading.virtual_account import VirtualAccount

    account = VirtualAccount(initial_capital=100000)

    account.buy("TCS", quantity=100, price=1000)
    account.update_prices({"TCS": 1100})

    perf = account.get_performance()

    assert perf['initial_capital'] == 100000
    assert perf['current_equity'] > 100000  # Profit
    assert perf['total_return_pct'] > 0


# Order Executor Tests
def test_order_validation():
    """Test order validation"""
    from src.order_executor.order_executor import OrderExecutor, OrderType

    executor = OrderExecutor()

    # Valid order
    valid = executor.validate_order("TCS", 100, 1000, OrderType.LIMIT)
    assert valid is True

    # Invalid quantity
    invalid = executor.validate_order("TCS", 0, 1000, OrderType.LIMIT)
    assert invalid is False


def test_place_order():
    """Test order placement"""
    from src.order_executor.order_executor import OrderExecutor, OrderType

    executor = OrderExecutor(kill_switch_enabled=False)

    order_id = executor.place_order("TCS", 100, 1000, OrderType.LIMIT)
    assert order_id is not None
    assert order_id in executor.orders


def test_cancel_order():
    """Test order cancellation"""
    from src.order_executor.order_executor import OrderExecutor, OrderType, OrderStatus

    executor = OrderExecutor(kill_switch_enabled=False)

    order_id = executor.place_order("TCS", 100, 1000, OrderType.LIMIT)
    success = executor.cancel_order(order_id)

    assert success is True
    assert executor.get_order_status(order_id) == OrderStatus.CANCELLED


def test_kill_switch():
    """Test kill switch activation"""
    from src.order_executor.order_executor import OrderExecutor, OrderType

    executor = OrderExecutor(kill_switch_enabled=True)

    # Activate kill switch
    executor.activate_kill_switch("Test")
    assert executor.kill_switch_enabled is True
