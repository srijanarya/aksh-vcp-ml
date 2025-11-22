"""
Edge cases for Corporate Action Handler to reach 100% coverage
"""

import pytest
import pandas as pd
from datetime import datetime
from src.data.corporate_action_handler import CorporateActionHandler


class TestEdgeCases:
    """Test edge cases for 100% coverage"""

    def test_detect_split_single_row(self):
        """Test split detection with single row (should return None)"""
        handler = CorporateActionHandler(storage_path=False)
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 1000, 'high': 1050, 'low': 950, 'close': 1020, 'volume': 1000}
        ])
        split = handler.detect_split(df)
        assert split is None

    def test_record_action_storage_disabled(self):
        """Test recording action with storage disabled"""
        handler = CorporateActionHandler(storage_path=False)
        from src.data.corporate_action_handler import CorporateAction

        action = CorporateAction(
            symbol="TEST",
            action_type="SPLIT",
            date=datetime(2025, 1, 1),
            details={'ratio': 2.0}
        )

        # Should not raise error, just log warning
        handler.record_action("TEST", action)

        # Verify no actions stored (storage disabled)
        actions = handler.get_actions("TEST")
        assert len(actions) == 0

    def test_get_actions_storage_disabled(self):
        """Test getting actions with storage disabled"""
        handler = CorporateActionHandler(storage_path=False)
        actions = handler.get_actions("ANY_SYMBOL")
        assert len(actions) == 0
