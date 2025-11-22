# SHORT-012: Real-Time WebSocket Data Stream

**Parent**: FX-001 (Data Ingestion)
**Status**: ✅ Complete
**Estimated Effort**: 4-5 hours
**TDD Approach**: Red-Green-Refactor

---

## Objective

Implement real-time WebSocket data streaming for Angel One market data.

## User Story

**AS A** trader
**I WANT** real-time streaming market data
**SO THAT** I can react to price movements instantly

## Acceptance Criteria

1. Connect to Angel One WebSocket feed
2. Subscribe to symbol tick data
3. Parse and normalize tick data to OHLCV
4. Handle reconnection on disconnect
5. Buffer ticks for aggregation
6. Thread-safe tick handling
7. 100% test coverage (with mocked WebSocket)

---

## Technical Specification

### Class Design

```python
class WebSocketDataStream:
    """
    Real-time WebSocket data streaming

    Features:
    - WebSocket connection management
    - Symbol subscription
    - Tick data normalization
    - Auto-reconnection
    - Thread-safe buffering
    """

    def __init__(
        self,
        client: AngelOneClient,
        on_tick_callback: Callable = None
    ):
        pass

    def connect(self) -> bool:
        """Connect to WebSocket"""

    def subscribe(self, symbols: List[Tuple[str, str]]):
        """Subscribe to symbols"""

    def unsubscribe(self, symbols: List[Tuple[str, str]]):
        """Unsubscribe from symbols"""

    def disconnect(self):
        """Disconnect from WebSocket"""

    def get_latest_ticks(
        self,
        symbol: str,
        exchange: str
    ) -> List[Dict]:
        """Get buffered ticks for symbol"""
```

---

## TDD Implementation Plan

### Phase 1: RED (Write 12 failing tests)

1. **TestConnection** (3 tests)
   - test_connect_success
   - test_connect_failure
   - test_reconnect_on_disconnect

2. **TestSubscription** (4 tests)
   - test_subscribe_symbols
   - test_unsubscribe_symbols
   - test_subscribe_multiple
   - test_resubscribe_after_reconnect

3. **TestTickHandling** (3 tests)
   - test_receive_tick_data
   - test_tick_normalization
   - test_tick_buffering

4. **TestThreadSafety** (2 tests)
   - test_concurrent_tick_access
   - test_concurrent_subscribe

### Phase 2: GREEN (Implement)

### Phase 3: REFACTOR (Improve)

---

## Definition of Done

- ✅ All 12 tests passing
- ✅ 100% code coverage
- ✅ WebSocket connection working
- ✅ Tick data normalized
- ✅ Thread-safe implementation

---

**Created**: 2025-11-19
**Completed**: 2025-11-19
**Status**: Complete
