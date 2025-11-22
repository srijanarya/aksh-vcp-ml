"""
Tests for OHLCV Data Validator

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.data.ohlcv_validator import (
    OHLCVValidator,
    ValidationError,
    ValidationWarning,
    ValidationResult
)


class TestValidatorInitialization:
    """Test validator initialization"""

    def test_validator_initialization_default(self):
        """Test validator with default parameters"""
        validator = OHLCVValidator()
        assert validator.price_jump_threshold == 0.20
        assert validator.volume_spike_threshold == 5.0

    def test_validator_initialization_custom_thresholds(self):
        """Test validator with custom thresholds"""
        validator = OHLCVValidator(
            price_jump_threshold=0.15,
            volume_spike_threshold=3.0
        )
        assert validator.price_jump_threshold == 0.15
        assert validator.volume_spike_threshold == 3.0


class TestOHLCRelationships:
    """Test OHLC price relationship validation"""

    @pytest.fixture
    def validator(self):
        return OHLCVValidator()

    def test_valid_ohlc_relationships(self, validator):
        """Test valid OHLC data passes validation"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 102,
                'high': 110,
                'low': 100,
                'close': 108,
                'volume': 1200
            }
        ])
        errors = validator.check_ohlc_relationships(df)
        assert len(errors) == 0

    def test_high_less_than_close_detected(self, validator):
        """Test detection of high < close"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 99,  # Invalid: high < close and high < open
                'low': 95,
                'close': 102,
                'volume': 1000
            }
        ])
        errors = validator.check_ohlc_relationships(df)
        assert len(errors) == 2  # Two errors: high < open and high < close
        assert all(e.field == 'high' for e in errors)
        assert all('less than' in e.message.lower() for e in errors)

    def test_low_greater_than_open_detected(self, validator):
        """Test detection of low > open"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 103,  # Invalid: low > open and low > close
                'close': 102,
                'volume': 1000
            }
        ])
        errors = validator.check_ohlc_relationships(df)
        assert len(errors) == 2  # Two errors: low > open and low > close
        assert all(e.field == 'low' for e in errors)
        assert all('greater than' in e.message.lower() for e in errors)


class TestPriceValidity:
    """Test price validity checks"""

    @pytest.fixture
    def validator(self):
        return OHLCVValidator()

    def test_valid_prices(self, validator):
        """Test all positive prices pass validation"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100.5,
                'high': 105.2,
                'low': 95.8,
                'close': 102.3,
                'volume': 1000
            }
        ])
        errors = validator.check_price_validity(df)
        assert len(errors) == 0

    def test_negative_price_detected(self, validator):
        """Test detection of negative prices"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': -5,  # Invalid: negative price
                'close': 102,
                'volume': 1000
            }
        ])
        errors = validator.check_price_validity(df)
        assert len(errors) >= 1
        assert any('negative' in e.message.lower() for e in errors)

    def test_zero_price_detected(self, validator):
        """Test detection of zero prices"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 0,  # Invalid: zero price
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            }
        ])
        errors = validator.check_price_validity(df)
        assert len(errors) >= 1
        assert any('zero' in e.message.lower() or 'non-positive' in e.message.lower() for e in errors)


class TestPriceJumps:
    """Test price jump detection"""

    @pytest.fixture
    def validator(self):
        return OHLCVValidator(price_jump_threshold=0.20)

    def test_no_price_jumps(self, validator):
        """Test no warnings for normal price movements"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 103,  # 1% jump from previous close
                'high': 108,
                'low': 100,
                'close': 106,
                'volume': 1200
            }
        ])
        warnings = validator.detect_price_jumps(df)
        assert len(warnings) == 0

    def test_price_jump_detected_above_threshold(self, validator):
        """Test detection of price jumps above 20% threshold"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 130,  # 27.5% jump from previous close
                'high': 135,
                'low': 128,
                'close': 132,
                'volume': 5000
            }
        ])
        warnings = validator.detect_price_jumps(df)
        assert len(warnings) >= 1
        assert warnings[0].timestamp == datetime(2025, 1, 2)
        assert 'jump' in warnings[0].message.lower()


class TestVolumeAnomalies:
    """Test volume anomaly detection"""

    @pytest.fixture
    def validator(self):
        return OHLCVValidator(volume_spike_threshold=5.0)

    def test_normal_volume(self, validator):
        """Test no warnings for normal volume"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 102,
                'high': 108,
                'low': 100,
                'close': 106,
                'volume': 1200  # 1.2x average, below 5x threshold
            },
            {
                'timestamp': datetime(2025, 1, 3),
                'open': 106,
                'high': 112,
                'low': 104,
                'close': 110,
                'volume': 900
            }
        ])
        warnings = validator.detect_volume_anomalies(df)
        assert len(warnings) == 0

    def test_volume_spike_detected(self, validator):
        """Test detection of volume spikes above 5x threshold"""
        # Use 10 rows with 1000 volume, then 1 spike of 60000
        # avg = (10*1000 + 60000)/11 = 6363, threshold = 5*6363 = 31818
        # 60000 > 31818, so warning should trigger
        rows = [
            {
                'timestamp': datetime(2025, 1, i),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            }
            for i in range(1, 11)
        ]
        rows.append({
            'timestamp': datetime(2025, 1, 11),
            'open': 112,
            'high': 118,
            'low': 110,
            'close': 115,
            'volume': 60000
        })
        df = pd.DataFrame(rows)
        warnings = validator.detect_volume_anomalies(df)
        assert len(warnings) >= 1
        assert warnings[0].timestamp == datetime(2025, 1, 11)
        assert 'volume' in warnings[0].message.lower()


