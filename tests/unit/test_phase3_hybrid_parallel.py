"""
Unit Tests for Phase 3: Hybrid Search + Parallel Analysis

Tests:
- Hybrid search engine (local + web)
- Parallel financial analysis
- Integration and performance
"""

import pytest
import asyncio
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.rag.hybrid_search import (
    HybridSearchEngine,
    HybridSearchResult,
    get_hybrid_search_engine,
    hybrid_search
)

from agents.workflows.parallel_analysis import (
    ParallelFinancialAnalyzer,
    ParallelAnalysisResult,
    AnalysisResult,
    run_parallel_analysis
)


class TestHybridSearchEngine:
    """Test hybrid search combining local RAG + web"""

    @pytest.fixture
    def mock_local_result(self):
        """Mock local RAG result"""
        mock = Mock()
        mock.response = "TCS showed strong QoQ revenue growth of 15%"
        mock.source_nodes = [{"score": 0.95, "metadata": {"company": "TCS"}}]
        return mock

    @pytest.fixture
    def mock_web_results(self):
        """Mock EXA web search results"""
        mock_response = Mock()
        mock_result1 = Mock()
        mock_result1.title = "TCS beats Q4 estimates"
        mock_result1.url = "https://moneycontrol.com/tcs-q4"
        mock_result1.text = "TCS reported strong quarterly results..."
        mock_result1.score = 0.9
        mock_result1.highlights = ["strong results", "beat estimates"]
        mock_result1.published_date = "2025-01-15"

        mock_response.results = [mock_result1]
        return mock_response

    def test_initialization_without_web(self):
        """Test engine initialization without web search"""
        engine = HybridSearchEngine(enable_web_search=False)

        assert engine.local_engine is not None
        assert engine.enable_web_search is False
        assert engine.exa_client is None

    @patch('src.rag.hybrid_search.get_earnings_query_engine')
    def test_initialization_with_local_only(self, mock_query_engine):
        """Test initialization with only local RAG"""
        mock_query_engine.return_value = Mock()

        engine = HybridSearchEngine(enable_web_search=False)

        assert engine.local_engine is not None
        assert not engine.enable_web_search

    @pytest.mark.asyncio
    async def test_search_local_only(self, mock_local_result):
        """Test search with local source only"""
        engine = HybridSearchEngine(enable_web_search=False)

        with patch.object(engine.local_engine, 'query', return_value=mock_local_result):
            result = await engine.search(
                "TCS earnings growth",
                sources=["local"]
            )

            assert result.query == "TCS earnings growth"
            assert result.local_results is not None
            assert result.web_results is None
            assert "local" in result.sources_used
            assert result.execution_time > 0

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires EXA API key - tested in integration")
    async def test_search_web_only(self, mock_web_results):
        """Test search with web source only (requires EXA setup)"""
        # This test is skipped because it requires actual EXA API configuration
        # Web search functionality is tested in integration tests with proper setup
        pass

    @pytest.mark.asyncio
    async def test_search_both_sources(self, mock_local_result):
        """Test search with both local and web sources"""
        engine = HybridSearchEngine(enable_web_search=False)  # Web disabled for test

        with patch.object(engine.local_engine, 'query', return_value=mock_local_result):
            result = await engine.search(
                "TCS earnings",
                sources=["both"]
            )

            assert result.local_results is not None
            assert result.combined_summary != ""

    @pytest.mark.asyncio
    async def test_search_with_filters(self, mock_local_result):
        """Test search with metadata filters"""
        engine = HybridSearchEngine(enable_web_search=False)

        with patch.object(engine.local_engine, 'query', return_value=mock_local_result):
            result = await engine.search(
                "earnings growth",
                sources=["local"],
                filters={"company": "TCS", "quarter": "Q4FY24"}
            )

            assert result.local_results is not None

    def test_synthesize_results_local_only(self, mock_local_result):
        """Test result synthesis with local only"""
        engine = HybridSearchEngine(enable_web_search=False)

        summary = engine._synthesize_results(
            "test query",
            local=mock_local_result,
            web=None
        )

        assert "test query" in summary
        assert "From Local Earnings Documents" in summary
        assert mock_local_result.response in summary

    def test_synthesize_results_web_only(self):
        """Test result synthesis with web only"""
        engine = HybridSearchEngine(enable_web_search=False)

        web_results = [
            {
                "title": "TCS News",
                "url": "https://example.com",
                "text": "TCS reported strong results",
                "highlights": ["strong", "growth"]
            }
        ]

        summary = engine._synthesize_results(
            "test query",
            local=None,
            web=web_results
        )

        assert "From Web" in summary
        assert "TCS News" in summary

    def test_synthesize_results_both_sources(self, mock_local_result):
        """Test result synthesis with both sources"""
        engine = HybridSearchEngine(enable_web_search=False)

        web_results = [{
            "title": "TCS News",
            "url": "https://example.com",
            "text": "Latest updates",
            "highlights": []
        }]

        summary = engine._synthesize_results(
            "test query",
            local=mock_local_result,
            web=web_results
        )

        assert "From Local" in summary
        assert "From Web" in summary

    def test_singleton_instance(self):
        """Test singleton pattern for hybrid engine"""
        engine1 = get_hybrid_search_engine()
        engine2 = get_hybrid_search_engine()

        assert engine1 is engine2


