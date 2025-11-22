"""
Unit tests for Angel One OHLCV Data Fetcher

Following TDD approach:
1. RED: Write failing tests first
2. GREEN: Make tests pass
3. REFACTOR: Improve code

Test Coverage Target: 100% (critical component)
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import Mock


class TestOHLCVFetcherInitialization:
    """Test AngelOneOHLCVFetcher initialization"""

    def test_fetcher_initialization_with_authenticated_client(self):
        """Test fetcher initializes with authenticated client"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        # Create authenticated client
        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"  # Simulate authenticated

        fetcher = AngelOneOHLCVFetcher(client=client)

        assert fetcher.client == client
        assert fetcher.cache_dir is not None
        assert fetcher.cache_ttl == 3600  # Default 1 hour

    def test_fetcher_initialization_with_unauthenticated_client_raises_error(self):
        """Test fetcher raises error with unauthenticated client"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        # Create unauthenticated client
        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        # No session_token set

        with pytest.raises(ValueError, match="Client must be authenticated"):
            AngelOneOHLCVFetcher(client=client)

    def test_fetcher_initialization_with_custom_cache_settings(self, tmp_path):
        """Test fetcher with custom cache configuration"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        custom_cache = str(tmp_path / "custom_cache")
        fetcher = AngelOneOHLCVFetcher(
            client=client,
            cache_dir=custom_cache,
            cache_ttl=7200
        )

        assert fetcher.cache_dir == custom_cache
        assert fetcher.cache_ttl == 7200


class TestSymbolTokenLookup:
    """Test Angel One symbol token lookup"""

    def test_get_symbol_token_for_nse_stock(self, mocker):
        """Test get symbol token for NSE stock"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        # Mock the SmartAPI searchScrip response
        mock_smartapi = mocker.Mock()
        mock_smartapi.searchScrip.return_value = {
            'status': True,
            'data': [
                {
                    'symbol': 'RELIANCE',
                    'token': '2885',
                    'exch_seg': 'NSE'
                }
            ]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client)
        token = fetcher.get_symbol_token("RELIANCE", "NSE")

        assert token == "2885"

    def test_get_symbol_token_for_bse_stock(self, mocker):
        """Test get symbol token for BSE stock"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.searchScrip.return_value = {
            'status': True,
            'data': [
                {
                    'symbol': 'RELIANCE',
                    'token': '500325',
                    'exch_seg': 'BSE'
                }
            ]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client)
        token = fetcher.get_symbol_token("RELIANCE", "BSE")

        assert token == "500325"

    def test_get_symbol_token_invalid_symbol_raises_error(self, mocker):
        """Test invalid symbol raises error"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.searchScrip.return_value = {
            'status': False,
            'message': 'Symbol not found'
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client)

        with pytest.raises(ValueError, match="Symbol .* not found"):
            fetcher.get_symbol_token("INVALID", "NSE")

    def test_get_symbol_token_caching(self, mocker):
        """Test symbol token is cached"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.searchScrip.return_value = {
            'status': True,
            'data': [{'symbol': 'RELIANCE', 'token': '2885', 'exch_seg': 'NSE'}]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client)

        # First call
        token1 = fetcher.get_symbol_token("RELIANCE", "NSE")

        # Second call (should use cache)
        token2 = fetcher.get_symbol_token("RELIANCE", "NSE")

        assert token1 == token2 == "2885"
        # searchScrip should only be called once due to caching
        assert mock_smartapi.searchScrip.call_count == 1


