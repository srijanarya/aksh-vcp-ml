"""
VCP Multi-Stage Workflow

Sequential agent pipeline for comprehensive VCP stock analysis:
1. DataCollector - Fetches OHLCV data, earnings, fundamentals
2. PatternDetector - Identifies VCP patterns and technical signals
3. FundamentalAnalyst - Analyzes earnings quality and growth
4. SignalGenerator - Generates buy/sell signals with risk metrics

Source: Learned from awesome-ai-apps/advance_ai_agents/deep_researcher_agent
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

# Import existing VCP system components
from src.data.yahoo_finance_fetcher import YahooFinanceFetcher
from src.rag.earnings_query import get_earnings_query_engine
from src.memory.memori_config import get_memori_instance

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStageResult:
    """Result from a single workflow stage"""
    stage_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class WorkflowResult:
    """Complete workflow result with all stage outputs"""
    symbol: str
    success: bool
    stages: List[WorkflowStageResult]
    final_recommendation: Optional[str] = None
    confidence_score: float = 0.0
    execution_time: float = 0.0

    def get_stage(self, stage_name: str) -> Optional[WorkflowStageResult]:
        """Get specific stage result"""
        for stage in self.stages:
            if stage.stage_name == stage_name:
                return stage
        return None


class VCPWorkflow:
    """
    Multi-stage VCP analysis workflow

    Architecture:
    Stage 1: DataCollector → Stage 2: PatternDetector →
    Stage 3: FundamentalAnalyst → Stage 4: SignalGenerator

    Each stage:
    - Receives output from previous stage
    - Performs specialized analysis
    - Passes enriched data to next stage
    - Can use memory from past analyses
    """

    def __init__(
        self,
        use_memory: bool = True,
        enable_streaming: bool = False
    ):
        """
        Initialize VCP workflow

        Args:
            use_memory: Enable persistent memory across sessions
            enable_streaming: Stream results as they're generated
        """
        self.use_memory = use_memory
        self.enable_streaming = enable_streaming

        # Initialize components
        self.data_fetcher = YahooFinanceFetcher()
        self.earnings_engine = get_earnings_query_engine()

        # Memory integration (already implemented in Phase 1)
        if self.use_memory:
            try:
                self.memory = get_memori_instance()
                logger.info("Memory system initialized for workflow")
            except Exception as e:
                logger.warning(f"Memory initialization failed: {e}, continuing without memory")
                self.use_memory = False
                self.memory = None

        logger.info(f"Initialized VCPWorkflow (memory={use_memory}, streaming={enable_streaming})")

    async def run(self, symbol: str, exchange: str = "NSE") -> WorkflowResult:
        """
        Execute complete VCP analysis workflow

        Args:
            symbol: Stock symbol (e.g., "TCS", "RELIANCE")
            exchange: Exchange (NSE or BSE)

        Returns:
            WorkflowResult with all stage outputs

        Example:
            >>> workflow = VCPWorkflow()
            >>> result = await workflow.run("TCS", "NSE")
            >>> print(result.final_recommendation)
        """
        start_time = datetime.now()
        stages = []

        try:
            # Stage 1: Data Collection
            stage1 = await self._stage1_data_collector(symbol, exchange)
            stages.append(stage1)

            if not stage1.success:
                return WorkflowResult(
                    symbol=symbol,
                    success=False,
                    stages=stages,
                    final_recommendation="Data collection failed",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            # Stage 2: Pattern Detection
            stage2 = await self._stage2_pattern_detector(symbol, stage1.data)
            stages.append(stage2)

            if not stage2.success:
                logger.warning(f"Pattern detection failed for {symbol}")

            # Stage 3: Fundamental Analysis
            stage3 = await self._stage3_fundamental_analyst(symbol, stage2.data)
            stages.append(stage3)

            if not stage3.success:
                logger.warning(f"Fundamental analysis failed for {symbol}")

            # Stage 4: Signal Generation
            stage4 = await self._stage4_signal_generator(symbol, stage3.data)
            stages.append(stage4)

            # Calculate overall confidence
            confidence = self._calculate_confidence(stages)

            # Generate final recommendation
            recommendation = self._synthesize_recommendation(stages)

            # Store in memory if enabled
            if self.use_memory:
                await self._store_in_memory(symbol, stages, recommendation, confidence)

            result = WorkflowResult(
                symbol=symbol,
                success=True,
                stages=stages,
                final_recommendation=recommendation,
                confidence_score=confidence,
                execution_time=(datetime.now() - start_time).total_seconds()
            )

            logger.info(f"Workflow complete for {symbol}: confidence={confidence:.2f}")
            return result

        except Exception as e:
            logger.error(f"Workflow failed for {symbol}: {e}")
            return WorkflowResult(
                symbol=symbol,
                success=False,
                stages=stages,
                final_recommendation=f"Workflow error: {str(e)}",
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    async def _stage1_data_collector(
        self,
        symbol: str,
        exchange: str
    ) -> WorkflowStageResult:
        """
        Stage 1: Collect price data, earnings, fundamentals

        Returns:
            Stage result with OHLCV data, earnings info, fundamentals
        """
        start_time = datetime.now()

        try:
            logger.info(f"Stage 1: Collecting data for {symbol}")

            # Fetch historical price data (last 365 days for VCP detection)
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            # Use Yahoo Finance fetcher
            ohlcv_data = await asyncio.to_thread(
                self.data_fetcher.fetch_ohlcv,
                symbol=symbol,
                exchange=exchange,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                timeframe="1d"
            )

            # Check if we got data
            if ohlcv_data is None or len(ohlcv_data) == 0:
                return WorkflowStageResult(
                    stage_name="DataCollector",
                    success=False,
                    data={},
                    error=f"No OHLCV data available for {symbol}",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            # Fetch earnings data from RAG
            earnings_query = f"Show latest earnings and growth trends for {symbol}"
            try:
                earnings_result = self.earnings_engine.search_by_company(
                    symbol,
                    earnings_query,
                    top_k=3
                )
                earnings_info = {
                    "summary": earnings_result.response,
                    "sources": [
                        {
                            "quarter": node["metadata"].get("quarter"),
                            "score": node["score"]
                        }
                        for node in earnings_result.source_nodes
                    ]
                }
            except Exception as e:
                logger.warning(f"Earnings query failed: {e}")
                earnings_info = {"summary": "No earnings data available"}

            # Check memory for past analysis
            past_analysis = None
            if self.use_memory and self.memory:
                try:
                    memory_query = f"Previous VCP analysis for {symbol}"
                    # Search memory using Memori instance
                    past_results = self.memory.search(memory_query, limit=3)
                    if past_results:
                        past_analysis = [r.get("content", "") for r in past_results]
                except Exception as e:
                    logger.debug(f"Memory search failed: {e}")

            data = {
                "symbol": symbol,
                "exchange": exchange,
                "ohlcv": ohlcv_data,
                "data_points": len(ohlcv_data),
                "date_range": {
                    "start": ohlcv_data.index[0].strftime("%Y-%m-%d") if len(ohlcv_data) > 0 else None,
                    "end": ohlcv_data.index[-1].strftime("%Y-%m-%d") if len(ohlcv_data) > 0 else None
                },
                "earnings": earnings_info,
                "past_analysis": past_analysis
            }

            return WorkflowStageResult(
                stage_name="DataCollector",
                success=True,
                data=data,
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            logger.error(f"Stage 1 failed: {e}")
            return WorkflowStageResult(
                stage_name="DataCollector",
                success=False,
                data={},
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    async def _stage2_pattern_detector(
        self,
        symbol: str,
        data_collector_output: Dict[str, Any]
    ) -> WorkflowStageResult:
        """
        Stage 2: Detect VCP patterns and technical signals

        Args:
            data_collector_output: Output from Stage 1

        Returns:
            Stage result with VCP detection, volume analysis, support/resistance
        """
        start_time = datetime.now()

        try:
            logger.info(f"Stage 2: Detecting patterns for {symbol}")

            ohlcv = data_collector_output.get("ohlcv")
            if ohlcv is None or len(ohlcv) < 150:
                return WorkflowStageResult(
                    stage_name="PatternDetector",
                    success=False,
                    data=data_collector_output,
                    error="Insufficient data for pattern detection (need 150+ days)",
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            # VCP Pattern Detection (simplified - using existing logic)
            # In production, this would use your actual VCP detector
            vcp_detected = False
            vcp_score = 0.0

            # Calculate volume contraction (key VCP characteristic)
            recent_volume = ohlcv['volume'].tail(30).mean()
            prior_volume = ohlcv['volume'].tail(90).head(60).mean()
            volume_contraction = (prior_volume - recent_volume) / prior_volume if prior_volume > 0 else 0

            # Simple VCP heuristic
            if volume_contraction > 0.2:  # 20%+ volume contraction
                price_consolidation = (ohlcv['high'].tail(30).max() - ohlcv['low'].tail(30).min()) / ohlcv['close'].tail(30).mean()
                if price_consolidation < 0.15:  # Tight consolidation (<15%)
                    vcp_detected = True
                    vcp_score = min(0.9, volume_contraction + (1 - price_consolidation))

            # Calculate support/resistance
            recent_high = ohlcv['high'].tail(90).max()
            recent_low = ohlcv['low'].tail(90).min()
            current_price = ohlcv['close'].iloc[-1]

            # Calculate simple RSI
            delta = ohlcv['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50

            pattern_data = {
                **data_collector_output,  # Carry forward previous data
                "vcp_detected": vcp_detected,
                "vcp_score": vcp_score,
                "volume_contraction": volume_contraction,
                "support_level": recent_low,
                "resistance_level": recent_high,
                "current_price": current_price,
                "rsi": current_rsi,
                "technical_strength": vcp_score * 0.6 + (current_rsi / 100) * 0.4
            }

            return WorkflowStageResult(
                stage_name="PatternDetector",
                success=True,
                data=pattern_data,
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            logger.error(f"Stage 2 failed: {e}")
            return WorkflowStageResult(
                stage_name="PatternDetector",
                success=False,
                data=data_collector_output,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    async def _stage3_fundamental_analyst(
        self,
        symbol: str,
        pattern_detector_output: Dict[str, Any]
    ) -> WorkflowStageResult:
        """
        Stage 3: Analyze earnings quality and fundamental strength

        Args:
            pattern_detector_output: Output from Stage 2

        Returns:
            Stage result with earnings quality score, growth metrics
        """
        start_time = datetime.now()

        try:
            logger.info(f"Stage 3: Analyzing fundamentals for {symbol}")

            earnings_info = pattern_detector_output.get("earnings", {})
            earnings_summary = earnings_info.get("summary", "")

            # Analyze earnings quality from RAG summary
            quality_indicators = {
                "earnings_beat": any(word in earnings_summary.lower() for word in ["beat", "exceeded", "surpassed"]),
                "revenue_growth": any(word in earnings_summary.lower() for word in ["growth", "increase", "higher"]),
                "positive_guidance": any(word in earnings_summary.lower() for word in ["guidance", "outlook", "positive"]),
                "margin_improvement": any(word in earnings_summary.lower() for word in ["margin", "profitability", "improved"])
            }

            # Calculate fundamental score
            fundamental_score = sum(quality_indicators.values()) / len(quality_indicators)

            # Query for QoQ growth specifically
            try:
                qoq_query = f"What was the QoQ revenue and profit growth for {symbol} in latest quarter?"
                qoq_result = self.earnings_engine.search_by_company(symbol, qoq_query, top_k=2)
                qoq_analysis = qoq_result.response
            except Exception as e:
                logger.warning(f"QoQ query failed: {e}")
                qoq_analysis = "QoQ data not available"

            fundamental_data = {
                **pattern_detector_output,  # Carry forward
                "fundamental_score": fundamental_score,
                "quality_indicators": quality_indicators,
                "qoq_analysis": qoq_analysis,
                "earnings_quality": "Strong" if fundamental_score > 0.6 else "Moderate" if fundamental_score > 0.3 else "Weak"
            }

            return WorkflowStageResult(
                stage_name="FundamentalAnalyst",
                success=True,
                data=fundamental_data,
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            logger.error(f"Stage 3 failed: {e}")
            return WorkflowStageResult(
                stage_name="FundamentalAnalyst",
                success=False,
                data=pattern_detector_output,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    async def _stage4_signal_generator(
        self,
        symbol: str,
        fundamental_analyst_output: Dict[str, Any]
    ) -> WorkflowStageResult:
        """
        Stage 4: Generate buy/sell signals with risk metrics

        Args:
            fundamental_analyst_output: Output from Stage 3

        Returns:
            Stage result with signal, entry price, stop loss, target
        """
        start_time = datetime.now()

        try:
            logger.info(f"Stage 4: Generating signals for {symbol}")

            # Extract key metrics from previous stages
            vcp_detected = fundamental_analyst_output.get("vcp_detected", False)
            vcp_score = fundamental_analyst_output.get("vcp_score", 0.0)
            technical_strength = fundamental_analyst_output.get("technical_strength", 0.0)
            fundamental_score = fundamental_analyst_output.get("fundamental_score", 0.0)
            current_price = fundamental_analyst_output.get("current_price", 0)
            support_level = fundamental_analyst_output.get("support_level", 0)
            resistance_level = fundamental_analyst_output.get("resistance_level", 0)
            rsi = fundamental_analyst_output.get("rsi", 50)

            # Generate signal
            signal = "HOLD"
            signal_strength = 0.0

            # Buy criteria: VCP + Strong fundamentals + RSI not overbought
            if vcp_detected and fundamental_score > 0.5 and rsi < 70:
                signal = "BUY"
                signal_strength = (vcp_score * 0.4 + fundamental_score * 0.4 + technical_strength * 0.2)

            # Sell criteria: No VCP + Weak fundamentals OR Overbought
            elif not vcp_detected and (fundamental_score < 0.3 or rsi > 80):
                signal = "SELL"
                signal_strength = 1 - (vcp_score * 0.3 + fundamental_score * 0.4 + (100 - rsi) / 100 * 0.3)

            # Calculate risk metrics
            entry_price = current_price
            stop_loss = support_level * 0.98  # 2% below support
            target_price = resistance_level * 1.05  # 5% above resistance

            risk_reward = (target_price - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

            signal_data = {
                **fundamental_analyst_output,  # Carry forward
                "signal": signal,
                "signal_strength": signal_strength,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "target_price": target_price,
                "risk_reward_ratio": risk_reward,
                "position_size_suggestion": "5-10%" if signal_strength > 0.7 else "2-5%" if signal_strength > 0.5 else "0-2%"
            }

            return WorkflowStageResult(
                stage_name="SignalGenerator",
                success=True,
                data=signal_data,
                execution_time=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            logger.error(f"Stage 4 failed: {e}")
            return WorkflowStageResult(
                stage_name="SignalGenerator",
                success=False,
                data=fundamental_analyst_output,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def _calculate_confidence(self, stages: List[WorkflowStageResult]) -> float:
        """Calculate overall confidence score from all stages"""
        if not stages or len(stages) < 4:
            return 0.0

        # Weight each stage
        weights = {
            "DataCollector": 0.1,
            "PatternDetector": 0.3,
            "FundamentalAnalyst": 0.3,
            "SignalGenerator": 0.3
        }

        total_confidence = 0.0
        for stage in stages:
            if stage.success:
                weight = weights.get(stage.stage_name, 0.0)
                # Extract stage-specific confidence
                if stage.stage_name == "PatternDetector":
                    stage_conf = stage.data.get("technical_strength", 0.5)
                elif stage.stage_name == "FundamentalAnalyst":
                    stage_conf = stage.data.get("fundamental_score", 0.5)
                elif stage.stage_name == "SignalGenerator":
                    stage_conf = stage.data.get("signal_strength", 0.5)
                else:
                    stage_conf = 1.0  # DataCollector gets full if successful

                total_confidence += weight * stage_conf

        return min(1.0, total_confidence)

    def _synthesize_recommendation(self, stages: List[WorkflowStageResult]) -> str:
        """Synthesize final recommendation from all stages"""
        if not stages or len(stages) < 4:
            return "Incomplete analysis - unable to generate recommendation"

        signal_stage = stages[-1]  # SignalGenerator is last
        if not signal_stage.success:
            return "Signal generation failed - no recommendation available"

        data = signal_stage.data
        signal = data.get("signal", "HOLD")
        strength = data.get("signal_strength", 0.0)
        vcp_detected = data.get("vcp_detected", False)
        earnings_quality = data.get("earnings_quality", "Unknown")
        risk_reward = data.get("risk_reward_ratio", 0.0)

        # Build recommendation
        recommendation = f"**{signal}** (Strength: {strength:.1%})\n\n"
        recommendation += f"VCP Pattern: {'✓ Detected' if vcp_detected else '✗ Not detected'}\n"
        recommendation += f"Earnings Quality: {earnings_quality}\n"
        recommendation += f"Risk/Reward: {risk_reward:.2f}:1\n\n"

        if signal == "BUY":
            recommendation += f"Entry: ₹{data.get('entry_price', 0):.2f}\n"
            recommendation += f"Stop Loss: ₹{data.get('stop_loss', 0):.2f}\n"
            recommendation += f"Target: ₹{data.get('target_price', 0):.2f}\n"
            recommendation += f"Position Size: {data.get('position_size_suggestion', 'N/A')}"
        elif signal == "SELL":
            recommendation += "Consider exiting position or avoiding entry."
        else:
            recommendation += "Monitor for better entry opportunity."

        return recommendation

    async def _store_in_memory(
        self,
        symbol: str,
        stages: List[WorkflowStageResult],
        recommendation: str,
        confidence: float
    ):
        """Store workflow result in persistent memory"""
        if not self.memory:
            return

        try:
            memory_content = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "recommendation": recommendation,
                "confidence": confidence,
                "stages": [
                    {
                        "name": stage.stage_name,
                        "success": stage.success,
                        "execution_time": stage.execution_time
                    }
                    for stage in stages
                ]
            }

            # Store using existing memory system
            import json
            await asyncio.to_thread(
                self.memory.record_conversation,
                user_input=f"VCP analysis for {symbol}",
                ai_output=json.dumps(memory_content, indent=2)
            )

            logger.info(f"Workflow result stored in memory for {symbol}")
        except Exception as e:
            logger.warning(f"Failed to store in memory: {e}")


def get_vcp_workflow(use_memory: bool = True) -> VCPWorkflow:
    """
    Factory function to get VCP workflow instance

    Args:
        use_memory: Enable persistent memory

    Returns:
        Configured VCPWorkflow

    Example:
        >>> workflow = get_vcp_workflow()
        >>> result = await workflow.run("TCS", "NSE")
    """
    return VCPWorkflow(use_memory=use_memory)


# Synchronous wrapper for convenience
def run_vcp_analysis(symbol: str, exchange: str = "NSE") -> WorkflowResult:
    """
    Synchronous wrapper for VCP analysis

    Args:
        symbol: Stock symbol
        exchange: Exchange (NSE or BSE)

    Returns:
        WorkflowResult

    Example:
        >>> result = run_vcp_analysis("TCS")
        >>> print(result.final_recommendation)
    """
    workflow = get_vcp_workflow()
    return asyncio.run(workflow.run(symbol, exchange))


if __name__ == "__main__":
    # Test workflow
    logging.basicConfig(level=logging.INFO)

    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "TCS"
    exchange = sys.argv[2] if len(sys.argv) > 2 else "NSE"

    print(f"\n=== VCP Multi-Stage Workflow ===")
    print(f"Symbol: {symbol}")
    print(f"Exchange: {exchange}")
    print("="*30 + "\n")

    result = run_vcp_analysis(symbol, exchange)

    print(f"Success: {result.success}")
    print(f"Confidence: {result.confidence_score:.1%}")
    print(f"Execution Time: {result.execution_time:.2f}s\n")

    print("Stages:")
    for stage in result.stages:
        status = "✓" if stage.success else "✗"
        print(f"  {status} {stage.stage_name} ({stage.execution_time:.2f}s)")

    print(f"\n{result.final_recommendation}")