class TestParallelAnalysis:
    """Test parallel financial analysis"""

    @pytest.fixture
    def mock_ohlcv_data(self):
        """Generate mock OHLCV DataFrame"""
        dates = pd.date_range(end=datetime.now(), periods=250, freq='D')
        data = {
            'open': [100 + i * 0.1 for i in range(250)],
            'high': [101 + i * 0.1 for i in range(250)],
            'low': [99 + i * 0.1 for i in range(250)],
            'close': [100.5 + i * 0.1 for i in range(250)],
            'volume': [1000000 + i * 1000 for i in range(250)]
        }
        return pd.DataFrame(data, index=dates)

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return ParallelFinancialAnalyzer()

    @pytest.mark.asyncio
    async def test_technical_analysis(self, analyzer, mock_ohlcv_data):
        """Test technical analysis execution"""
        result = await analyzer._technical_analysis("TCS", mock_ohlcv_data)

        assert result.analysis_type == "technical"
        assert result.success is True
        assert 0.0 <= result.score <= 1.0
        assert "current_price" in result.data
        assert "rsi" in result.data
        assert len(result.insights) > 0
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_technical_analysis_insufficient_data(self, analyzer):
        """Test technical analysis with insufficient data"""
        short_data = pd.DataFrame({
            'close': [100] * 10,
            'volume': [1000] * 10
        })

        result = await analyzer._technical_analysis("TCS", short_data)

        assert result.success is False
        assert "Insufficient" in result.error

    @pytest.mark.asyncio
    async def test_fundamental_analysis(self, analyzer):
        """Test fundamental analysis execution"""
        # Mock hybrid search
        mock_search_result = Mock()
        mock_search_result.local_results = Mock()
        mock_search_result.local_results.response = "TCS showed strong revenue growth and improved profit margins"

        with patch.object(analyzer.hybrid_search, 'search', return_value=mock_search_result):
            result = await analyzer._fundamental_analysis("TCS", "NSE")

            assert result.analysis_type == "fundamental"
            assert result.success is True
            assert 0.0 <= result.score <= 1.0
            assert len(result.insights) > 0

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, analyzer):
        """Test sentiment analysis execution"""
        # Mock hybrid search
        mock_search_result = Mock()
        mock_search_result.web_results = [
            {
                "title": "TCS stock surges on strong growth",
                "text": "TCS reported beat earnings with strong profit growth",
                "url": "https://example.com"
            }
        ]

        with patch.object(analyzer.hybrid_search, 'search', return_value=mock_search_result):
            result = await analyzer._sentiment_analysis("TCS")

            assert result.analysis_type == "sentiment"
            assert result.success is True
            assert 0.0 <= result.score <= 1.0
            assert "news" in result.insights[0].lower() or "sentiment" in result.insights[0].lower()

    @pytest.mark.asyncio
    async def test_sentiment_analysis_negative(self, analyzer):
        """Test sentiment analysis with negative news"""
        mock_search_result = Mock()
        mock_search_result.web_results = [
            {
                "title": "TCS stock falls on weak guidance",
                "text": "TCS disappointed investors with weak outlook and declining margins",
                "url": "https://example.com"
            }
        ]

        with patch.object(analyzer.hybrid_search, 'search', return_value=mock_search_result):
            result = await analyzer._sentiment_analysis("TCS")

            assert result.success is True
            # Score should be below neutral for negative sentiment
            assert result.score < 0.6

    @pytest.mark.asyncio
    async def test_risk_analysis(self, analyzer, mock_ohlcv_data):
        """Test risk analysis execution"""
        result = await analyzer._risk_analysis("TCS", mock_ohlcv_data)

        assert result.analysis_type == "risk"
        assert result.success is True
        assert 0.0 <= result.score <= 1.0
        assert "volatility" in result.data
        assert "max_drawdown" in result.data
        assert len(result.insights) > 0

    @pytest.mark.asyncio
    async def test_parallel_analysis_all(self, analyzer, mock_ohlcv_data):
        """Test full parallel analysis with all components"""
        # Mock data fetching
        with patch.object(analyzer, '_fetch_ohlcv_data', return_value=mock_ohlcv_data):
            # Mock hybrid search for fundamental and sentiment
            mock_search_result = Mock()
            mock_search_result.local_results = Mock()
            mock_search_result.local_results.response = "Strong earnings"
            mock_search_result.web_results = [{"title": "Good news", "text": "Growth", "url": "https://example.com"}]

            with patch.object(analyzer.hybrid_search, 'search', return_value=mock_search_result):
                result = await analyzer.analyze("TCS", "NSE")

                assert result.symbol == "TCS"
                assert result.technical is not None
                assert result.fundamental is not None
                assert result.sentiment is not None
                assert result.risk is not None
                assert 0.0 <= result.combined_score <= 1.0
                assert result.recommendation in ["BUY", "HOLD", "SELL", "HOLD (Weak Buy)", "HOLD (Weak Sell)"]
                assert 0.0 <= result.confidence <= 1.0
                assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_parallel_analysis_selective(self, analyzer, mock_ohlcv_data):
        """Test parallel analysis with selective analyses"""
        with patch.object(analyzer, '_fetch_ohlcv_data', return_value=mock_ohlcv_data):
            result = await analyzer.analyze(
                "TCS",
                "NSE",
                analyses=["technical", "risk"]
            )

            assert result.technical is not None
            assert result.risk is not None
            assert result.fundamental is None
            assert result.sentiment is None

    @pytest.mark.asyncio
    async def test_parallel_execution_speed(self, analyzer, mock_ohlcv_data):
        """Test that parallel execution is actually faster"""
        with patch.object(analyzer, '_fetch_ohlcv_data', return_value=mock_ohlcv_data):
            # Mock slow analyses (100ms each)
            async def slow_analysis(*args, **kwargs):
                await asyncio.sleep(0.1)
                return AnalysisResult("test", True, 0.5)

            with patch.object(analyzer, '_technical_analysis', side_effect=slow_analysis):
                with patch.object(analyzer, '_fundamental_analysis', side_effect=slow_analysis):
                    with patch.object(analyzer, '_sentiment_analysis', side_effect=slow_analysis):
                        with patch.object(analyzer, '_risk_analysis', side_effect=slow_analysis):
                            start = datetime.now()
                            result = await analyzer.analyze("TCS", "NSE")
                            elapsed = (datetime.now() - start).total_seconds()

                            # Parallel: ~0.1s, Sequential would be ~0.4s
                            assert elapsed < 0.25, f"Parallel execution too slow: {elapsed}s"

    def test_combined_score_calculation(self, analyzer):
        """Test combined score calculation"""
        tech = AnalysisResult("technical", True, 0.8)
        fund = AnalysisResult("fundamental", True, 0.7)
        sent = AnalysisResult("sentiment", True, 0.6)
        risk = AnalysisResult("risk", True, 0.5)

        combined = analyzer._calculate_combined_score(tech, fund, sent, risk)

        assert 0.0 <= combined <= 1.0
        # Should be weighted average leaning toward tech/fundamental
        assert 0.65 < combined < 0.75

    def test_combined_score_partial_success(self, analyzer):
        """Test combined score with some failed analyses"""
        tech = AnalysisResult("technical", True, 0.8)
        fund = AnalysisResult("fundamental", False, 0.0, error="Failed")
        sent = AnalysisResult("sentiment", True, 0.6)
        risk = None

        combined = analyzer._calculate_combined_score(tech, fund, sent, risk)

        assert 0.0 <= combined <= 1.0
        # Should only use tech and sentiment

    def test_recommendation_generation_buy(self, analyzer):
        """Test BUY recommendation generation"""
        tech = AnalysisResult("technical", True, 0.85)
        fund = AnalysisResult("fundamental", True, 0.80)
        sent = AnalysisResult("sentiment", True, 0.75)
        risk = AnalysisResult("risk", True, 0.70)

        recommendation, confidence = analyzer._generate_recommendation(0.78, tech, fund, sent, risk)

        assert recommendation == "BUY"
        assert confidence > 0.7

    def test_recommendation_generation_sell(self, analyzer):
        """Test SELL recommendation generation"""
        tech = AnalysisResult("technical", True, 0.2)
        fund = AnalysisResult("fundamental", True, 0.25)
        sent = AnalysisResult("sentiment", True, 0.3)
        risk = AnalysisResult("risk", True, 0.35)

        recommendation, confidence = analyzer._generate_recommendation(0.25, tech, fund, sent, risk)

        assert recommendation == "SELL"
        assert confidence > 0.5

    def test_recommendation_generation_hold(self, analyzer):
        """Test HOLD recommendation generation"""
        tech = AnalysisResult("technical", True, 0.5)
        fund = AnalysisResult("fundamental", True, 0.48)
        sent = AnalysisResult("sentiment", True, 0.52)
        risk = AnalysisResult("risk", True, 0.50)

        recommendation, confidence = analyzer._generate_recommendation(0.50, tech, fund, sent, risk)

        assert "HOLD" in recommendation

    @pytest.mark.asyncio
    async def test_convenience_function(self, mock_ohlcv_data):
        """Test run_parallel_analysis convenience function"""
        with patch('agents.workflows.parallel_analysis.ParallelFinancialAnalyzer') as MockAnalyzer:
            mock_instance = MockAnalyzer.return_value
            mock_instance.analyze = AsyncMock(return_value=ParallelAnalysisResult(
                symbol="TCS",
                exchange="NSE",
                combined_score=0.75,
                recommendation="BUY",
                confidence=0.85
            ))

            result = await run_parallel_analysis("TCS", "NSE")

            assert isinstance(result, ParallelAnalysisResult)
            assert result.symbol == "TCS"


