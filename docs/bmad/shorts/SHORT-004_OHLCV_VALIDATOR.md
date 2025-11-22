# SHORT-004: OHLCV Data Validator

**Parent**: FX-001 (Data Ingestion)
**Status**: ✅ Complete
**Estimated Effort**: 3-4 hours
**TDD Approach**: Red-Green-Refactor

---

## Objective

Implement comprehensive OHLCV data validation to ensure data quality before use in analysis and trading decisions.

## User Story

**AS A** portfolio manager
**I WANT** robust data validation
**SO THAT** I can trust the data used in my trading strategies and avoid errors from bad data

## Acceptance Criteria

1. Validate OHLC price relationships (high >= max(open, close), low <= min(open, close))
2. Detect and report negative/zero prices
3. Identify price jumps/gaps (potential corporate actions)
4. Detect volume anomalies
5. Check for missing/duplicate timestamps
6. Validate date range continuity
7. Generate validation report with quality score
8. 100% test coverage

---

## Technical Specification

### Class Design

```python
class OHLCVValidator:
    """
    Validate OHLCV data quality

    Performs comprehensive validation checks on price/volume data
    """

    def __init__(
        self,
        price_jump_threshold: float = 0.20,  # 20% default
        volume_spike_threshold: float = 5.0   # 5x average
    ):
        pass

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Run all validation checks

        Args:
            df: DataFrame with OHLCV data

        Returns:
            ValidationResult with is_valid, errors, warnings, quality_score
        """

    def check_ohlc_relationships(self, df: pd.DataFrame) -> List[ValidationError]:
        """Check high >= max(open, close), low <= min(open, close)"""

    def check_price_validity(self, df: pd.DataFrame) -> List[ValidationError]:
        """Check for negative/zero prices"""

    def detect_price_jumps(self, df: pd.DataFrame) -> List[ValidationWarning]:
        """Detect large price jumps (potential corporate actions)"""

    def detect_volume_anomalies(self, df: pd.DataFrame) -> List[ValidationWarning]:
        """Detect unusual volume spikes"""

    def check_timestamp_integrity(self, df: pd.DataFrame) -> List[ValidationError]:
        """Check for missing/duplicate timestamps"""

    def calculate_quality_score(self, errors: List, warnings: List) -> float:
        """Calculate overall data quality score (0-100)"""
```

### Data Models

```python
@dataclass
class ValidationError:
    timestamp: datetime
    field: str
    message: str
    severity: str = "ERROR"

@dataclass
class ValidationWarning:
    timestamp: datetime
    field: str
    message: str
    severity: str = "WARNING"

@dataclass
class ValidationResult:
    is_valid: bool
    quality_score: float  # 0-100
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    checked_rows: int
```

---

## TDD Implementation Plan

### Phase 1: RED (Write 15 failing tests)

1. **TestValidatorInitialization** (2 tests)
   - test_validator_initialization_default
   - test_validator_initialization_custom_thresholds

2. **TestOHLCRelationships** (3 tests)
   - test_valid_ohlc_relationships
   - test_high_less_than_close_detected
   - test_low_greater_than_open_detected

3. **TestPriceValidity** (3 tests)
   - test_valid_prices
   - test_negative_price_detected
   - test_zero_price_detected

4. **TestPriceJumps** (2 tests)
   - test_no_price_jumps
   - test_price_jump_detected_above_threshold

5. **TestVolumeAnomalies** (2 tests)
   - test_normal_volume
   - test_volume_spike_detected

6. **TestTimestampIntegrity** (2 tests)
   - test_valid_timestamps
   - test_duplicate_timestamp_detected

7. **TestQualityScore** (1 test)
   - test_quality_score_calculation

### Phase 2: GREEN (Implement)

### Phase 3: REFACTOR (Improve)

---

## Definition of Done

- ✅ All 19 tests passing (17 main + 2 edge cases)
- ✅ 100% code coverage
- ✅ Can validate OHLCV data from any source
- ✅ Returns detailed validation report
- ✅ Quality score calculated correctly

---

**Created**: 2025-11-19
**Completed**: 2025-11-19
**Status**: Complete
