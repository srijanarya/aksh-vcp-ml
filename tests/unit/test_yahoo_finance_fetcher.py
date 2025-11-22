"""
Unit tests for Yahoo Finance Data Fetcher

Following TDD approach:
1. RED: Write failing tests first
2. GREEN: Make tests pass
3. REFACTOR: Improve code

Test Coverage Target: 100%
"""

import pytest
from datetime import datetime
import pandas as pd


class TestYahooFetcherInitialization:
    """Test YahooFinanceFetcher initialization"""

    def test_fetcher_initialization(self):
        """Test fetcher initializes with defaults"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        fetcher = YahooFinanceFetcher()

        assert fetcher.cache_dir is not None
        assert fetcher.cache_ttl == 3600

    def test_fetcher_with_custom_cache(self, tmp_path):
        """Test fetcher with custom cache settings"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        custom_cache = str(tmp_path / "yahoo_cache")
        fetcher = YahooFinanceFetcher(
            cache_dir=custom_cache,
            cache_ttl=7200
        )

        assert fetcher.cache_dir == custom_cache
        assert fetcher.cache_ttl == 7200


class TestSymbolConversion:
    """Test symbol conversion for Yahoo Finance"""

    def test_nse_symbol_conversion(self):
        """Test NSE symbol gets .NS suffix"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        fetcher = YahooFinanceFetcher()
        yahoo_symbol = fetcher._convert_symbol("RELIANCE", "NSE")

        assert yahoo_symbol == "RELIANCE.NS"

    def test_bse_symbol_conversion(self):
        """Test BSE symbol gets .BO suffix"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        fetcher = YahooFinanceFetcher()
        yahoo_symbol = fetcher._convert_symbol("RELIANCE", "BSE")

        assert yahoo_symbol == "RELIANCE.BO"

    def test_invalid_exchange_raises_error(self):
        """Test invalid exchange raises error"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        fetcher = YahooFinanceFetcher()

        with pytest.raises(ValueError, match="Invalid exchange"):
            fetcher._convert_symbol("RELIANCE", "INVALID")


class TestOHLCVFetching:
    """Test OHLCV data fetching from Yahoo Finance"""

    def test_fetch_daily_data_success(self, mocker):
        """Test fetch daily OHLCV data"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        # Mock yfinance
        mock_ticker = mocker.Mock()
        mock_hist = pd.DataFrame({
            'Open': [2500.0, 2540.0],
            'High': [2550.0, 2580.0],
            'Low': [2480.0, 2520.0],
            'Close': [2540.0, 2570.0],
            'Volume': [1000000, 1200000]
        }, index=pd.DatetimeIndex(['2023-01-02', '2023-01-03']))

        mock_ticker.history.return_value = mock_hist
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)
        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31),
            interval="1d"
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']

    def test_fetch_intraday_data_success(self, mocker):
        """Test fetch intraday data"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        mock_ticker = mocker.Mock()
        mock_hist = pd.DataFrame({
            'Open': [2500.0],
            'High': [2510.0],
            'Low': [2495.0],
            'Close': [2505.0],
            'Volume': [100000]
        }, index=pd.DatetimeIndex(['2023-01-02 09:15:00']))

        mock_ticker.history.return_value = mock_hist
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)
        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 2, 9, 15),
            to_date=datetime(2023, 1, 2, 15, 30),
            interval="5m"
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_fetch_invalid_symbol_returns_empty(self, mocker):
        """Test invalid symbol returns empty DataFrame"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        mock_ticker = mocker.Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # Empty
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)
        df = fetcher.fetch_ohlcv(
            symbol="INVALID",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_fetch_with_date_range(self, mocker):
        """Test fetch respects date range"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        mock_ticker = mocker.Mock()
        mock_hist = pd.DataFrame({
            'Open': [2500.0],
            'High': [2550.0],
            'Low': [2480.0],
            'Close': [2540.0],
            'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2023-01-02']))

        mock_ticker.history.return_value = mock_hist
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)

        from_date = datetime(2023, 1, 1)
        to_date = datetime(2023, 1, 31)

        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=from_date,
            to_date=to_date
        )

        # Verify yfinance was called with correct dates
        mock_ticker.history.assert_called_once()
        call_kwargs = mock_ticker.history.call_args.kwargs
        assert 'start' in call_kwargs
        assert 'end' in call_kwargs

    def test_data_schema_matches_angel_one(self, mocker):
        """Test output schema matches Angel One format"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        mock_ticker = mocker.Mock()
        mock_hist = pd.DataFrame({
            'Open': [2500.0],
            'High': [2550.0],
            'Low': [2480.0],
            'Close': [2540.0],
            'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2023-01-02']))

        mock_ticker.history.return_value = mock_hist
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)
        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Must match Angel One format
        assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        assert df['timestamp'].dtype == 'datetime64[ns]'
        assert df['open'].dtype == 'float64'
        assert df['volume'].dtype in ['int64', 'int32']

    def test_handles_yahoo_api_failure(self, mocker):
        """Test gracefully handles Yahoo API failures"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        mock_ticker = mocker.Mock()
        mock_ticker.history.side_effect = Exception("Yahoo API error")
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)

        # Should not crash, return empty DataFrame
        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0


class TestCaching:
    """Test caching functionality"""

    def test_cache_hit(self, mocker, tmp_path):
        """Test cache hit avoids API call"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        mock_ticker = mocker.Mock()
        mock_hist = pd.DataFrame({
            'Open': [2500.0],
            'High': [2550.0],
            'Low': [2480.0],
            'Close': [2540.0],
            'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2023-01-02']))

        mock_ticker.history.return_value = mock_hist
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=str(tmp_path))

        # First fetch (cache miss)
        df1 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Second fetch (cache hit)
        df2 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # API should only be called once
        assert mock_ticker.history.call_count == 1
        assert len(df1) == len(df2)

    def test_cache_disabled(self, mocker):
        """Test caching can be disabled"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        mock_ticker = mocker.Mock()
        mock_hist = pd.DataFrame({
            'Open': [2500.0],
            'High': [2550.0],
            'Low': [2480.0],
            'Close': [2540.0],
            'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2023-01-02']))

        mock_ticker.history.return_value = mock_hist
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)

        # Two identical fetches
        df1 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        df2 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # API should be called twice (no caching)
        assert mock_ticker.history.call_count == 2


class TestDataTransformation:
    """Test data transformation to standard format"""

    def test_transforms_to_standard_format(self, mocker):
        """Test Yahoo format transforms to standard format"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        # Yahoo returns capitalized column names
        mock_ticker = mocker.Mock()
        mock_hist = pd.DataFrame({
            'Open': [2500.0],
            'High': [2550.0],
            'Low': [2480.0],
            'Close': [2540.0],
            'Volume': [1000000]
        }, index=pd.DatetimeIndex(['2023-01-02'], name='Date'))

        mock_ticker.history.return_value = mock_hist
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)
        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Should be lowercase
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        assert 'timestamp' in df.columns

    def test_handles_missing_data(self, mocker):
        """Test handles missing data in Yahoo response"""
        from src.data.yahoo_finance_fetcher import YahooFinanceFetcher

        # Missing 'Volume' column
        mock_ticker = mocker.Mock()
        mock_hist = pd.DataFrame({
            'Open': [2500.0],
            'High': [2550.0],
            'Low': [2480.0],
            'Close': [2540.0]
        }, index=pd.DatetimeIndex(['2023-01-02']))

        mock_ticker.history.return_value = mock_hist
        mocker.patch('yfinance.Ticker', return_value=mock_ticker)

        fetcher = YahooFinanceFetcher(cache_dir=False)
        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Should still work, with volume = 0 or NaN
        assert 'volume' in df.columns
        assert len(df) == 1