class TestIntegration:
    """Integration tests for Phase 3"""

    @pytest.fixture
    def mock_ohlcv_data(self):
        """Generate mock OHLCV DataFrame"""
        dates = pd.date_range(end=datetime.now(), periods=250, freq='D')
        data = {
            'open': [100 + i * 0.1 for i in range(250)],
            'high': [101 + i * 0.1 for i in range(250)],
            'low': [99 + i * 0.1 for i in range(250)],
            'close': [100.5 + i * 0.1 for i in range(250)],
            'volume': [1000000 + i * 1000 for i in range(250)]
        }
        return pd.DataFrame(data, index=dates)

    @pytest.mark.asyncio
    async def test_hybrid_search_with_parallel_analysis(self, mock_ohlcv_data):
        """Test integration between hybrid search and parallel analysis"""
        analyzer = ParallelFinancialAnalyzer()

        with patch.object(analyzer, '_fetch_ohlcv_data', return_value=mock_ohlcv_data):
            # Mock hybrid search
            mock_search = Mock()
            mock_search.search = AsyncMock(return_value=Mock(
                local_results=Mock(response="Good earnings"),
                web_results=[{"title": "News", "text": "Update", "url": "https://example.com"}]
            ))

            analyzer.hybrid_search = mock_search

            result = await analyzer.analyze("TCS", "NSE")

            assert result.symbol == "TCS"
            assert result.fundamental is not None
            assert result.sentiment is not None
            assert result.combined_score > 0.0


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
