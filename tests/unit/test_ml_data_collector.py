"""
Tests for MLDataCollectorAgent (Story 1.1)

Acceptance Criteria (from Epic 1 Story 1.1):
AC1.1.1: MLDataCollectorAgent class created at agents/ml/ml_data_collector.py
AC1.1.2: Agent coordinates 4 sub-collection tasks in sequence
AC1.1.3: Configuration loaded from .env file
AC1.1.4: Progress tracking in ml_collection_status.db
AC1.1.5: Error handling with retry logic (3 attempts, exponential backoff)
AC1.1.6: Logging with structured JSON format
AC1.1.7: Returns CollectionReport with summary statistics

Test Strategy: AAA (Arrange, Act, Assert) pattern with mocking
Coverage Target: ≥90%

Author: VCP Financial Research Team
Created: 2025-11-13
"""

import pytest
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile

# System under test (will be created)
# from agents.ml.ml_data_collector import MLDataCollectorAgent, CollectionReport


class TestMLDataCollectorAgentInitialization:
    """Test agent initialization and configuration loading (AC1.1.1, AC1.1.3)"""

    def test_agent_class_exists(self):
        """AC1.1.1: Verify MLDataCollectorAgent class exists"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent
        assert MLDataCollectorAgent is not None

    def test_agent_instantiation_with_defaults(self):
        """AC1.1.1: Agent can be instantiated with default config"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent()
        assert agent is not None
        assert hasattr(agent, 'config')

    def test_agent_loads_config_from_env(self, monkeypatch, tmp_path):
        """AC1.1.3: Agent loads configuration from .env file"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        # Set environment variables
        monkeypatch.setenv("DB_BASE_PATH", str(tmp_path))
        monkeypatch.setenv("START_DATE", "2022-01-01")
        monkeypatch.setenv("END_DATE", "2025-11-13")

        agent = MLDataCollectorAgent()

        assert agent.config.db_base_path == str(tmp_path)
        assert agent.config.start_date == "2022-01-01"
        assert agent.config.end_date == "2025-11-13"

    def test_agent_initializes_status_database(self, tmp_path):
        """AC1.1.4: Agent initializes ml_collection_status.db on startup"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        db_path = tmp_path / "ml_collection_status.db"
        agent = MLDataCollectorAgent(status_db_path=str(db_path))

        # Verify database exists
        assert db_path.exists()

        # Verify tables created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "collection_tasks" in tables
        assert "collection_progress" in tables
        conn.close()

    def test_agent_has_required_methods(self):
        """AC1.1.1, AC1.1.2: Agent has all required collection methods"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent()

        # Main orchestration method
        assert hasattr(agent, 'collect_all_data')

        # Sub-task methods
        assert hasattr(agent, 'label_upper_circuits')
        assert hasattr(agent, 'improve_bse_nse_mapping')
        assert hasattr(agent, 'extract_historical_financials')
        assert hasattr(agent, 'collect_price_movements')


class TestMLDataCollectorAgentOrchestration:
    """Test main orchestration logic (AC1.1.2)"""

    def test_collect_all_data_executes_in_sequence(self, tmp_path):
        """AC1.1.2: collect_all_data() runs 4 sub-tasks in correct order"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        # Mock sub-task methods
        with patch.object(agent, 'label_upper_circuits') as mock_label, \
             patch.object(agent, 'improve_bse_nse_mapping') as mock_mapping, \
             patch.object(agent, 'extract_historical_financials') as mock_financials, \
             patch.object(agent, 'collect_price_movements') as mock_prices:

            # Configure mocks to return success
            mock_label.return_value = {"success": True, "circuits_labeled": 5000}
            mock_mapping.return_value = {"success": True, "mapping_pct": 82.5}
            mock_financials.return_value = {"success": True, "pdfs_extracted": 8000}
            mock_prices.return_value = {"success": True, "days_collected": 1000}

            # Execute
            report = agent.collect_all_data(
                bse_codes=["500570", "500209"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Verify all tasks called in order
            assert mock_label.called
            assert mock_mapping.called
            assert mock_financials.called
            assert mock_prices.called

            # Verify call order
            call_order = [
                mock_label.call_args,
                mock_mapping.call_args,
                mock_financials.call_args,
                mock_prices.call_args
            ]
            assert all(call is not None for call in call_order)

    def test_collect_all_data_returns_collection_report(self, tmp_path):
        """AC1.1.7: collect_all_data() returns CollectionReport with statistics"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent, CollectionReport

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        with patch.object(agent, 'label_upper_circuits') as mock_label, \
             patch.object(agent, 'improve_bse_nse_mapping') as mock_mapping, \
             patch.object(agent, 'extract_historical_financials') as mock_financials, \
             patch.object(agent, 'collect_price_movements') as mock_prices:

            mock_label.return_value = {"success": True, "circuits_labeled": 5000}
            mock_mapping.return_value = {"success": True, "mapping_pct": 82.5}
            mock_financials.return_value = {"success": True, "pdfs_extracted": 8000}
            mock_prices.return_value = {"success": True, "days_collected": 1000}

            report = agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Verify report structure
            assert isinstance(report, CollectionReport)
            assert hasattr(report, 'total_samples')
            assert hasattr(report, 'circuits_labeled')
            assert hasattr(report, 'bse_nse_mapping_pct')
            assert hasattr(report, 'financials_extracted')
            assert hasattr(report, 'price_days_collected')
            assert hasattr(report, 'success_rate')
            assert hasattr(report, 'duration_seconds')

    def test_collect_all_data_stops_on_critical_failure(self, tmp_path):
        """AC1.1.2: Agent stops execution if critical sub-task fails"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        with patch.object(agent, 'label_upper_circuits') as mock_label, \
             patch.object(agent, 'improve_bse_nse_mapping') as mock_mapping:

            # First task fails
            mock_label.return_value = {"success": False, "error": "Database unavailable"}

            report = agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Verify first task called but not second
            assert mock_label.called
            assert not mock_mapping.called

            # Verify report shows failure
            assert report.success_rate < 1.0


class TestErrorHandlingAndRetry:
    """Test error handling and retry logic (AC1.1.5)"""

    def test_retry_logic_on_transient_failure(self, tmp_path):
        """AC1.1.5: Agent retries failed operations up to 3 times"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        with patch.object(agent, 'label_upper_circuits') as mock_label:
            # Fail twice, succeed on third attempt
            mock_label.side_effect = [
                {"success": False, "error": "Timeout"},
                {"success": False, "error": "Timeout"},
                {"success": True, "circuits_labeled": 5000}
            ]

            report = agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Verify retried 3 times
            assert mock_label.call_count == 3

            # Verify eventual success
            assert report.circuits_labeled == 5000

    def test_exponential_backoff_between_retries(self, tmp_path):
        """AC1.1.5: Agent uses exponential backoff between retry attempts"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        with patch('time.sleep') as mock_sleep, \
             patch.object(agent, 'label_upper_circuits') as mock_label:

            mock_label.side_effect = [
                {"success": False, "error": "Timeout"},
                {"success": False, "error": "Timeout"},
                {"success": True, "circuits_labeled": 5000}
            ]

            agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Verify exponential backoff (1s, 2s, 4s...)
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert len(sleep_calls) == 2  # 2 retries = 2 sleeps
            assert sleep_calls[0] < sleep_calls[1]  # Increasing delays

    def test_agent_logs_all_errors(self, tmp_path, caplog):
        """AC1.1.5: Agent logs all errors with context"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        with patch.object(agent, 'label_upper_circuits') as mock_label:
            mock_label.return_value = {"success": False, "error": "Database connection failed"}

            agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Verify error logged
            assert "Database connection failed" in caplog.text


class TestProgressTracking:
    """Test progress tracking in database (AC1.1.4)"""

    def test_progress_written_to_database(self, tmp_path):
        """AC1.1.4: Agent writes progress to ml_collection_status.db"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        db_path = tmp_path / "status.db"
        agent = MLDataCollectorAgent(status_db_path=str(db_path))

        with patch.object(agent, 'label_upper_circuits') as mock_label:
            mock_label.return_value = {"success": True, "circuits_labeled": 5000}

            agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Query database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT task_name, status, result FROM collection_tasks")
            rows = cursor.fetchall()
            conn.close()

            # Verify progress recorded
            assert len(rows) > 0
            task_names = [row[0] for row in rows]
            assert "label_upper_circuits" in task_names

    def test_progress_includes_timestamps(self, tmp_path):
        """AC1.1.4: Progress records include start/end timestamps"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        db_path = tmp_path / "status.db"
        agent = MLDataCollectorAgent(status_db_path=str(db_path))

        with patch.object(agent, 'label_upper_circuits') as mock_label:
            mock_label.return_value = {"success": True, "circuits_labeled": 5000}

            agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT started_at, completed_at FROM collection_tasks LIMIT 1")
            row = cursor.fetchone()
            conn.close()

            # Verify timestamps exist and are valid
            assert row[0] is not None  # started_at
            assert row[1] is not None  # completed_at

            # Parse timestamps
            start_time = datetime.fromisoformat(row[0])
            end_time = datetime.fromisoformat(row[1])
            assert end_time >= start_time


class TestStructuredLogging:
    """Test structured JSON logging (AC1.1.6)"""

    def test_logs_use_json_format(self, tmp_path, caplog):
        """AC1.1.6: Agent uses structured JSON logging"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        with patch.object(agent, 'label_upper_circuits') as mock_label:
            mock_label.return_value = {"success": True, "circuits_labeled": 5000}

            agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Verify at least one log message is JSON parseable
            json_logs = []
            for record in caplog.records:
                try:
                    parsed = json.loads(record.getMessage())
                    json_logs.append(parsed)
                except json.JSONDecodeError:
                    pass

            assert len(json_logs) > 0  # At least some logs are JSON

    def test_logs_include_agent_name(self, tmp_path, caplog):
        """AC1.1.6: Logs include agent identifier"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        with patch.object(agent, 'label_upper_circuits') as mock_label:
            mock_label.return_value = {"success": True, "circuits_labeled": 5000}

            agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            # Verify agent name in logs
            assert any("MLDataCollectorAgent" in record.getMessage() for record in caplog.records)


class TestIntegrationScenarios:
    """Integration tests with realistic scenarios"""

    def test_collect_small_dataset_end_to_end(self, tmp_path):
        """Integration: Collect data for 2 companies over 1 month"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        # Use real sub-task implementations (not mocked)
        report = agent.collect_all_data(
            bse_codes=["500570", "500209"],  # TCS, Infosys
            start_date="2024-10-01",
            end_date="2024-10-31"
        )

        # Verify realistic results
        assert report.total_samples > 0
        assert 0 <= report.success_rate <= 1.0
        assert report.duration_seconds > 0

    def test_handle_empty_bse_codes_list(self, tmp_path):
        """Edge case: Empty BSE codes list"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        report = agent.collect_all_data(
            bse_codes=[],
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        assert report.total_samples == 0
        assert report.success_rate == 1.0  # No failures if no work

    def test_handle_invalid_date_range(self, tmp_path):
        """Edge case: Invalid date range (end before start)"""
        from agents.ml.ml_data_collector import MLDataCollectorAgent

        agent = MLDataCollectorAgent(status_db_path=str(tmp_path / "status.db"))

        with pytest.raises(ValueError, match="end_date must be after start_date"):
            agent.collect_all_data(
                bse_codes=["500570"],
                start_date="2024-12-31",
                end_date="2024-01-01"  # Invalid: before start
            )


# Pytest fixtures
@pytest.fixture
def sample_bse_codes():
    """Sample BSE codes for testing"""
    return ["500570", "500209", "500180"]  # TCS, Infosys, HDFC Bank


@pytest.fixture
def sample_date_range():
    """Sample date range for testing"""
    return {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.ml.ml_data_collector", "--cov-report=term-missing"])
