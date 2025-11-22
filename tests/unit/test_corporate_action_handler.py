"""
Tests for Corporate Action Handler

TDD Approach: RED Phase - All tests will fail initially
"""

import pytest
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from src.data.corporate_action_handler import (
    CorporateActionHandler,
    CorporateAction,
    SplitEvent
)


class TestHandlerInitialization:
    """Test handler initialization"""

    def test_handler_initialization_default(self):
        """Test handler with default storage path"""
        handler = CorporateActionHandler()
        assert handler.storage_path is not None
        assert os.path.exists(handler.storage_path)

    def test_handler_initialization_custom_storage(self, tmp_path):
        """Test handler with custom storage path"""
        custom_path = str(tmp_path / "corporate_actions")
        handler = CorporateActionHandler(storage_path=custom_path)
        assert handler.storage_path == custom_path
        assert os.path.exists(custom_path)


class TestSplitDetection:
    """Test stock split detection"""

    @pytest.fixture
    def handler(self):
        return CorporateActionHandler(storage_path=False)

    def test_no_split_detected_normal_data(self, handler):
        """Test no split detected for normal price movements"""
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
        split = handler.detect_split(df)
        assert split is None

    def test_2_for_1_split_detected(self, handler):
        """Test detection of 2:1 stock split (50% price drop)"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 1000,
                'high': 1050,
                'low': 950,
                'close': 1020,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 510,  # ~50% drop
                'high': 525,
                'low': 475,
                'close': 510,
                'volume': 2000
            }
        ])
        split = handler.detect_split(df, threshold=0.45)
        assert split is not None
        assert isinstance(split, SplitEvent)
        assert split.date == datetime(2025, 1, 2)
        assert 1.8 <= split.ratio <= 2.2  # Allow some tolerance

    def test_10_for_1_split_detected(self, handler):
        """Test detection of 10:1 stock split (90% price drop)"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 10000,
                'high': 10500,
                'low': 9500,
                'close': 10200,
                'volume': 100
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 1000,  # 90% drop
                'high': 1050,
                'low': 950,
                'close': 1020,
                'volume': 1000
            }
        ])
        split = handler.detect_split(df, threshold=0.85)
        assert split is not None
        assert 9.0 <= split.ratio <= 11.0

    def test_reverse_split_detected(self, handler):
        """Test detection of reverse split (price increase)"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 10,
                'high': 12,
                'low': 9,
                'close': 11,
                'volume': 10000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 100,  # 10x increase (1:10 reverse split)
                'high': 120,
                'low': 90,
                'close': 110,
                'volume': 1000
            }
        ])
        split = handler.detect_split(df, threshold=0.85)
        assert split is not None
        assert split.ratio < 1  # Reverse split has ratio < 1


class TestSplitAdjustment:
    """Test OHLCV adjustment for splits"""

    @pytest.fixture
    def handler(self):
        return CorporateActionHandler(storage_path=False)

    def test_adjust_prices_for_split(self, handler):
        """Test price adjustment for 2:1 split"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 1000,
                'high': 1050,
                'low': 950,
                'close': 1020,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 500,
                'high': 525,
                'low': 475,
                'close': 510,
                'volume': 2000
            }
        ])

        adjusted = handler.adjust_for_split(
            df,
            split_date=datetime(2025, 1, 2),
            split_ratio=2.0
        )

        # Pre-split prices should be divided by 2
        assert adjusted.iloc[0]['open'] == 500
        assert adjusted.iloc[0]['close'] == 510

        # Post-split prices unchanged
        assert adjusted.iloc[1]['open'] == 500
        assert adjusted.iloc[1]['close'] == 510

    def test_adjust_volume_for_split(self, handler):
        """Test volume adjustment for 2:1 split"""
        df = pd.DataFrame([
            {
                'timestamp': datetime(2025, 1, 1),
                'open': 1000,
                'high': 1050,
                'low': 950,
                'close': 1020,
                'volume': 1000
            },
            {
                'timestamp': datetime(2025, 1, 2),
                'open': 500,
                'high': 525,
                'low': 475,
                'close': 510,
                'volume': 2000
            }
        ])

        adjusted = handler.adjust_for_split(
            df,
            split_date=datetime(2025, 1, 2),
            split_ratio=2.0
        )

        # Pre-split volume should be multiplied by 2
        assert adjusted.iloc[0]['volume'] == 2000

        # Post-split volume unchanged
        assert adjusted.iloc[1]['volume'] == 2000

    def test_split_only_affects_pre_split_data(self, handler):
        """Test that split only adjusts pre-split data"""
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 1000, 'high': 1050, 'low': 950, 'close': 1020, 'volume': 1000},
            {'timestamp': datetime(2025, 1, 2), 'open': 500, 'high': 525, 'low': 475, 'close': 510, 'volume': 2000},
            {'timestamp': datetime(2025, 1, 3), 'open': 510, 'high': 520, 'low': 500, 'close': 515, 'volume': 2100},
        ])

        adjusted = handler.adjust_for_split(
            df,
            split_date=datetime(2025, 1, 2),
            split_ratio=2.0
        )

        # Only first row should be adjusted
        assert adjusted.iloc[0]['close'] == 510  # 1020 / 2
        assert adjusted.iloc[1]['close'] == 510  # unchanged
        assert adjusted.iloc[2]['close'] == 515  # unchanged

    def test_multiple_splits(self, handler):
        """Test applying multiple splits sequentially"""
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 4000, 'high': 4200, 'low': 3800, 'close': 4000, 'volume': 100},
            {'timestamp': datetime(2025, 1, 2), 'open': 2000, 'high': 2100, 'low': 1900, 'close': 2000, 'volume': 200},
            {'timestamp': datetime(2025, 1, 3), 'open': 1000, 'high': 1050, 'low': 950, 'close': 1000, 'volume': 400},
        ])

        # First split: 2:1 on Jan 2
        adjusted = handler.adjust_for_split(df, datetime(2025, 1, 2), 2.0)

        # Second split: 2:1 on Jan 3
        adjusted = handler.adjust_for_split(adjusted, datetime(2025, 1, 3), 2.0)

        # After two 2:1 splits, original price should be 1/4
        assert adjusted.iloc[0]['close'] == 1000  # 4000 / 2 / 2
        assert adjusted.iloc[0]['volume'] == 400  # 100 * 2 * 2


