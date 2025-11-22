"""
Tests for Historical Data Backfill Utility (SHORT-015)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import pandas as pd


class TestHistoricalBackfillUtility:
    """Test historical data backfill"""

    @pytest.fixture
    def date_range(self):
        """Sample date range"""
        return datetime(2024, 1, 1), datetime(2024, 1, 31)

    @pytest.fixture
    def mock_data_source(self):
        """Mock data source"""
        source = Mock()
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        data = pd.DataFrame({
            'open': [100.0] * len(dates),
            'high': [105.0] * len(dates),
            'low': [95.0] * len(dates),
            'close': [102.0] * len(dates),
            'volume': [1000000] * len(dates)
        }, index=dates)
        source.fetch_ohlcv.return_value = data
        return source

    @pytest.fixture
    def mock_cache(self):
        """Mock data cache"""
        cache = Mock()
        cache.get.return_value = None
        cache.set.return_value = True
        return cache

    def test_backfill_full_range(self, date_range, mock_data_source, mock_cache):
        """TC-1: Backfill complete date range"""
        from src.data.historical_backfill import HistoricalBackfillUtility

        backfiller = HistoricalBackfillUtility(
            data_source=mock_data_source,
            cache=mock_cache
        )

        start_date, end_date = date_range
        result = backfiller.backfill(
            symbol="TCS",
            start_date=start_date,
            end_date=end_date
        )

        # Should fetch and cache data
        assert result['success'] is True
        assert result['records_added'] > 0
        assert mock_data_source.fetch_ohlcv.called
        assert mock_cache.set.called

    def test_incremental_backfill(self, date_range, mock_data_source, mock_cache):
        """TC-2: Incremental backfill only fetches gaps"""
        from src.data.historical_backfill import HistoricalBackfillUtility

        # Partial existing data (first 15 days)
        existing_dates = pd.date_range(start='2024-01-01', end='2024-01-15', freq='D')
        existing_data = pd.DataFrame({
            'open': [100.0] * len(existing_dates),
            'high': [105.0] * len(existing_dates),
            'low': [95.0] * len(existing_dates),
            'close': [102.0] * len(existing_dates),
            'volume': [1000000] * len(existing_dates)
        }, index=existing_dates)

        mock_cache.get.return_value = existing_data

        backfiller = HistoricalBackfillUtility(
            data_source=mock_data_source,
            cache=mock_cache
        )

        start_date, end_date = date_range
        result = backfiller.backfill(
            symbol="TCS",
            start_date=start_date,
            end_date=end_date,
            incremental=True
        )

        # Should only fetch missing dates
        assert result['success'] is True
        assert result['existing_records'] > 0
        assert result['records_added'] < 31  # Not all records

    def test_skip_market_holidays(self, mock_data_source, mock_cache):
        """TC-3: Skip market holidays and weekends"""
        from src.data.historical_backfill import HistoricalBackfillUtility

        # Define holidays
        holidays = [datetime(2024, 1, 26)]  # Republic Day

        backfiller = HistoricalBackfillUtility(
            data_source=mock_data_source,
            cache=mock_cache,
            market_holidays=holidays
        )

        result = backfiller.backfill(
            symbol="TCS",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )

        # Should skip holidays
        assert result['success'] is True
        assert result.get('skipped_dates') is not None

    def test_batch_backfill(self, date_range, mock_data_source, mock_cache):
        """Test backfilling multiple symbols"""
        from src.data.historical_backfill import HistoricalBackfillUtility

        backfiller = HistoricalBackfillUtility(
            data_source=mock_data_source,
            cache=mock_cache
        )

        symbols = ["TCS", "INFY", "WIPRO"]
        start_date, end_date = date_range

        results = backfiller.backfill_batch(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )

        # All symbols should be processed
        assert len(results) == len(symbols)
        for symbol in symbols:
            assert symbol in results
            assert 'success' in results[symbol]

    def test_track_progress(self, date_range, mock_data_source, mock_cache):
        """Test progress tracking during backfill"""
        from src.data.historical_backfill import HistoricalBackfillUtility

        progress_updates = []

        def progress_callback(symbol, current, total, status):
            progress_updates.append({
                'symbol': symbol,
                'current': current,
                'total': total,
                'status': status
            })

        backfiller = HistoricalBackfillUtility(
            data_source=mock_data_source,
            cache=mock_cache,
            progress_callback=progress_callback
        )

        start_date, end_date = date_range
        backfiller.backfill("TCS", start_date, end_date)

        # Should receive progress updates
        assert len(progress_updates) > 0

    def test_handle_backfill_errors(self, date_range, mock_cache):
        """Test error handling during backfill"""
        from src.data.historical_backfill import HistoricalBackfillUtility

        # Data source that fails
        failing_source = Mock()
        failing_source.fetch_ohlcv.side_effect = Exception("Network error")

        backfiller = HistoricalBackfillUtility(
            data_source=failing_source,
            cache=mock_cache
        )

        start_date, end_date = date_range
        result = backfiller.backfill("TCS", start_date, end_date)

        # Should handle error gracefully
        assert result['success'] is False
        assert 'error' in result

    def test_detect_gaps_before_backfill(self, date_range, mock_data_source, mock_cache):
        """Test gap detection before backfilling"""
        from src.data.historical_backfill import HistoricalBackfillUtility

        # Sparse existing data
        sparse_dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='7D')
        sparse_data = pd.DataFrame({
            'open': [100.0] * len(sparse_dates),
            'high': [105.0] * len(sparse_dates),
            'low': [95.0] * len(sparse_dates),
            'close': [102.0] * len(sparse_dates),
            'volume': [1000000] * len(sparse_dates)
        }, index=sparse_dates)

        mock_cache.get.return_value = sparse_data

        backfiller = HistoricalBackfillUtility(
            data_source=mock_data_source,
            cache=mock_cache
        )

        start_date, end_date = date_range
        gaps = backfiller.detect_gaps("TCS", start_date, end_date)

        # Should identify gaps
        assert len(gaps) > 0
        assert 'missing_dates' in gaps

    def test_dry_run_mode(self, date_range, mock_data_source, mock_cache):
        """Test dry run mode (no data persistence)"""
        from src.data.historical_backfill import HistoricalBackfillUtility

        backfiller = HistoricalBackfillUtility(
            data_source=mock_data_source,
            cache=mock_cache
        )

        start_date, end_date = date_range
        result = backfiller.backfill(
            "TCS",
            start_date,
            end_date,
            dry_run=True
        )

        # Should not persist to cache
        assert result['success'] is True
        assert not mock_cache.set.called
