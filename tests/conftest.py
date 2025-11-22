"""
Pytest configuration and shared fixtures

This file is automatically loaded by pytest and provides:
- Shared fixtures available to all tests
- Test configuration
- Custom markers
- Test utilities
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, date
import logging

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (multi-component)"
    )
    config.addinivalue_line(
        "markers", "system: System tests (end-to-end)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (>1 second)"
    )
    config.addinivalue_line(
        "markers", "critical: Critical component tests (must have 100% coverage)"
    )


# ============================================================================
# SHARED FIXTURES - CONSTANTS
# ============================================================================

@pytest.fixture
def initial_capital():
    """Initial capital for testing"""
    return 100000  # ₹1,00,000


@pytest.fixture
def max_drawdown_pct():
    """Max drawdown percentage"""
    return 0.02  # 2%


@pytest.fixture
def equity_position_cap():
    """Max position as % of capital (equity)"""
    return 0.20  # 20%


@pytest.fixture
def fno_position_cap():
    """Max position as % of capital (F&O)"""
    return 0.04  # 4%


# ============================================================================
# SHARED FIXTURES - SAMPLE DATA
# ============================================================================

@pytest.fixture
def sample_signal():
    """Sample trading signal"""
    return {
        "symbol": "RELIANCE.NS",
        "strategy": "ADX_DMA",
        "side": "BUY",
        "entry_price": 2500.0,
        "stop_loss": 2425.0,
        "target": 2625.0,
        "signal_strength": 0.85,
        "timestamp": datetime(2025, 11, 19, 9, 30, 0),
    }


@pytest.fixture
def sample_strategy_stats():
    """Sample strategy performance stats"""
    return {
        "strategy_name": "ADX_DMA",
        "total_trades": 100,
        "wins": 55,
        "losses": 45,
        "win_rate": 0.55,
        "avg_win_pct": 0.05,
        "avg_loss_pct": 0.03,
        "last_updated": "2025-11-19",
    }


@pytest.fixture
def sample_trade():
    """Sample trade data"""
    return {
        "symbol": "RELIANCE.NS",
        "entry_date": date(2025, 11, 19),
        "entry_price": 2500.0,
        "exit_date": date(2025, 11, 22),
        "exit_price": 2580.0,
        "shares": 40,
        "gross_pnl": 3200.0,  # (2580 - 2500) * 40
        "costs": 175.0,
        "net_pnl": 3025.0,
        "exit_reason": "TARGET",
    }


# ============================================================================
# SHARED FIXTURES - DATABASE
# ============================================================================

@pytest.fixture
def temp_db_path(tmp_path):
    """Create temporary database for testing"""
    db_path = tmp_path / "test_trades.db"
    return str(db_path)


@pytest.fixture
def sample_trades_db(temp_db_path):
    """Create sample trades database with test data"""
    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Create trades table
    cursor.execute("""
        CREATE TABLE trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            strategy TEXT NOT NULL,
            side TEXT CHECK(side IN ('BUY', 'SELL')),
            entry_date DATE NOT NULL,
            entry_price REAL NOT NULL,
            shares INTEGER NOT NULL,
            stop_loss REAL NOT NULL,
            target REAL,
            exit_date DATE,
            exit_price REAL,
            exit_reason TEXT,
            gross_pnl REAL,
            costs REAL,
            net_pnl REAL,
            return_pct REAL,
            kelly_fraction REAL,
            position_value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Insert 100 sample trades (55 wins, 45 losses)
    for i in range(100):
        is_win = i < 55
        entry_price = 2500
        exit_price = 2625 if is_win else 2425  # +5% or -3%
        gross_pnl = (exit_price - entry_price) * 40
        costs = 175
        net_pnl = gross_pnl - costs
        return_pct = (exit_price - entry_price) / entry_price

        cursor.execute("""
            INSERT INTO trades (
                symbol, strategy, side, entry_date, entry_price,
                shares, stop_loss, target, exit_date, exit_price,
                exit_reason, gross_pnl, costs, net_pnl, return_pct,
                kelly_fraction, position_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"STOCK_{i % 10}",
            "ADX_DMA",
            "BUY",
            f"2024-{(i % 12) + 1:02d}-01",
            entry_price,
            40,
            2425,
            2625,
            f"2024-{(i % 12) + 1:02d}-05",
            exit_price,
            "TARGET" if is_win else "STOP_LOSS",
            gross_pnl,
            costs,
            net_pnl,
            return_pct,
            0.14,
            100000,
        ))

    conn.commit()
    conn.close()

    return temp_db_path


# ============================================================================
# SHARED FIXTURES - MOCKING
# ============================================================================

@pytest.fixture
def mock_market_data():
    """Mock market data (OHLCV)"""
    import pandas as pd
    import numpy as np

    dates = pd.date_range(start='2024-01-01', periods=250, freq='D')

    data = pd.DataFrame({
        'date': dates,
        'open': np.random.uniform(2400, 2600, 250),
        'high': np.random.uniform(2500, 2700, 250),
        'low': np.random.uniform(2300, 2500, 250),
        'close': np.random.uniform(2400, 2600, 250),
        'volume': np.random.randint(1000000, 5000000, 250),
    })

    data.set_index('date', inplace=True)
    return data


@pytest.fixture
def mock_angel_one_client(mocker):
    """Mock Angel One API client"""
    mock_client = mocker.Mock()

    # Mock methods
    mock_client.get_current_price.return_value = 2500.0
    mock_client.place_order.return_value = {
        'status': 'success',
        'orderid': '12345',
        'message': 'Order placed successfully'
    }
    mock_client.get_order_status.return_value = {
        'status': 'complete',
        'averageprice': 2501.50,
    }

    return mock_client


@pytest.fixture
def mock_trium_finance_api(mocker):
    """Mock Trium Finance news API"""
    mock_api = mocker.Mock()

    mock_api.get.return_value.json.return_value = {
        'articles': [
            {
                'article_id': '1',
                'title': 'Positive earnings announcement',
                'description': 'Company beats estimates',
                'source': 'Economic Times',
                'published_at': '2025-11-19T08:00:00',
                'url': 'http://example.com',
                'symbols': ['RELIANCE'],
            }
        ]
    }

    return mock_api


@pytest.fixture
def mock_llm_sentiment(mocker):
    """Mock LLM sentiment scoring"""
    mock_llm = mocker.Mock()
    mock_llm.return_value = 0.7  # Positive sentiment
    return mock_llm


# ============================================================================
# SHARED UTILITIES
# ============================================================================

@pytest.fixture
def assert_within_range():
    """Utility to assert value is within range"""
    def _assert_within_range(value, min_val, max_val, msg=None):
        assert min_val <= value <= max_val, (
            msg or f"{value} not in range [{min_val}, {max_val}]"
        )
    return _assert_within_range


@pytest.fixture
def assert_percent_diff():
    """Utility to assert percentage difference"""
    def _assert_percent_diff(value1, value2, max_diff_pct, msg=None):
        diff = abs(value1 - value2)
        diff_pct = diff / value1 if value1 != 0 else 0
        assert diff_pct <= max_diff_pct, (
            msg or f"Difference {diff_pct:.2%} exceeds {max_diff_pct:.2%}"
        )
    return _assert_percent_diff


# ============================================================================
# PERFORMANCE TESTING FIXTURES
# ============================================================================

@pytest.fixture
def benchmark_timer():
    """Timer for benchmarking performance"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None

        def assert_under(self, max_ms, msg=None):
            assert self.elapsed_ms < max_ms, (
                msg or f"Elapsed {self.elapsed_ms:.2f}ms exceeds {max_ms}ms"
            )

    return Timer()


# ============================================================================
# AUTOUSE FIXTURES (Run automatically)
# ============================================================================

@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration for each test"""
    # Clear all handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Reconfigure
    logging.basicConfig(
        level=logging.WARNING,  # Less verbose during tests
        format='%(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture(autouse=True)
def suppress_warnings():
    """Suppress common warnings during tests"""
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