class TestOHLCVFetching:
    """Test OHLCV data fetching"""

    def test_fetch_daily_ohlcv_success(self, mocker):
        """Test fetch daily OHLCV data"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        # Mock API response
        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [
                ["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000],
                ["2023-01-03T09:15:00+05:30", 2540.0, 2580.0, 2520.0, 2570.0, 1200000],
            ]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client)

        # Mock get_symbol_token
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        assert df.iloc[0]['open'] == 2500.0
        assert df.iloc[0]['close'] == 2540.0

    def test_fetch_intraday_5min_ohlcv_success(self, mocker):
        """Test fetch 5-minute intraday OHLCV data"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [
                ["2023-01-02T09:15:00+05:30", 2500.0, 2510.0, 2495.0, 2505.0, 100000],
                ["2023-01-02T09:20:00+05:30", 2505.0, 2515.0, 2500.0, 2510.0, 120000],
            ]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client)
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="FIVE_MINUTE",
            from_date=datetime(2023, 1, 2, 9, 15),
            to_date=datetime(2023, 1, 2, 15, 30)
        )

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_fetch_with_date_range(self, mocker):
        """Test fetch respects date range"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [
                ["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000],
            ]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client, cache_dir=False)  # Disable cache
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        from_date = datetime(2023, 1, 1)
        to_date = datetime(2023, 1, 31)

        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=from_date,
            to_date=to_date
        )

        # Verify API was called with correct date range
        assert mock_smartapi.getCandleData.called
        call_kwargs = mock_smartapi.getCandleData.call_args.kwargs
        assert 'fromdate' in call_kwargs
        assert 'todate' in call_kwargs

    def test_fetch_invalid_symbol_raises_error(self, mocker):
        """Test invalid symbol raises error"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        fetcher = AngelOneOHLCVFetcher(client=client)

        # Mock get_symbol_token to raise error
        mocker.patch.object(
            fetcher,
            'get_symbol_token',
            side_effect=ValueError("Symbol INVALID not found")
        )

        with pytest.raises(ValueError, match="Symbol .* not found"):
            fetcher.fetch_ohlcv(
                symbol="INVALID",
                exchange="NSE",
                interval="ONE_DAY",
                from_date=datetime(2023, 1, 1),
                to_date=datetime(2023, 1, 31)
            )

    def test_fetch_invalid_date_range_raises_error(self, mocker):
        """Test invalid date range raises error"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        fetcher = AngelOneOHLCVFetcher(client=client)
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        # from_date after to_date
        with pytest.raises(ValueError, match="from_date must be before to_date"):
            fetcher.fetch_ohlcv(
                symbol="RELIANCE",
                exchange="NSE",
                interval="ONE_DAY",
                from_date=datetime(2023, 12, 31),
                to_date=datetime(2023, 1, 1)
            )

    def test_fetch_unauthenticated_raises_error(self, mocker):
        """Test fetch with expired token raises error"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.side_effect = Exception("Invalid token")
        client._smart_api = mock_smartapi

        # Mock refresh to fail
        mocker.patch.object(client, 'refresh_session', return_value=False)

        fetcher = AngelOneOHLCVFetcher(client=client, cache_dir=False)
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        with pytest.raises(Exception, match="Invalid token"):
            fetcher.fetch_ohlcv(
                symbol="RELIANCE",
                exchange="NSE",
                interval="ONE_DAY",
                from_date=datetime(2023, 1, 1),
                to_date=datetime(2023, 1, 31)
            )

    def test_fetch_rate_limit_retry(self, mocker):
        """Test rate limit triggers retry with backoff"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        import requests

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()

        # First call: rate limit error
        # Second call: success
        mock_smartapi.getCandleData.side_effect = [
            requests.HTTPError("429 Too Many Requests"),
            {
                'status': True,
                'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
            }
        ]
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client, cache_dir=False)  # Disable cache
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        # Mock time.sleep to avoid actual delays
        mock_sleep = mocker.patch('src.data.angel_one_ohlcv.time.sleep')

        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Should succeed after retry
        assert len(df) == 1
        assert mock_smartapi.getCandleData.call_count == 2
        # Verify sleep was called for retry
        assert mock_sleep.call_count > 0

    def test_fetch_token_expiry_auto_refresh(self, mocker):
        """Test auto-refresh on token expiry"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"
        client.refresh_token = "refresh_token"

        mock_smartapi = mocker.Mock()

        # First 3 calls: token expired (retry logic will use these)
        # 4th call after refresh: success
        mock_smartapi.getCandleData.side_effect = [
            Exception("Invalid token"),
            Exception("Invalid token"),
            Exception("Invalid token"),
            {
                'status': True,
                'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
            }
        ]
        client._smart_api = mock_smartapi

        # Mock refresh_session
        mocker.patch.object(client, 'refresh_session', return_value=True)

        fetcher = AngelOneOHLCVFetcher(client=client, cache_dir=False)  # Disable cache
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Should succeed after token refresh
        assert len(df) == 1
        client.refresh_session.assert_called_once()


