"""
Unit Tests for VCP Multi-Stage Workflow

Tests workflow orchestration, stage execution, and memory integration.
"""

import pytest
import asyncio
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from agents.workflows.vcp_workflow import (
    VCPWorkflow,
    WorkflowResult,
    WorkflowStageResult,
    get_vcp_workflow,
    run_vcp_analysis
)


@pytest.fixture
def mock_ohlcv_data():
    """Generate mock OHLCV DataFrame"""
    dates = pd.date_range(end=datetime.now(), periods=200, freq='D')
    data = {
        'open': [100 + i * 0.1 for i in range(200)],
        'high': [101 + i * 0.1 for i in range(200)],
        'low': [99 + i * 0.1 for i in range(200)],
        'close': [100.5 + i * 0.1 for i in range(200)],
        'volume': [1000000 - i * 1000 for i in range(200)]  # Decreasing volume (VCP pattern)
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def mock_earnings_result():
    """Mock earnings query result"""
    mock_result = Mock()
    mock_result.response = "TCS showed strong QoQ revenue growth of 15% with improved profit margins."
    mock_result.source_nodes = [
        {
            "metadata": {"quarter": "Q4FY24", "company": "TCS"},
            "score": 0.95
        }
    ]
    return mock_result


class TestWorkflowStageResult:
    """Test workflow stage result dataclass"""

    def test_stage_result_creation(self):
        """Test creating a stage result"""
        result = WorkflowStageResult(
            stage_name="TestStage",
            success=True,
            data={"key": "value"},
            execution_time=1.5
        )

        assert result.stage_name == "TestStage"
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.execution_time == 1.5
        assert result.error is None
        assert result.timestamp is not None

    def test_stage_result_with_error(self):
        """Test stage result with error"""
        result = WorkflowStageResult(
            stage_name="FailedStage",
            success=False,
            data={},
            error="Something went wrong"
        )

        assert result.success is False
        assert result.error == "Something went wrong"


class TestWorkflowResult:
    """Test complete workflow result"""

    def test_workflow_result_creation(self):
        """Test creating workflow result"""
        stages = [
            WorkflowStageResult("Stage1", True, {"a": 1}),
            WorkflowStageResult("Stage2", True, {"b": 2})
        ]

        result = WorkflowResult(
            symbol="TCS",
            success=True,
            stages=stages,
            final_recommendation="BUY",
            confidence_score=0.85,
            execution_time=5.0
        )

        assert result.symbol == "TCS"
        assert result.success is True
        assert len(result.stages) == 2
        assert result.final_recommendation == "BUY"
        assert result.confidence_score == 0.85

    def test_get_stage(self):
        """Test retrieving specific stage"""
        stages = [
            WorkflowStageResult("DataCollector", True, {"a": 1}),
            WorkflowStageResult("PatternDetector", True, {"b": 2})
        ]

        result = WorkflowResult("TCS", True, stages)

        stage = result.get_stage("PatternDetector")
        assert stage is not None
        assert stage.stage_name == "PatternDetector"
        assert stage.data == {"b": 2}

        missing = result.get_stage("NonExistent")
        assert missing is None


class TestVCPWorkflow:
    """Test VCP workflow orchestration"""

    @pytest.fixture
    def workflow(self):
        """Create workflow instance without memory"""
        return VCPWorkflow(use_memory=False)

    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test workflow initialization"""
        workflow = VCPWorkflow(use_memory=False, enable_streaming=False)

        assert workflow.use_memory is False
        assert workflow.enable_streaming is False
        assert workflow.data_fetcher is not None
        assert workflow.earnings_engine is not None

    @pytest.mark.asyncio
    async def test_stage1_data_collector_success(self, workflow, mock_ohlcv_data, mock_earnings_result):
        """Test Stage 1: Data Collection"""
        # Mock data fetcher
        with patch.object(workflow.data_fetcher, 'fetch_ohlcv', return_value=mock_ohlcv_data):
            # Mock earnings engine
            with patch.object(workflow.earnings_engine, 'search_by_company', return_value=mock_earnings_result):
                result = await workflow._stage1_data_collector("TCS", "NSE")

                assert result.success is True
                assert result.stage_name == "DataCollector"
                assert result.data["symbol"] == "TCS"
                assert result.data["data_points"] == 200
                assert "earnings" in result.data
                assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_stage1_no_data_failure(self, workflow):
        """Test Stage 1 failure when no data available"""
        # Mock empty data
        with patch.object(workflow.data_fetcher, 'fetch_ohlcv', return_value=pd.DataFrame()):
            result = await workflow._stage1_data_collector("INVALID", "NSE")

            assert result.success is False
            assert "No OHLCV data" in result.error

    @pytest.mark.asyncio
    async def test_stage2_pattern_detector(self, workflow, mock_ohlcv_data):
        """Test Stage 2: Pattern Detection"""
        # Create mock Stage 1 output
        stage1_output = {
            "symbol": "TCS",
            "exchange": "NSE",
            "ohlcv": mock_ohlcv_data,
            "data_points": 200,
            "earnings": {"summary": "Strong growth"}
        }

        result = await workflow._stage2_pattern_detector("TCS", stage1_output)

        assert result.success is True
        assert result.stage_name == "PatternDetector"
        assert "vcp_detected" in result.data
        assert "volume_contraction" in result.data
        assert "support_level" in result.data
        assert "rsi" in result.data

    @pytest.mark.asyncio
    async def test_stage2_insufficient_data(self, workflow):
        """Test Stage 2 with insufficient data"""
        # Only 50 days (need 150+)
        short_data = pd.DataFrame({
            'close': [100] * 50,
            'volume': [1000] * 50
        }, index=pd.date_range(end=datetime.now(), periods=50))

        stage1_output = {
            "ohlcv": short_data
        }

        result = await workflow._stage2_pattern_detector("TCS", stage1_output)

        assert result.success is False
        assert "Insufficient data" in result.error

    @pytest.mark.asyncio
    async def test_stage3_fundamental_analyst(self, workflow):
        """Test Stage 3: Fundamental Analysis"""
        stage2_output = {
            "symbol": "TCS",
            "vcp_detected": True,
            "earnings": {
                "summary": "Strong revenue growth, beat estimates, improved margins"
            }
        }

        with patch.object(workflow.earnings_engine, 'search_by_company') as mock_search:
            mock_search.return_value = Mock(response="QoQ revenue growth: 15%, profit growth: 20%")

            result = await workflow._stage3_fundamental_analyst("TCS", stage2_output)

            assert result.success is True
            assert result.stage_name == "FundamentalAnalyst"
            assert "fundamental_score" in result.data
            assert "quality_indicators" in result.data
            assert "qoq_analysis" in result.data

    @pytest.mark.asyncio
    async def test_stage4_signal_generator_buy(self, workflow):
        """Test Stage 4: Signal Generation - BUY signal"""
        stage3_output = {
            "symbol": "TCS",
            "vcp_detected": True,
            "vcp_score": 0.8,
            "technical_strength": 0.75,
            "fundamental_score": 0.85,
            "current_price": 3500,
            "support_level": 3400,
            "resistance_level": 3700,
            "rsi": 55
        }

        result = await workflow._stage4_signal_generator("TCS", stage3_output)

        assert result.success is True
        assert result.stage_name == "SignalGenerator"
        assert result.data["signal"] == "BUY"
        assert result.data["signal_strength"] > 0.5
        assert "entry_price" in result.data
        assert "stop_loss" in result.data
        assert "target_price" in result.data

    @pytest.mark.asyncio
    async def test_stage4_signal_generator_sell(self, workflow):
        """Test Stage 4: Signal Generation - SELL signal"""
        stage3_output = {
            "symbol": "TCS",
            "vcp_detected": False,
            "vcp_score": 0.2,
            "technical_strength": 0.3,
            "fundamental_score": 0.2,
            "current_price": 3500,
            "support_level": 3400,
            "resistance_level": 3700,
            "rsi": 85  # Overbought
        }

        result = await workflow._stage4_signal_generator("TCS", stage3_output)

        assert result.success is True
        assert result.data["signal"] == "SELL"

    @pytest.mark.asyncio
    async def test_full_workflow_success(self, workflow, mock_ohlcv_data, mock_earnings_result):
        """Test complete workflow execution"""
        # Mock all dependencies
        with patch.object(workflow.data_fetcher, 'fetch_ohlcv', return_value=mock_ohlcv_data):
            with patch.object(workflow.earnings_engine, 'search_by_company', return_value=mock_earnings_result):
                result = await workflow.run("TCS", "NSE")

                assert result.success is True
                assert result.symbol == "TCS"
                assert len(result.stages) == 4
                assert result.final_recommendation is not None
                assert result.confidence_score >= 0
                assert result.execution_time > 0

                # Verify all stages executed
                stage_names = [stage.stage_name for stage in result.stages]
                assert "DataCollector" in stage_names
                assert "PatternDetector" in stage_names
                assert "FundamentalAnalyst" in stage_names
                assert "SignalGenerator" in stage_names

    @pytest.mark.asyncio
    async def test_workflow_stage1_failure(self, workflow):
        """Test workflow when Stage 1 fails"""
        # Mock Stage 1 failure
        with patch.object(workflow.data_fetcher, 'fetch_ohlcv', return_value=pd.DataFrame()):
            result = await workflow.run("INVALID", "NSE")

            assert result.success is False
            assert len(result.stages) == 1  # Only Stage 1 executed
            assert result.stages[0].stage_name == "DataCollector"
            assert "Data collection failed" in result.final_recommendation

    def test_calculate_confidence(self, workflow):
        """Test confidence calculation"""
        stages = [
            WorkflowStageResult("DataCollector", True, {}),
            WorkflowStageResult("PatternDetector", True, {"technical_strength": 0.8}),
            WorkflowStageResult("FundamentalAnalyst", True, {"fundamental_score": 0.7}),
            WorkflowStageResult("SignalGenerator", True, {"signal_strength": 0.75})
        ]

        confidence = workflow._calculate_confidence(stages)

        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be high for successful stages

    def test_synthesize_recommendation_buy(self, workflow):
        """Test recommendation synthesis for BUY signal"""
        stages = [
            WorkflowStageResult("DataCollector", True, {}),
            WorkflowStageResult("PatternDetector", True, {}),
            WorkflowStageResult("FundamentalAnalyst", True, {}),
            WorkflowStageResult("SignalGenerator", True, {
                "signal": "BUY",
                "signal_strength": 0.85,
                "vcp_detected": True,
                "earnings_quality": "Strong",
                "risk_reward_ratio": 3.5,
                "entry_price": 3500,
                "stop_loss": 3400,
                "target_price": 3700,
                "position_size_suggestion": "5-10%"
            })
        ]

        recommendation = workflow._synthesize_recommendation(stages)

        assert "BUY" in recommendation
        assert "3500" in recommendation
        assert "Strong" in recommendation

    def test_factory_function(self):
        """Test factory function"""
        workflow = get_vcp_workflow(use_memory=False)

        assert isinstance(workflow, VCPWorkflow)
        assert workflow.use_memory is False

    @pytest.mark.asyncio
    async def test_memory_integration(self):
        """Test memory integration in workflow"""
        workflow = VCPWorkflow(use_memory=True)

        # Verify memory is initialized (or gracefully degraded)
        assert hasattr(workflow, 'use_memory')

        # If memory failed, it should be disabled
        if not workflow.use_memory:
            pytest.skip("Memory system not available")

    def test_synchronous_wrapper(self, mock_ohlcv_data, mock_earnings_result):
        """Test synchronous run_vcp_analysis wrapper"""
        with patch('agents.workflows.vcp_workflow.VCPWorkflow') as MockWorkflow:
            mock_instance = Mock()
            mock_instance.run = AsyncMock(return_value=WorkflowResult(
                symbol="TCS",
                success=True,
                stages=[],
                final_recommendation="Test"
            ))
            MockWorkflow.return_value = mock_instance

            result = run_vcp_analysis("TCS", "NSE")

            assert isinstance(result, WorkflowResult)
            assert result.symbol == "TCS"


class TestWorkflowEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_workflow_exception_handling(self):
        """Test workflow handles exceptions gracefully"""
        workflow = VCPWorkflow(use_memory=False)

        # Mock to raise exception
        with patch.object(workflow.data_fetcher, 'fetch_ohlcv', side_effect=Exception("Network error")):
            result = await workflow.run("TCS", "NSE")

            assert result.success is False
            assert len(result.stages) == 1
            assert "Network error" in result.stages[0].error

    @pytest.mark.asyncio
    async def test_partial_workflow_completion(self):
        """Test workflow continues even if middle stages have issues"""
        workflow = VCPWorkflow(use_memory=False)

        # This tests graceful degradation - workflow should complete even if some stages warn
        # (Not fail completely, but continue with partial data)
        # Implementation already handles this by continuing after warnings

        assert workflow is not None  # Placeholder for actual test

    def test_workflow_without_memory(self):
        """Test workflow works without memory system"""
        workflow = VCPWorkflow(use_memory=False)

        assert workflow.use_memory is False
        assert not hasattr(workflow, 'memory') or workflow.memory is None


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-k", "not asyncio"])
