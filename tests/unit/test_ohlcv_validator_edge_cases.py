"""
Additional tests for OHLCV Validator edge cases to reach 100% coverage
"""

import pytest
import pandas as pd
from datetime import datetime
from src.data.ohlcv_validator import OHLCVValidator


class TestEdgeCases:
    """Test edge cases for 100% coverage"""

    @pytest.fixture
    def validator(self):
        return OHLCVValidator()

    def test_high_less_than_low(self, validator):
        """Test detection of high < low edge case"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 95,  # Invalid: high < low
                'low': 98,
                'close': 97,
                'volume': 1000
            }
        ])
        errors = validator.check_ohlc_relationships(df)
        # Should have multiple errors including high < low
        assert len(errors) > 0
        assert any(e.field == 'high' and 'low' in e.message.lower() for e in errors)

    def test_zero_volume_no_warnings(self, validator):
        """Test that zero average volume doesn't trigger warnings"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 100,
                'high': 105,
                'low': 95,
                'close': 102,
                'volume': 0
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 102,
                'high': 108,
                'low': 100,
                'close': 106,
                'volume': 0
            }
        ])
        warnings = validator.detect_volume_anomalies(df)
        assert len(warnings) == 0
