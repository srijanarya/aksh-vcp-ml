"""
Edge cases for Symbol Token Lookup to reach higher coverage
"""

import pytest
from unittest.mock import Mock
from src.data.symbol_token_lookup import SymbolTokenLookup


class TestEdgeCases:
    """Test edge cases for coverage"""

    def test_lookup_api_error(self):
        """Test handling of API errors"""
        client = Mock()
        client._smart_api = Mock()
        client._smart_api.searchScrip.side_effect = Exception("API error")

        lookup = SymbolTokenLookup(client, cache_file=False)
        token = lookup.get_token('RELIANCE', 'NSE')

        assert token is None

    def test_lookup_status_false(self):
        """Test handling of failed API status"""
        client = Mock()
        client._smart_api = Mock()
        client._smart_api.searchScrip.return_value = {
            'status': False,
            'message': 'Error'
        }

        lookup = SymbolTokenLookup(client, cache_file=False)
        token = lookup.get_token('RELIANCE', 'NSE')

        assert token is None

    def test_load_cache_file_not_exists(self, tmp_path):
        """Test loading cache when file doesn't exist"""
        client = Mock()
        cache_file = str(tmp_path / "nonexistent.json")

        lookup = SymbolTokenLookup(client, cache_file=cache_file)

        # Should not raise error
        assert len(lookup._cache) == 0

    def test_load_cache_invalid_json(self, tmp_path):
        """Test loading cache with invalid JSON"""
        client = Mock()
        cache_file = str(tmp_path / "invalid.json")

        # Write invalid JSON
        with open(cache_file, 'w') as f:
            f.write("invalid json{")

        lookup = SymbolTokenLookup(client, cache_file=cache_file)

        # Should not raise error, just log warning
        assert len(lookup._cache) == 0

    def test_bulk_lookup_with_none_token(self):
        """Test bulk lookup where some symbols return None"""
        client = Mock()
        client._smart_api = Mock()

        def mock_search(exchange, symbol):
            if symbol == 'INVALID':
                return {'status': True, 'data': []}
            return {
                'status': True,
                'data': [{'symbol': symbol, 'token': '1234', 'exch_seg': exchange}]
            }

        client._smart_api.searchScrip.side_effect = mock_search

        lookup = SymbolTokenLookup(client, cache_file=False)

        symbols = [
            ('RELIANCE', 'NSE'),
            ('INVALID', 'NSE')
        ]

        tokens = lookup.get_tokens_bulk(symbols)

        # Should only contain valid token
        assert len(tokens) == 1
        assert ('RELIANCE', 'NSE') in tokens
        assert ('INVALID', 'NSE') not in tokens
