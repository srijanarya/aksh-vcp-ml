"""
Unit Tests for Phase 4: Observability (Phoenix + AgentOps)

Tests:
- Phoenix RAG monitoring
- AgentOps workflow tracking
- Unified monitoring interface
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.observability import (
    start_monitoring,
    monitor_workflow,
    get_monitoring_status,
    stop_monitoring
)

from src.observability.phoenix_monitor import (
    PhoenixMonitor,
    start_phoenix_monitoring,
    get_phoenix_monitor
)

from src.observability.agentops_monitor import (
    AgentOpsMonitor,
    init_agentops,
    get_agentops_monitor
)


class TestPhoenixMonitor:
    """Test Phoenix RAG monitoring"""

    def test_phoenix_initialization_without_library(self):
        """Test Phoenix initialization when library not installed"""
        with patch('src.observability.phoenix_monitor.PHOENIX_AVAILABLE', False):
            monitor = PhoenixMonitor()

            assert monitor.enabled is False
            assert not monitor.is_enabled

    @pytest.mark.skip(reason="Requires actual Phoenix library - tested in integration")
    def test_phoenix_initialization_success(self):
        """Test successful Phoenix initialization (requires Phoenix library)"""
        # This test requires actual Phoenix library installation
        # Tested in integration tests with proper setup
        pass

    @patch('src.observability.phoenix_monitor.PHOENIX_AVAILABLE', True)
    @patch('src.observability.phoenix_monitor.px')
    def test_phoenix_initialization_failure(self, mock_px):
        """Test Phoenix initialization failure handling"""
        mock_px.launch_app.side_effect = Exception("Launch failed")

        monitor = PhoenixMonitor()

        assert monitor.enabled is False

    def test_trace_rag_query_disabled(self):
        """Test RAG query tracing when Phoenix is disabled"""
        monitor = PhoenixMonitor()
        monitor.enabled = False

        # Should not raise exception
        with monitor.trace_rag_query("test query"):
            pass

    def test_trace_rag_query_enabled(self):
        """Test RAG query tracing when Phoenix is enabled"""
        monitor = PhoenixMonitor()
        monitor.enabled = True
        monitor.project_name = "test"

        # Should not raise exception even when tracing is enabled
        with monitor.trace_rag_query("test query", {"key": "value"}):
            pass

    def test_get_dashboard_url_disabled(self):
        """Test dashboard URL when disabled"""
        monitor = PhoenixMonitor()
        monitor.enabled = False

        url = monitor.get_dashboard_url()

        assert "not available" in url.lower()

    def test_get_dashboard_url_enabled(self):
        """Test dashboard URL when enabled"""
        monitor = PhoenixMonitor()
        monitor.enabled = True

        url = monitor.get_dashboard_url()

        assert "localhost:6006" in url

    def test_stop_monitoring(self):
        """Test stopping Phoenix monitoring"""
        monitor = PhoenixMonitor()
        monitor._session = Mock()

        monitor.stop()

        monitor._session.stop.assert_called_once()

    def test_singleton_phoenix_monitor(self):
        """Test singleton pattern"""
        with patch('src.observability.phoenix_monitor._phoenix_monitor_instance', None):
            monitor1 = start_phoenix_monitoring("project1")
            monitor2 = start_phoenix_monitoring("project2")

            # Should return same instance
            assert monitor1 is monitor2


class TestAgentOpsMonitor:
    """Test AgentOps workflow monitoring"""

    def test_agentops_initialization_without_library(self):
        """Test AgentOps initialization when library not installed"""
        with patch('src.observability.agentops_monitor.AGENTOPS_AVAILABLE', False):
            monitor = AgentOpsMonitor()

            assert monitor.enabled is False
            assert not monitor.is_enabled

    def test_agentops_initialization_without_api_key(self):
        """Test AgentOps initialization without API key"""
        with patch('src.observability.agentops_monitor.AGENTOPS_AVAILABLE', True):
            with patch.dict('os.environ', {}, clear=True):
                monitor = AgentOpsMonitor()

                assert monitor.enabled is False

    @patch('src.observability.agentops_monitor.AGENTOPS_AVAILABLE', True)
    @patch('src.observability.agentops_monitor.agentops')
    def test_agentops_initialization_success(self, mock_agentops):
        """Test successful AgentOps initialization"""
        monitor = AgentOpsMonitor(api_key="test-key", tags=["test"])

        assert monitor.enabled is True
        mock_agentops.init.assert_called_once()

    @patch('src.observability.agentops_monitor.AGENTOPS_AVAILABLE', True)
    @patch('src.observability.agentops_monitor.agentops')
    def test_agentops_initialization_failure(self, mock_agentops):
        """Test AgentOps initialization failure handling"""
        mock_agentops.init.side_effect = Exception("Init failed")

        monitor = AgentOpsMonitor(api_key="test-key")

        assert monitor.enabled is False

    def test_start_workflow_disabled(self):
        """Test workflow start when disabled"""
        monitor = AgentOpsMonitor()
        monitor.enabled = False

        # Should not raise exception
        monitor.start_workflow("test-workflow")

    @patch('src.observability.agentops_monitor.AGENTOPS_AVAILABLE', True)
    @patch('src.observability.agentops_monitor.agentops')
    def test_start_workflow_enabled(self, mock_agentops):
        """Test workflow start when enabled"""
        monitor = AgentOpsMonitor(api_key="test-key")
        monitor.enabled = True
        monitor.session = mock_agentops

        monitor.start_workflow("test-workflow", {"symbol": "TCS"})

        mock_agentops.record.assert_called_once()

    def test_record_agent_action_disabled(self):
        """Test agent action recording when disabled"""
        monitor = AgentOpsMonitor()
        monitor.enabled = False

        # Should not raise exception
        monitor.record_agent_action("test-agent", "test-action")

    @patch('src.observability.agentops_monitor.AGENTOPS_AVAILABLE', True)
    @patch('src.observability.agentops_monitor.agentops')
    def test_record_agent_action_enabled(self, mock_agentops):
        """Test agent action recording when enabled"""
        monitor = AgentOpsMonitor(api_key="test-key")
        monitor.enabled = True
        monitor.session = mock_agentops

        monitor.record_agent_action("test-agent", "analyze", {"score": 0.8})

        mock_agentops.record.assert_called_once()

    def test_end_workflow_disabled(self):
        """Test workflow end when disabled"""
        monitor = AgentOpsMonitor()
        monitor.enabled = False

        # Should not raise exception
        monitor.end_workflow("test-workflow", "Success")

    @patch('src.observability.agentops_monitor.AGENTOPS_AVAILABLE', True)
    @patch('src.observability.agentops_monitor.agentops')
    def test_end_workflow_enabled(self, mock_agentops):
        """Test workflow end when enabled"""
        monitor = AgentOpsMonitor(api_key="test-key")
        monitor.enabled = True
        monitor.session = mock_agentops

        monitor.end_workflow("test-workflow", "Success", {"duration": 5.2})

        mock_agentops.end_session.assert_called_once()


class TestUnifiedMonitoring:
    """Test unified monitoring interface"""

    @patch('src.observability.start_phoenix_monitoring')
    @patch('src.observability.init_agentops')
    def test_start_monitoring_all(self, mock_init_agentops, mock_start_phoenix):
        """Test starting all monitoring systems"""
        mock_phoenix = Mock()
        mock_phoenix.is_enabled = True
        mock_phoenix.get_dashboard_url.return_value = "http://localhost:6006"
        mock_start_phoenix.return_value = mock_phoenix

        mock_agentops = Mock()
        mock_agentops.is_enabled = True
        mock_init_agentops.return_value = mock_agentops

        status = start_monitoring(enable_phoenix=True, enable_agentops=True)

        assert status["phoenix"]["enabled"] is True
        assert status["phoenix"]["url"] == "http://localhost:6006"
        assert status["agentops"]["enabled"] is True

    @patch('src.observability.start_phoenix_monitoring')
    def test_start_monitoring_phoenix_only(self, mock_start_phoenix):
        """Test starting only Phoenix monitoring"""
        mock_phoenix = Mock()
        mock_phoenix.is_enabled = True
        mock_phoenix.get_dashboard_url.return_value = "http://localhost:6006"
        mock_start_phoenix.return_value = mock_phoenix

        status = start_monitoring(enable_phoenix=True, enable_agentops=False)

        assert status["phoenix"]["enabled"] is True
        assert status["agentops"]["enabled"] is False

    @patch('src.observability.get_agentops_monitor')
    @patch('src.observability.get_phoenix_monitor')
    def test_monitor_workflow_success(self, mock_get_phoenix, mock_get_agentops):
        """Test workflow monitoring context manager - success case"""
        mock_agentops = Mock()
        mock_agentops.is_enabled = True
        mock_get_agentops.return_value = mock_agentops

        mock_phoenix = Mock()
        mock_phoenix.is_enabled = False
        mock_get_phoenix.return_value = mock_phoenix

        with monitor_workflow("test-workflow", symbol="TCS"):
            # Workflow code
            pass

        mock_agentops.start_workflow.assert_called_once()
        mock_agentops.end_workflow.assert_called_once_with(
            "test-workflow",
            status="Success",
            metadata={"symbol": "TCS"}
        )

    @patch('src.observability.get_agentops_monitor')
    @patch('src.observability.get_phoenix_monitor')
    def test_monitor_workflow_failure(self, mock_get_phoenix, mock_get_agentops):
        """Test workflow monitoring context manager - failure case"""
        mock_agentops = Mock()
        mock_agentops.is_enabled = True
        mock_get_agentops.return_value = mock_agentops

        mock_phoenix = Mock()
        mock_phoenix.is_enabled = False
        mock_get_phoenix.return_value = mock_phoenix

        with pytest.raises(ValueError):
            with monitor_workflow("test-workflow"):
                raise ValueError("Test error")

        mock_agentops.start_workflow.assert_called_once()
        # Should record failure
        assert mock_agentops.end_workflow.called
        call_kwargs = mock_agentops.end_workflow.call_args[1]
        assert call_kwargs["status"] == "Fail"

    @patch('src.observability.get_phoenix_monitor')
    @patch('src.observability.get_agentops_monitor')
    def test_get_monitoring_status(self, mock_get_agentops, mock_get_phoenix):
        """Test getting monitoring status"""
        mock_phoenix = Mock()
        mock_phoenix.is_enabled = True
        mock_phoenix.get_dashboard_url.return_value = "http://localhost:6006"
        mock_get_phoenix.return_value = mock_phoenix

        mock_agentops = Mock()
        mock_agentops.is_enabled = False
        mock_get_agentops.return_value = mock_agentops

        status = get_monitoring_status()

        assert status["phoenix"]["enabled"] is True
        assert status["phoenix"]["url"] == "http://localhost:6006"
        assert status["agentops"]["enabled"] is False

    @patch('src.observability.stop_phoenix_monitoring')
    def test_stop_monitoring(self, mock_stop_phoenix):
        """Test stopping all monitoring"""
        stop_monitoring()

        mock_stop_phoenix.assert_called_once()


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