class TestDataValidation:
    """Test OHLCV data validation"""

    def test_validate_ohlc_valid_data(self):
        """Test validation passes for valid OHLC data"""
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        fetcher = AngelOneOHLCVFetcher(client=client)

        df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 2)],
            'open': [2500.0],
            'high': [2550.0],
            'low': [2480.0],
            'close': [2540.0],
            'volume': [1000000]
        })

        is_valid, errors = fetcher.validate_ohlc(df)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_ohlc_invalid_high_low_relationship(self):
        """Test validation catches invalid high/low"""
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        fetcher = AngelOneOHLCVFetcher(client=client)

        # Invalid: high < low
        df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 2)],
            'open': [2500.0],
            'high': [2400.0],  # Invalid: high < low
            'low': [2480.0],
            'close': [2450.0],
            'volume': [1000000]
        })

        is_valid, errors = fetcher.validate_ohlc(df)

        assert is_valid is False
        assert len(errors) > 0
        assert any('high' in err.lower() for err in errors)

    def test_validate_ohlc_negative_prices(self):
        """Test validation catches negative prices"""
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        fetcher = AngelOneOHLCVFetcher(client=client)

        df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 2)],
            'open': [-2500.0],  # Invalid: negative
            'high': [2550.0],
            'low': [2480.0],
            'close': [2540.0],
            'volume': [1000000]
        })

        is_valid, errors = fetcher.validate_ohlc(df)

        assert is_valid is False
        assert any('negative' in err.lower() or 'positive' in err.lower() for err in errors)

    def test_validate_ohlc_missing_columns(self):
        """Test validation catches missing columns"""
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        fetcher = AngelOneOHLCVFetcher(client=client)

        # Missing 'close' column
        df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 2)],
            'open': [2500.0],
            'high': [2550.0],
            'low': [2480.0],
            'volume': [1000000]
        })

        is_valid, errors = fetcher.validate_ohlc(df)

        assert is_valid is False
        assert any('column' in err.lower() or 'missing' in err.lower() for err in errors)

    def test_detect_data_gaps(self):
        """Test detection of missing dates"""
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        fetcher = AngelOneOHLCVFetcher(client=client)

        # Missing Jan 3 (gap in data)
        df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 2), datetime(2023, 1, 4)],
            'open': [2500.0, 2520.0],
            'high': [2550.0, 2570.0],
            'low': [2480.0, 2500.0],
            'close': [2540.0, 2560.0],
            'volume': [1000000, 1100000]
        })

        gaps = fetcher.detect_data_gaps(df)

        assert len(gaps) > 0

    def test_detect_large_price_jumps(self):
        """Test detection of suspicious price jumps"""
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        from src.data.angel_one_client import AngelOneClient

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        fetcher = AngelOneOHLCVFetcher(client=client)

        # 50% jump (suspicious)
        df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 2), datetime(2023, 1, 3)],
            'open': [2500.0, 3750.0],  # 50% jump
            'high': [2550.0, 3800.0],
            'low': [2480.0, 3700.0],
            'close': [2540.0, 3780.0],
            'volume': [1000000, 1100000]
        })

        jumps = fetcher.detect_price_jumps(df, threshold=0.2)

        assert len(jumps) > 0