class TestActionRecording:
    """Test corporate action recording"""

    @pytest.fixture
    def handler(self, tmp_path):
        return CorporateActionHandler(storage_path=str(tmp_path / "actions"))

    def test_record_split_action(self, handler):
        """Test recording a split action"""
        action = CorporateAction(
            symbol="RELIANCE",
            action_type="SPLIT",
            date=datetime(2025, 1, 1),
            details={'ratio': 2.0}
        )
        handler.record_action("RELIANCE", action)

        actions = handler.get_actions("RELIANCE")
        assert len(actions) == 1
        assert actions[0].action_type == "SPLIT"
        assert actions[0].details['ratio'] == 2.0

    def test_record_bonus_action(self, handler):
        """Test recording a bonus issue"""
        action = CorporateAction(
            symbol="TCS",
            action_type="BONUS",
            date=datetime(2025, 2, 1),
            details={'ratio': 1.5}  # 3:2 bonus
        )
        handler.record_action("TCS", action)

        actions = handler.get_actions("TCS")
        assert len(actions) == 1
        assert actions[0].action_type == "BONUS"

    def test_record_dividend_action(self, handler):
        """Test recording a dividend"""
        action = CorporateAction(
            symbol="INFY",
            action_type="DIVIDEND",
            date=datetime(2025, 3, 1),
            details={'amount': 25.50}
        )
        handler.record_action("INFY", action)

        actions = handler.get_actions("INFY")
        assert len(actions) == 1
        assert actions[0].action_type == "DIVIDEND"
        assert actions[0].details['amount'] == 25.50


