# SHORT-005: Corporate Action Handler

**Parent**: FX-001 (Data Ingestion)
**Status**: ✅ Complete
**Estimated Effort**: 4-5 hours
**TDD Approach**: Red-Green-Refactor

---

## Objective

Implement corporate action handling (stock splits, bonuses, dividends, rights issues) to adjust historical OHLCV data for accurate backtesting and analysis.

## User Story

**AS A** portfolio manager
**I WANT** historical prices adjusted for corporate actions
**SO THAT** my backtests and technical analysis reflect accurate price movements

## Acceptance Criteria

1. Detect stock splits from price jumps
2. Adjust OHLCV data for splits (prices ÷ ratio, volume × ratio)
3. Handle bonus issues (similar to splits)
4. Track dividends (for total return calculations)
5. Store corporate action history
6. Provide unadjusted and adjusted price views
7. 100% test coverage

---

## Technical Specification

### Class Design

```python
class CorporateActionHandler:
    """
    Handle corporate actions (splits, bonuses, dividends)

    Adjusts historical OHLCV data for accurate analysis
    """

    def __init__(
        self,
        storage_path: Optional[str] = None
    ):
        pass

    def detect_split(
        self,
        df: pd.DataFrame,
        threshold: float = 0.45
    ) -> Optional[SplitEvent]:
        """
        Detect stock split from price jump

        Args:
            df: OHLCV DataFrame
            threshold: Price jump threshold (e.g., 0.45 for 2:1 split)

        Returns:
            SplitEvent if detected, None otherwise
        """

    def adjust_for_split(
        self,
        df: pd.DataFrame,
        split_date: datetime,
        split_ratio: float
    ) -> pd.DataFrame:
        """
        Adjust historical prices for stock split

        Before split_date:
        - Prices ÷ split_ratio
        - Volume × split_ratio

        Args:
            df: OHLCV DataFrame
            split_date: Date of split
            split_ratio: Split ratio (e.g., 2.0 for 2:1 split)

        Returns:
            Adjusted DataFrame
        """

    def record_action(
        self,
        symbol: str,
        action: CorporateAction
    ):
        """Store corporate action history"""

    def get_actions(
        self,
        symbol: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[CorporateAction]:
        """Retrieve corporate action history"""

    def apply_all_adjustments(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """Apply all recorded corporate actions to OHLCV data"""
```

### Data Models

```python
@dataclass
class CorporateAction:
    symbol: str
    action_type: str  # "SPLIT", "BONUS", "DIVIDEND"
    date: datetime
    details: Dict  # ratio, amount, etc.

@dataclass
class SplitEvent:
    date: datetime
    ratio: float  # e.g., 2.0 for 2:1 split
    old_price: float
    new_price: float
```

---

## TDD Implementation Plan

### Phase 1: RED (Write 18 failing tests)

1. **TestHandlerInitialization** (2 tests)
   - test_handler_initialization_default
   - test_handler_initialization_custom_storage

2. **TestSplitDetection** (4 tests)
   - test_no_split_detected_normal_data
   - test_2_for_1_split_detected
   - test_10_for_1_split_detected
   - test_reverse_split_detected

3. **TestSplitAdjustment** (4 tests)
   - test_adjust_prices_for_split
   - test_adjust_volume_for_split
   - test_split_only_affects_pre_split_data
   - test_multiple_splits

4. **TestActionRecording** (3 tests)
   - test_record_split_action
   - test_record_bonus_action
   - test_record_dividend_action

5. **TestActionRetrieval** (3 tests)
   - test_get_all_actions_for_symbol
   - test_get_actions_in_date_range
   - test_no_actions_for_symbol

6. **TestFullAdjustment** (2 tests)
   - test_apply_single_adjustment
   - test_apply_multiple_adjustments

### Phase 2: GREEN (Implement)

### Phase 3: REFACTOR (Improve)

---

## Definition of Done

- ✅ All 21 tests passing (18 main + 3 edge cases)
- ✅ 100% code coverage
- ✅ Can detect splits from price data
- ✅ Correctly adjusts OHLCV for corporate actions
- ✅ Persistent action history storage

---

**Created**: 2025-11-19
**Completed**: 2025-11-19
**Status**: Complete