class TestCaching:
    """Test OHLCV data caching"""

    def test_cache_hit_avoids_api_call(self, mocker, tmp_path):
        """Test cache hit avoids API call"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(
            client=client,
            cache_dir=str(tmp_path),
            cache_ttl=3600
        )
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        # First fetch (cache miss)
        df1 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Second fetch (cache hit)
        df2 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # API should only be called once
        assert mock_smartapi.getCandleData.call_count == 1
        assert len(df1) == len(df2)

    def test_cache_miss_makes_api_call(self, mocker, tmp_path):
        """Test cache miss triggers API call"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(
            client=client,
            cache_dir=str(tmp_path),
            cache_ttl=3600
        )
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        # Different date ranges = different cache keys
        df1 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        df2 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 2, 1),
            to_date=datetime(2023, 2, 28)
        )

        # Both should trigger API calls (different cache keys)
        assert mock_smartapi.getCandleData.call_count == 2

    def test_cache_ttl_expiry(self, mocker, tmp_path):
        """Test cache expires after TTL"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        import time

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(
            client=client,
            cache_dir=str(tmp_path),
            cache_ttl=1  # 1 second TTL
        )
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        # First fetch
        df1 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Wait for cache to expire
        time.sleep(1.1)

        # Second fetch (cache expired)
        df2 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # API should be called twice (cache expired)
        assert mock_smartapi.getCandleData.call_count == 2

    def test_cache_disabled(self, mocker):
        """Test caching can be disabled"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(
            client=client,
            cache_dir=False  # Disable caching (False = no cache)
        )
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        # Two identical fetches
        df1 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        df2 = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # API should be called twice (no caching)
        assert mock_smartapi.getCandleData.call_count == 2


class TestRateLimiting:
    """Test rate limiting"""

    def test_rate_limiter_respects_3_req_per_second(self, mocker):
        """Test rate limiter respects 3 requests/second"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        import time

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client, cache_dir=False)
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        start_time = time.time()

        # Make 6 requests (should take ~2 seconds with 3 req/sec limit)
        for i in range(6):
            fetcher.fetch_ohlcv(
                symbol="RELIANCE",
                exchange="NSE",
                interval="ONE_DAY",
                from_date=datetime(2023, 1, 1 + i),
                to_date=datetime(2023, 1, 2 + i)
            )

        elapsed = time.time() - start_time

        # Rate limiter sleeps after 3rd and 6th requests
        # Should have some delay from rate limiting
        assert elapsed >= 0.5  # At least some rate limiting occurred

    def test_rate_limiter_429_triggers_backoff(self, mocker):
        """Test 429 response triggers exponential backoff"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        import requests

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()

        # Simulate rate limit, then success
        error_response = requests.Response()
        error_response.status_code = 429

        mock_smartapi.getCandleData.side_effect = [
            requests.HTTPError("429", response=error_response),
            {
                'status': True,
                'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
            }
        ]
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client, cache_dir=False)
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        # Mock sleep in the correct module
        mock_sleep = mocker.patch('src.data.angel_one_ohlcv.time.sleep')

        df = fetcher.fetch_ohlcv(
            symbol="RELIANCE",
            exchange="NSE",
            interval="ONE_DAY",
            from_date=datetime(2023, 1, 1),
            to_date=datetime(2023, 1, 31)
        )

        # Should have slept before retrying
        assert mock_sleep.call_count > 0
        assert len(df) == 1

    def test_rate_limiter_concurrent_requests(self, mocker):
        """Test rate limiter handles concurrent requests"""
        from src.data.angel_one_client import AngelOneClient
        from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
        import concurrent.futures

        client = AngelOneClient(
            api_key="test_key",
            client_id="TEST123",
            mpin="1234",
            totp_secret="JBSWY3DPEHPK3PXP"
        )
        client.session_token = "test_token"

        mock_smartapi = mocker.Mock()
        mock_smartapi.getCandleData.return_value = {
            'status': True,
            'data': [["2023-01-02T09:15:00+05:30", 2500.0, 2550.0, 2480.0, 2540.0, 1000000]]
        }
        client._smart_api = mock_smartapi

        fetcher = AngelOneOHLCVFetcher(client=client, cache_dir=False)
        mocker.patch.object(fetcher, 'get_symbol_token', return_value='2885')

        # Make 5 concurrent requests
        def fetch_data(day):
            return fetcher.fetch_ohlcv(
                symbol="RELIANCE",
                exchange="NSE",
                interval="ONE_DAY",
                from_date=datetime(2023, 1, day),
                to_date=datetime(2023, 1, day + 1)
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_data, i) for i in range(1, 6)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert len(results) == 5
        assert all(len(df) > 0 for df in results)
