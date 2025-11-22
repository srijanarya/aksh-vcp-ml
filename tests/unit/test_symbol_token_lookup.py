"""
Tests for Symbol Token Lookup Service

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import os
from unittest.mock import Mock
from src.data.symbol_token_lookup import SymbolTokenLookup


class TestLookupInitialization:
    """Test lookup initialization"""

    def test_lookup_initialization(self):
        """Test lookup with default cache"""
        client = Mock()
        lookup = SymbolTokenLookup(client)
        assert lookup.client == client
        assert lookup.cache_file is not None

    def test_lookup_with_cache_file(self, tmp_path):
        """Test lookup with custom cache file"""
        client = Mock()
        cache_file = str(tmp_path / "token_cache.json")
        lookup = SymbolTokenLookup(client, cache_file=cache_file)
        assert lookup.cache_file == cache_file


class TestSingleLookup:
    """Test single symbol lookup"""

    def test_get_token_success(self):
        """Test successful token lookup"""
        client = Mock()
        client._smart_api = Mock()
        client._smart_api.searchScrip.return_value = {
            'status': True,
            'data': [
                {'symbol': 'RELIANCE', 'token': '2885', 'exch_seg': 'NSE'}
            ]
        }

        lookup = SymbolTokenLookup(client, cache_file=False)
        token = lookup.get_token('RELIANCE', 'NSE')

        assert token == '2885'
        client._smart_api.searchScrip.assert_called_once_with('NSE', 'RELIANCE')

    def test_get_token_cached(self):
        """Test cached token lookup (no API call)"""
        client = Mock()
        client._smart_api = Mock()
        client._smart_api.searchScrip.return_value = {
            'status': True,
            'data': [
                {'symbol': 'RELIANCE', 'token': '2885', 'exch_seg': 'NSE'}
            ]
        }

        lookup = SymbolTokenLookup(client, cache_file=False)

        # First call
        lookup.get_token('RELIANCE', 'NSE')

        # Second call should use cache
        client._smart_api.reset_mock()
        token = lookup.get_token('RELIANCE', 'NSE')

        assert token == '2885'
        client._smart_api.searchScrip.assert_not_called()

    def test_get_token_not_found(self):
        """Test token lookup for non-existent symbol"""
        client = Mock()
        client._smart_api = Mock()
        client._smart_api.searchScrip.return_value = {
            'status': True,
            'data': []
        }

        lookup = SymbolTokenLookup(client, cache_file=False)
        token = lookup.get_token('INVALID', 'NSE')

        assert token is None


class TestBulkLookup:
    """Test bulk symbol lookup"""

    def test_get_tokens_bulk(self):
        """Test bulk token lookup"""
        client = Mock()
        client._smart_api = Mock()

        def mock_search(exchange, symbol):
            tokens = {'RELIANCE': '2885', 'TCS': '11536', 'INFY': '1594'}
            return {
                'status': True,
                'data': [{'symbol': symbol, 'token': tokens.get(symbol, '0'), 'exch_seg': exchange}]
            }

        client._smart_api.searchScrip.side_effect = mock_search

        lookup = SymbolTokenLookup(client, cache_file=False)

        symbols = [
            ('RELIANCE', 'NSE'),
            ('TCS', 'NSE'),
            ('INFY', 'NSE')
        ]

        tokens = lookup.get_tokens_bulk(symbols)

        assert len(tokens) == 3
        assert tokens[('RELIANCE', 'NSE')] == '2885'
        assert tokens[('TCS', 'NSE')] == '11536'
        assert tokens[('INFY', 'NSE')] == '1594'

    def test_get_tokens_bulk_partial_cache(self):
        """Test bulk lookup with some symbols already cached"""
        client = Mock()
        client._smart_api = Mock()

        def mock_search(exchange, symbol):
            tokens = {'TCS': '11536'}
            return {
                'status': True,
                'data': [{'symbol': symbol, 'token': tokens.get(symbol, '0'), 'exch_seg': exchange}]
            }

        client._smart_api.searchScrip.side_effect = mock_search

        lookup = SymbolTokenLookup(client, cache_file=False)

        # Pre-cache RELIANCE
        lookup._cache[('RELIANCE', 'NSE')] = '2885'

        symbols = [
            ('RELIANCE', 'NSE'),  # Cached
            ('TCS', 'NSE')        # Not cached
        ]

        tokens = lookup.get_tokens_bulk(symbols)

        assert len(tokens) == 2
        assert tokens[('RELIANCE', 'NSE')] == '2885'
        assert tokens[('TCS', 'NSE')] == '11536'

        # Should only call API once for TCS
        assert client._smart_api.searchScrip.call_count == 1


class TestCacheManagement:
    """Test cache management"""

    def test_cache_persistence(self, tmp_path):
        """Test cache is saved to disk"""
        client = Mock()
        client._smart_api = Mock()
        client._smart_api.searchScrip.return_value = {
            'status': True,
            'data': [{'symbol': 'RELIANCE', 'token': '2885', 'exch_seg': 'NSE'}]
        }

        cache_file = str(tmp_path / "token_cache.json")

        # Create lookup and fetch token
        lookup = SymbolTokenLookup(client, cache_file=cache_file)
        lookup.get_token('RELIANCE', 'NSE')

        # Create new lookup instance
        client2 = Mock()
        lookup2 = SymbolTokenLookup(client2, cache_file=cache_file)

        # Should load from cache file
        token = lookup2.get_token('RELIANCE', 'NSE')
        assert token == '2885'

        # Should not call API
        client2._smart_api = Mock()
        assert not hasattr(client2._smart_api, 'searchScrip') or not client2._smart_api.searchScrip.called

    def test_invalidate_all(self):
        """Test invalidating entire cache"""
        client = Mock()
        client._smart_api = Mock()
        client._smart_api.searchScrip.return_value = {
            'status': True,
            'data': [{'symbol': 'RELIANCE', 'token': '2885', 'exch_seg': 'NSE'}]
        }

        lookup = SymbolTokenLookup(client, cache_file=False)

        # Cache token
        lookup.get_token('RELIANCE', 'NSE')
        assert len(lookup._cache) > 0

        # Invalidate
        lookup.invalidate()
        assert len(lookup._cache) == 0

    def test_invalidate_single_symbol(self):
        """Test invalidating single symbol"""
        client = Mock()
        lookup = SymbolTokenLookup(client, cache_file=False)

        # Manually populate cache
        lookup._cache[('RELIANCE', 'NSE')] = '2885'
        lookup._cache[('TCS', 'NSE')] = '11536'

        # Invalidate RELIANCE only
        lookup.invalidate(symbol='RELIANCE', exchange='NSE')

        assert ('RELIANCE', 'NSE') not in lookup._cache
        assert ('TCS', 'NSE') in lookup._cache
