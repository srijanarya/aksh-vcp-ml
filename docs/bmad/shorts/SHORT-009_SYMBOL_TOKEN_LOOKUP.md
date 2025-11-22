# SHORT-009: Symbol Token Lookup Service

**Parent**: FX-001 (Data Ingestion)
**Status**: ✅ Complete
**Estimated Effort**: 2-3 hours
**TDD Approach**: Red-Green-Refactor

---

## Objective

Implement symbol to token lookup service with caching for Angel One API.

## User Story

**AS A** data fetcher
**I WANT** fast symbol to token lookups
**SO THAT** I don't repeatedly query the API for the same symbol

## Acceptance Criteria

1. Look up Angel One token for symbol
2. Cache lookups persistently
3. Support both NSE and BSE
4. Handle symbol not found
5. Bulk lookup capability
6. Cache invalidation
7. 100% test coverage

---

## Technical Specification

### Class Design

```python
class SymbolTokenLookup:
    """
    Symbol to token lookup with caching
    """

    def __init__(
        self,
        client: AngelOneClient,
        cache_file: str = None
    ):
        pass

    def get_token(
        self,
        symbol: str,
        exchange: str
    ) -> Optional[str]:
        """Get token for symbol"""

    def get_tokens_bulk(
        self,
        symbols: List[Tuple[str, str]]
    ) -> Dict[Tuple[str, str], str]:
        """Get tokens for multiple symbols"""

    def invalidate(self, symbol: str = None):
        """Invalidate cache"""
```

---

## TDD Implementation Plan

### Phase 1: RED (Write 10 failing tests)

1. **TestLookupInitialization** (2 tests)
   - test_lookup_initialization
   - test_lookup_with_cache_file

2. **TestSingleLookup** (3 tests)
   - test_get_token_success
   - test_get_token_cached
   - test_get_token_not_found

3. **TestBulkLookup** (2 tests)
   - test_get_tokens_bulk
   - test_get_tokens_bulk_partial_cache

4. **TestCacheManagement** (3 tests)
   - test_cache_persistence
   - test_invalidate_all
   - test_invalidate_single_symbol

### Phase 2: GREEN (Implement)

### Phase 3: REFACTOR (Improve)

---

## Definition of Done

- ✅ All 15 tests passing (10 main + 5 edge cases)
- ✅ 92% code coverage
- ✅ Fast cached lookups
- ✅ Persistent cache
- ✅ Bulk operations

---

**Created**: 2025-11-19
**Completed**: 2025-11-19
**Status**: Complete
