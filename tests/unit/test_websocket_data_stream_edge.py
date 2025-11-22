"""
Edge cases for WebSocket Data Stream to reach higher coverage
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.data.websocket_data_stream import WebSocketDataStream


class TestEdgeCases:
    """Test edge cases for coverage"""

    def test_disconnect_without_websocket(self):
        """Test disconnect when WebSocket is None"""
        client = Mock()
        stream = WebSocketDataStream(client)

        # Should not raise error
        stream.disconnect()
        assert stream.is_connected() == False

    def test_get_latest_ticks_nonexistent_symbol(self):
        """Test getting ticks for non-existent symbol"""
        client = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            # Get ticks for symbol that was never subscribed
            ticks = stream.get_latest_ticks('NONEXISTENT', 'NSE')

            assert len(ticks) == 0

    def test_on_error_callback(self):
        """Test WebSocket error callback"""
        client = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            # Simulate error
            stream._on_error(mock_ws, "Test error")

            # Should not raise exception
            assert True

    def test_tick_processing_exception(self):
        """Test handling of exception during tick processing"""
        client = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            # Simulate invalid tick data that will cause exception
            invalid_tick = None  # This will cause error in _normalize_tick

            # Should handle exception gracefully
            stream._on_tick(mock_ws, [invalid_tick])

            # Should still be connected
            assert stream.is_connected() == True

    def test_unsubscribe_with_token_removal(self):
        """Test unsubscribing removes token mapping"""
        client = Mock()
        client._smart_api = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            # Subscribe to RELIANCE (which has hardcoded token '2885')
            stream.subscribe([('RELIANCE', 'NSE')])

            # Verify token is in map
            assert '2885' in stream._symbol_token_map

            # Unsubscribe
            stream.unsubscribe([('RELIANCE', 'NSE')])

            # Token should be removed from map
            assert '2885' not in stream._symbol_token_map
