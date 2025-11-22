"""
Tests for WebSocket Data Stream

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import threading
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from src.data.websocket_data_stream import WebSocketDataStream


class TestConnection:
    """Test WebSocket connection"""

    def test_connect_success(self):
        """Test successful connection"""
        client = Mock()

        # Mock WebSocket connection
        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            result = stream.connect()

            assert result == True
            assert stream.is_connected() == True

    def test_connect_failure(self):
        """Test connection failure"""
        client = Mock()

        # Mock WebSocket connection failure
        mock_ws = Mock()
        mock_ws.connect.side_effect = Exception("Connection failed")

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            result = stream.connect()

            assert result == False
            assert stream.is_connected() == False

    def test_reconnect_on_disconnect(self):
        """Test automatic reconnection on disconnect"""
        client = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            # Simulate disconnect
            stream._on_close(mock_ws, 1000, "Normal closure")

            # Check that reconnection was attempted
            # (In real implementation, this would be async)
            assert stream._reconnect_attempts > 0


class TestSubscription:
    """Test symbol subscription"""

    def test_subscribe_symbols(self):
        """Test subscribing to symbols"""
        client = Mock()
        client._smart_api = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            symbols = [('RELIANCE', 'NSE'), ('TCS', 'NSE')]
            stream.subscribe(symbols)

            # Verify subscription was called
            assert len(stream._subscribed_symbols) == 2
            assert ('RELIANCE', 'NSE') in stream._subscribed_symbols

    def test_unsubscribe_symbols(self):
        """Test unsubscribing from symbols"""
        client = Mock()
        client._smart_api = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            symbols = [('RELIANCE', 'NSE'), ('TCS', 'NSE')]
            stream.subscribe(symbols)
            stream.unsubscribe([('RELIANCE', 'NSE')])

            # Verify unsubscription
            assert len(stream._subscribed_symbols) == 1
            assert ('RELIANCE', 'NSE') not in stream._subscribed_symbols
            assert ('TCS', 'NSE') in stream._subscribed_symbols

    def test_subscribe_multiple(self):
        """Test subscribing to multiple batches"""
        client = Mock()
        client._smart_api = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            # First batch
            stream.subscribe([('RELIANCE', 'NSE')])
            # Second batch
            stream.subscribe([('TCS', 'NSE'), ('INFY', 'NSE')])

            assert len(stream._subscribed_symbols) == 3

    def test_resubscribe_after_reconnect(self):
        """Test symbols are resubscribed after reconnection"""
        client = Mock()
        client._smart_api = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            symbols = [('RELIANCE', 'NSE')]
            stream.subscribe(symbols)

            # Simulate reconnect
            stream._on_open(mock_ws)

            # Should still have subscriptions
            assert len(stream._subscribed_symbols) == 1


class TestTickHandling:
    """Test tick data handling"""

    def test_receive_tick_data(self):
        """Test receiving tick data"""
        received_ticks = []

        def on_tick(tick):
            received_ticks.append(tick)

        client = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client, on_tick_callback=on_tick)
            stream.connect()

            # Simulate tick data
            tick_data = {
                'symbol': 'RELIANCE',
                'exchange': 'NSE',
                'last_traded_price': 2500.50,
                'volume': 1000
            }
            stream._on_tick(mock_ws, [tick_data])

            assert len(received_ticks) > 0

    def test_tick_normalization(self):
        """Test tick data is normalized to OHLCV format"""
        client = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()
            stream.subscribe([('RELIANCE', 'NSE')])

            # Simulate tick data
            tick_data = {
                'token': '2885',
                'last_traded_price': 2500.50,
                'last_traded_quantity': 10,
                'volume': 1000,
                'best_5_buy': [{'price': 2500.0, 'quantity': 100}],
                'best_5_sell': [{'price': 2501.0, 'quantity': 100}]
            }
            stream._on_tick(mock_ws, [tick_data])

            # Get latest ticks
            ticks = stream.get_latest_ticks('RELIANCE', 'NSE')

            assert len(ticks) > 0
            # Verify normalized format has required fields
            tick = ticks[0]
            assert 'timestamp' in tick
            assert 'price' in tick or 'last_traded_price' in tick
            assert 'volume' in tick

    def test_tick_buffering(self):
        """Test ticks are buffered correctly"""
        client = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client, buffer_size=100)
            stream.connect()
            stream.subscribe([('RELIANCE', 'NSE')])

            # Simulate multiple ticks
            for i in range(5):
                tick_data = {
                    'token': '2885',
                    'last_traded_price': 2500.0 + i,
                    'volume': 1000 + i*100
                }
                stream._on_tick(mock_ws, [tick_data])

            ticks = stream.get_latest_ticks('RELIANCE', 'NSE')

            assert len(ticks) == 5


class TestThreadSafety:
    """Test thread safety"""

    def test_concurrent_tick_access(self):
        """Test concurrent access to tick buffer"""
        client = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()
            stream.subscribe([('RELIANCE', 'NSE')])

            # Simulate concurrent writes and reads
            def write_ticks():
                for i in range(10):
                    tick_data = {
                        'token': '2885',
                        'last_traded_price': 2500.0 + i,
                        'volume': 1000
                    }
                    stream._on_tick(mock_ws, [tick_data])
                    time.sleep(0.001)

            def read_ticks():
                for _ in range(10):
                    ticks = stream.get_latest_ticks('RELIANCE', 'NSE')
                    time.sleep(0.001)

            # Run concurrent operations
            writer = threading.Thread(target=write_ticks)
            reader = threading.Thread(target=read_ticks)

            writer.start()
            reader.start()

            writer.join()
            reader.join()

            # Should not raise any exceptions
            assert True

    def test_concurrent_subscribe(self):
        """Test concurrent subscription operations"""
        client = Mock()
        client._smart_api = Mock()

        mock_ws = Mock()
        mock_ws.connect.return_value = True

        with patch('src.data.websocket_data_stream.SmartWebSocket', return_value=mock_ws):
            stream = WebSocketDataStream(client)
            stream.connect()

            def subscribe_batch(symbols):
                stream.subscribe(symbols)

            # Run concurrent subscriptions
            threads = []
            for i in range(3):
                symbols = [(f'SYMBOL{i}', 'NSE')]
                t = threading.Thread(target=subscribe_batch, args=(symbols,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # All symbols should be subscribed
            assert len(stream._subscribed_symbols) == 3