class TestActionRetrieval:
    """Test retrieving corporate actions"""

    @pytest.fixture
    def handler_with_data(self, tmp_path):
        handler = CorporateActionHandler(storage_path=str(tmp_path / "actions"))

        # Add multiple actions
        handler.record_action("RELIANCE", CorporateAction(
            symbol="RELIANCE",
            action_type="SPLIT",
            date=datetime(2025, 1, 1),
            details={'ratio': 2.0}
        ))
        handler.record_action("RELIANCE", CorporateAction(
            symbol="RELIANCE",
            action_type="DIVIDEND",
            date=datetime(2025, 2, 1),
            details={'amount': 10.0}
        ))
        handler.record_action("RELIANCE", CorporateAction(
            symbol="RELIANCE",
            action_type="SPLIT",
            date=datetime(2025, 3, 1),
            details={'ratio': 5.0}
        ))

        return handler

    def test_get_all_actions_for_symbol(self, handler_with_data):
        """Test retrieving all actions for a symbol"""
        actions = handler_with_data.get_actions("RELIANCE")
        assert len(actions) == 3

    def test_get_actions_in_date_range(self, handler_with_data):
        """Test retrieving actions in date range"""
        actions = handler_with_data.get_actions(
            "RELIANCE",
            from_date=datetime(2025, 1, 15),
            to_date=datetime(2025, 2, 15)
        )
        assert len(actions) == 1
        assert actions[0].action_type == "DIVIDEND"

    def test_no_actions_for_symbol(self, handler_with_data):
        """Test retrieving actions for symbol with no history"""
        actions = handler_with_data.get_actions("UNKNOWN")
        assert len(actions) == 0


class TestFullAdjustment:
    """Test applying all adjustments"""

    @pytest.fixture
    def handler_with_actions(self, tmp_path):
        handler = CorporateActionHandler(storage_path=str(tmp_path / "actions"))

        # Record a split
        handler.record_action("TCS", CorporateAction(
            symbol="TCS",
            action_type="SPLIT",
            date=datetime(2025, 1, 15),
            details={'ratio': 2.0}
        ))

        return handler

    def test_apply_single_adjustment(self, handler_with_actions):
        """Test applying single recorded adjustment"""
        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 2000, 'high': 2100, 'low': 1900, 'close': 2000, 'volume': 100},
            {'timestamp': datetime(2025, 1, 20), 'open': 1000, 'high': 1050, 'low': 950, 'close': 1000, 'volume': 200},
        ])

        adjusted = handler_with_actions.apply_all_adjustments("TCS", df)

        # Pre-split price should be adjusted
        assert adjusted.iloc[0]['close'] == 1000  # 2000 / 2

    def test_apply_multiple_adjustments(self, tmp_path):
        """Test applying multiple recorded adjustments"""
        handler = CorporateActionHandler(storage_path=str(tmp_path / "actions2"))

        # Record two splits
        handler.record_action("RELIANCE", CorporateAction(
            symbol="RELIANCE",
            action_type="SPLIT",
            date=datetime(2025, 1, 15),
            details={'ratio': 2.0}
        ))
        handler.record_action("RELIANCE", CorporateAction(
            symbol="RELIANCE",
            action_type="SPLIT",
            date=datetime(2025, 2, 15),
            details={'ratio': 2.0}
        ))

        df = pd.DataFrame([
            {'timestamp': datetime(2025, 1, 1), 'open': 4000, 'high': 4200, 'low': 3800, 'close': 4000, 'volume': 100},
            {'timestamp': datetime(2025, 1, 20), 'open': 2000, 'high': 2100, 'low': 1900, 'close': 2000, 'volume': 200},
            {'timestamp': datetime(2025, 2, 20), 'open': 1000, 'high': 1050, 'low': 950, 'close': 1000, 'volume': 400},
        ])

        adjusted = handler.apply_all_adjustments("RELIANCE", df)

        # After two 2:1 splits, original price should be 1/4
        assert adjusted.iloc[0]['close'] == 1000  # 4000 / 2 / 2
        assert adjusted.iloc[0]['volume'] == 400  # 100 * 2 * 2
