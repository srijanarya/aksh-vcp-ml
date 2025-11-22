"""
Edge case tests for Batch Symbol Data Loader

Coverage for error paths and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import pandas as pd


class TestBatchSymbolDataLoaderEdgeCases:
    """Edge case tests for batch data loader"""

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

    def test_retry_exhaustion(self, date_range):
        """Test when all retry attempts are exhausted"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        mock_source = Mock()
        mock_source.fetch_ohlcv.side_effect = ConnectionError("Persistent failure")

        loader = BatchSymbolDataLoader(
            data_source=mock_source,
            max_workers=1,
            max_retries=2
        )

        start_date, end_date = date_range
        results = loader.load_batch(["FAIL"], start_date, end_date)

        # Symbol should fail after all retries
        assert "FAIL" in results['failed']
        assert "FAIL" in results['errors']

        # Should have attempted max_retries times
        assert mock_source.fetch_ohlcv.call_count == 2

    def test_none_data_handling(self, date_range):
        """Test handling when data source returns None"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        mock_source = Mock()
        mock_source.fetch_ohlcv.return_value = None

        loader = BatchSymbolDataLoader(data_source=mock_source)

        start_date, end_date = date_range
        results = loader.load_batch(["NULL"], start_date, end_date)

        # None data should fail
        assert "NULL" in results['failed']
        assert "Empty data returned" in results['errors'].get("NULL", "")

    def test_empty_dataframe_handling(self, date_range):
        """Test handling when data source returns empty DataFrame"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        mock_source = Mock()
        mock_source.fetch_ohlcv.return_value = pd.DataFrame()

        loader = BatchSymbolDataLoader(data_source=mock_source)

        start_date, end_date = date_range
        results = loader.load_batch(["EMPTY"], start_date, end_date)

        # Empty DataFrame should fail
        assert "EMPTY" in results['failed']

    def test_progress_callback_on_failure(self, date_range):
        """Test progress callback receives failure status"""
        from src.data.batch_symbol_data_loader import BatchSymbolDataLoader

        mock_source = Mock()
        mock_source.fetch_ohlcv.side_effect = ValueError("Error")

        progress_updates = []

        def progress_callback(symbol, status, current, total):
            progress_updates.append({'symbol': symbol, 'status': status})

        loader = BatchSymbolDataLoader(
            data_source=mock_source,
            progress_callback=progress_callback,
            max_retries=1
        )

        start_date, end_date = date_range
        loader.load_batch(["FAIL"], start_date, end_date)

        # Should have received failure status
        failed_updates = [u for u in progress_updates if u['status'] == 'failed']
        assert len(failed_updates) > 0
        assert failed_updates[0]['symbol'] == "FAIL"