class TestTimestampIntegrity:
    """Test timestamp integrity checks"""

    @pytest.fixture
    def validator(self):
        return OHLCVValidator()

    def test_valid_timestamps(self, validator):
        """Test unique sorted timestamps pass validation"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 102,
                'high': 108,
                'low': 100,
                'close': 106,
                'volume': 1200
            }
        ])
        errors = validator.check_timestamp_integrity(df)
        assert len(errors) == 0

    def test_duplicate_timestamp_detected(self, validator):
        """Test detection of duplicate timestamps"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 1),  # Duplicate
                'open': 102,
                'high': 108,
                'low': 100,
                'close': 106,
                'volume': 1200
            }
        ])
        errors = validator.check_timestamp_integrity(df)
        assert len(errors) >= 1
        assert any('duplicate' in e.message.lower() for e in errors)


class TestQualityScore:
    """Test quality score calculation"""

    @pytest.fixture
    def validator(self):
        return OHLCVValidator()

    def test_quality_score_calculation(self, validator):
        """Test quality score based on errors and warnings"""
        # Perfect data: score = 100
        assert validator.calculate_quality_score([], []) == 100.0

        # 1 error: score reduced
        errors = [ValidationError(datetime(2025, 1, 1), 'open', 'Invalid price', 'ERROR')]
        score_with_error = validator.calculate_quality_score(errors, [])
        assert 0 <= score_with_error < 100

        # 1 warning: score reduced less than error
        warnings = [ValidationWarning(datetime(2025, 1, 1), 'volume', 'Volume spike', 'WARNING')]
        score_with_warning = validator.calculate_quality_score([], warnings)
        assert score_with_error < score_with_warning < 100

        # Multiple errors: lower score
        errors_multiple = [
            ValidationError(datetime(2025, 1, 1), 'open', 'Invalid', 'ERROR'),
            ValidationError(datetime(2025, 1, 2), 'high', 'Invalid', 'ERROR')
        ]
        score_multiple = validator.calculate_quality_score(errors_multiple, [])
        assert score_multiple < score_with_error


class TestValidateMethod:
    """Test main validate method that runs all checks"""

    @pytest.fixture
    def validator(self):
        return OHLCVValidator()

    def test_validate_perfect_data(self, validator):
        """Test validation of perfect data"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 102,
                'high': 108,
                'low': 100,
                'close': 106,
                'volume': 1200
            }
        ])
        result = validator.validate(df)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.quality_score == 100.0
        assert len(result.errors) == 0
        assert result.checked_rows == 2

    def test_validate_data_with_errors(self, validator):
        """Test validation of data with errors"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 99,  # Invalid: high < close
                'low': 95,
                'close': 102,
                'volume': 1000
            }
        ])
        result = validator.validate(df)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.quality_score < 100
        assert result.checked_rows == 1
