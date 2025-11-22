"""
Tests for Batch Symbol Data Loader (SHORT-013)

TDD approach:
1. Write tests first
2. Run tests (they should FAIL)
3. Implement code to pass tests
4. Refactor
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import time


class TestBatchSymbolDataLoader:
    """Test batch data loading for multiple symbols"""

    @pytest.fixture
    def sample_symbols(self):
        """Sample list of symbols"""
        return ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"]

    @pytest.fixture
    def date_range(self):
        """Sample date range"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return start_date, end_date

    @pytest.fixture
    def mock_ohlcv_data(self):
        """Mock OHLCV data"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=30),
                             end=datetime.now(), freq='D')
        return pd.DataFrame({
            'open': [100.0] * len(dates),
            'high': [105.0] * len(dates),
            'low': [95.0] * len(dates),
            'close': [102.0] * len(dates),
            'volume': [1000000] * len(dates)
        }, index=dates)

    def test_batch_load_success(self, sample_symbols, date_range, mock_ohlcv_data):
        """TC-1: Load multiple symbols successfully"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        # Mock data source
        mock_source = Mock()
        mock_source.fetch_ohlcv.return_value = mock_ohlcv_data

        loader = BatchSymbolDataLoader(data_source=mock_source, max_workers=3)

        start_date, end_date = date_range
        results = loader.load_batch(sample_symbols, start_date, end_date)

        # All symbols should succeed
        assert len(results['success']) == len(sample_symbols)
        assert len(results['failed']) == 0

        # Each symbol should have data
        for symbol in sample_symbols:
            assert symbol in results['data']
            assert isinstance(results['data'][symbol], pd.DataFrame)
            assert len(results['data'][symbol]) > 0

    def test_batch_load_partial_failure(self, date_range, mock_ohlcv_data):
        """TC-2: Handle partial failures gracefully"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        # Mock data source with selective failures
        mock_source = Mock()
        def fetch_side_effect(symbol, start, end, **kwargs):
            if symbol == "INVALID":
                raise ValueError("Invalid symbol")
            return mock_ohlcv_data

        mock_source.fetch_ohlcv.side_effect = fetch_side_effect

        loader = BatchSymbolDataLoader(data_source=mock_source, max_workers=2)

        symbols = ["TCS", "INVALID", "INFY"]
        start_date, end_date = date_range
        results = loader.load_batch(symbols, start_date, end_date)

        # Valid symbols succeed
        assert "TCS" in results['success']
        assert "INFY" in results['success']

        # Invalid symbol fails
        assert "INVALID" in results['failed']
        assert "INVALID" in results['errors']

        # Valid symbols have data
        assert "TCS" in results['data']
        assert "INFY" in results['data']
        assert "INVALID" not in results['data']

    def test_batch_load_respects_rate_limit(self, sample_symbols, date_range, mock_ohlcv_data):
        """TC-3: Respect rate limits across concurrent workers"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        # Mock data source with timing tracking
        mock_source = Mock()
        call_times = []

        def fetch_with_timing(symbol, start, end, **kwargs):
            call_times.append(time.time())
            return mock_ohlcv_data

        mock_source.fetch_ohlcv.side_effect = fetch_with_timing

        # Create rate limiter mock
        mock_rate_limiter = Mock()
        mock_rate_limiter.acquire.return_value = None

        loader = BatchSymbolDataLoader(
            data_source=mock_source,
            rate_limiter=mock_rate_limiter,
            max_workers=3
        )

        start_date, end_date = date_range
        results = loader.load_batch(sample_symbols, start_date, end_date)

        # Rate limiter should be called for each symbol
        assert mock_rate_limiter.acquire.call_count == len(sample_symbols)

        # All symbols should succeed
        assert len(results['success']) == len(sample_symbols)

    def test_batch_load_retry_logic(self, date_range, mock_ohlcv_data):
        """TC-4: Retry failed symbols"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        # Mock data source that fails first attempt, succeeds second
        mock_source = Mock()
        attempt_count = {}

        def fetch_with_retry(symbol, start, end, **kwargs):
            if symbol not in attempt_count:
                attempt_count[symbol] = 0
            attempt_count[symbol] += 1

            # Fail first attempt for specific symbol
            if symbol == "FLAKY" and attempt_count[symbol] == 1:
                raise ConnectionError("Temporary failure")

            return mock_ohlcv_data

        mock_source.fetch_ohlcv.side_effect = fetch_with_retry

        loader = BatchSymbolDataLoader(
            data_source=mock_source,
            max_workers=2,
            max_retries=2
        )

        symbols = ["TCS", "FLAKY", "INFY"]
        start_date, end_date = date_range
        results = loader.load_batch(symbols, start_date, end_date)

        # All symbols should succeed (FLAKY succeeds on retry)
        assert len(results['success']) == 3
        assert "FLAKY" in results['success']

        # FLAKY should have been attempted twice
        assert attempt_count["FLAKY"] == 2

    def test_batch_load_progress_tracking(self, sample_symbols, date_range, mock_ohlcv_data):
        """Test progress tracking during batch load"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        mock_source = Mock()
        mock_source.fetch_ohlcv.return_value = mock_ohlcv_data

        progress_updates = []

        def progress_callback(symbol, status, current, total):
            progress_updates.append({
                'symbol': symbol,
                'status': status,
                'current': current,
                'total': total
            })

        loader = BatchSymbolDataLoader(
            data_source=mock_source,
            max_workers=2,
            progress_callback=progress_callback
        )

        start_date, end_date = date_range
        results = loader.load_batch(sample_symbols, start_date, end_date)

        # Should have progress updates
        assert len(progress_updates) > 0

        # Should have completion updates for all symbols
        completed = [u for u in progress_updates if u['status'] == 'completed']
        assert len(completed) == len(sample_symbols)

    def test_batch_load_with_validation(self, sample_symbols, date_range):
        """Test batch load validates data before returning"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        # Mock data with validation
        valid_data = pd.DataFrame({
            'open': [100.0] * 10,
            'high': [105.0] * 10,
            'low': [95.0] * 10,
            'close': [102.0] * 10,
            'volume': [1000000] * 10
        })

        invalid_data = pd.DataFrame({
            'open': [100.0] * 10,
            'high': [90.0] * 10,  # Invalid: high < low
            'low': [95.0] * 10,
            'close': [102.0] * 10,
            'volume': [1000000] * 10
        })

        mock_source = Mock()
        def fetch_with_validation(symbol, start, end, **kwargs):
            if symbol == "INVALID_DATA":
                return invalid_data
            return valid_data

        mock_source.fetch_ohlcv.side_effect = fetch_with_validation

        mock_validator = Mock()
        mock_validator.validate.side_effect = lambda df: len(df) if df['high'].iloc[0] > df['low'].iloc[0] else 0

        loader = BatchSymbolDataLoader(
            data_source=mock_source,
            validator=mock_validator,
            max_workers=2
        )

        symbols = ["TCS", "INVALID_DATA", "INFY"]
        start_date, end_date = date_range
        results = loader.load_batch(symbols, start_date, end_date)

        # Valid data passes
        assert "TCS" in results['success']
        assert "INFY" in results['success']

        # Invalid data fails validation
        assert "INVALID_DATA" in results['failed']

    def test_batch_load_empty_symbol_list(self, date_range):
        """Test batch load with empty symbol list"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        mock_source = Mock()
        loader = BatchSymbolDataLoader(data_source=mock_source)

        start_date, end_date = date_range
        results = loader.load_batch([], start_date, end_date)

        assert len(results['success']) == 0
        assert len(results['failed']) == 0
        assert len(results['data']) == 0

    def test_batch_load_max_workers_limit(self, sample_symbols, date_range, mock_ohlcv_data):
        """Test concurrent execution respects max workers"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        mock_source = Mock()
        active_workers = {'count': 0, 'max_seen': 0}

        def fetch_with_worker_tracking(symbol, start, end, **kwargs):
            active_workers['count'] += 1
            active_workers['max_seen'] = max(active_workers['max_seen'], active_workers['count'])
            time.sleep(0.1)  # Simulate work
            active_workers['count'] -= 1
            return mock_ohlcv_data

        mock_source.fetch_ohlcv.side_effect = fetch_with_worker_tracking

        max_workers = 2
        loader = BatchSymbolDataLoader(
            data_source=mock_source,
            max_workers=max_workers
        )

        start_date, end_date = date_range
        results = loader.load_batch(sample_symbols, start_date, end_date)

        # Should not exceed max workers
        assert active_workers['max_seen'] <= max_workers

        # All symbols should complete
        assert len(results['success']) == len(sample_symbols)
