"""
Parallel Financial Analysis Module

Executes multiple analysis types simultaneously using asyncio.gather:
1. Technical Analysis (VCP, indicators)
2. Fundamental Analysis (earnings, growth)
3. Sentiment Analysis (news, social)
4. Risk Analysis (volatility, drawdown)

Usage:
    from agents.workflows.parallel_analysis import run_parallel_analysis

    result = await run_parallel_analysis("TCS", "NSE")
    print(result.technical_score, result.fundamental_score)
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import pandas as pd

# Import existing components
from src.data.yahoo_finance_fetcher import YahooFinanceFetcher
from src.rag.hybrid_search import get_hybrid_search_engine

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result from a single analysis type"""
    analysis_type: str
    success: bool
    score: float  # 0.0 to 1.0
    data: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    error: Optional[str] = None


@dataclass
class ParallelAnalysisResult:
    """Combined result from all parallel analyses"""
    symbol: str
    exchange: str
    technical: Optional[AnalysisResult] = None
    fundamental: Optional[AnalysisResult] = None
    sentiment: Optional[AnalysisResult] = None
    risk: Optional[AnalysisResult] = None

    combined_score: float = 0.0
    recommendation: str = "HOLD"
    confidence: float = 0.0

    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class ParallelFinancialAnalyzer:
    """
    Execute multiple financial analyses in parallel

    Runs technical, fundamental, sentiment, and risk analyses
    simultaneously using asyncio.gather for maximum performance.
    """

    def __init__(self):
        """Initialize analyzer with required components"""
        self.data_fetcher = YahooFinanceFetcher()
        self.hybrid_search = get_hybrid_search_engine()

        logger.info("Parallel analyzer initialized")

    async def analyze(
        self,
        symbol: str,
        exchange: str = "NSE",
        analyses: Optional[List[str]] = None
    ) -> ParallelAnalysisResult:
        """
        Run parallel financial analysis

        Args:
            symbol: Stock symbol
            exchange: Exchange (NSE/BSE)
            analyses: Which analyses to run (default: all)

        Returns:
            ParallelAnalysisResult with all analysis results
        """
        start_time = datetime.now()

        # Default to all analyses
        if analyses is None:
            analyses = ["technical", "fundamental", "sentiment", "risk"]

        # Fetch OHLCV data once (shared by multiple analyses)
        ohlcv_data = await self._fetch_ohlcv_data(symbol, exchange)

        # Create analysis tasks
        tasks = []
        analysis_names = []

        if "technical" in analyses:
            tasks.append(self._technical_analysis(symbol, ohlcv_data))
            analysis_names.append("technical")

        if "fundamental" in analyses:
            tasks.append(self._fundamental_analysis(symbol, exchange))
            analysis_names.append("fundamental")

        if "sentiment" in analyses:
            tasks.append(self._sentiment_analysis(symbol))
            analysis_names.append("sentiment")

        if "risk" in analyses:
            tasks.append(self._risk_analysis(symbol, ohlcv_data))
            analysis_names.append("risk")

        # Execute all analyses in parallel
        logger.info(f"Starting parallel analysis for {symbol}: {analysis_names}")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Parse results
        tech_result = None
        fund_result = None
        sent_result = None
        risk_result = None

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Analysis {analysis_names[i]} failed: {result}")
                continue

            if analysis_names[i] == "technical":
                tech_result = result
            elif analysis_names[i] == "fundamental":
                fund_result = result
            elif analysis_names[i] == "sentiment":
                sent_result = result
            elif analysis_names[i] == "risk":
                risk_result = result

        # Calculate combined score and recommendation
        combined_score = self._calculate_combined_score(
            tech_result, fund_result, sent_result, risk_result
        )

        recommendation, confidence = self._generate_recommendation(
            combined_score, tech_result, fund_result, sent_result, risk_result
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        return ParallelAnalysisResult(
            symbol=symbol,
            exchange=exchange,
            technical=tech_result,
            fundamental=fund_result,
            sentiment=sent_result,
            risk=risk_result,
            combined_score=combined_score,
            recommendation=recommendation,
            confidence=confidence,
            execution_time=execution_time
        )

    async def _fetch_ohlcv_data(
        self,
        symbol: str,
        exchange: str,
        lookback_days: int = 365
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data (shared by multiple analyses)"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)

            ohlcv = await asyncio.to_thread(
                self.data_fetcher.fetch_ohlcv,
                symbol=symbol,
                exchange=exchange,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                timeframe="1d"
            )

            return ohlcv
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV data: {e}")
            return None

    async def _technical_analysis(
        self,
        symbol: str,
        ohlcv: Optional[pd.DataFrame]
    ) -> AnalysisResult:
        """Technical analysis: VCP, RSI, MACD, volume"""
        start_time = datetime.now()

        try:
            if ohlcv is None or len(ohlcv) < 50:
                return AnalysisResult(
                    analysis_type="technical",
                    success=False,
                    score=0.0,
                    error="Insufficient OHLCV data"
                )

            insights = []
            score_components = []

            # Price trend
            sma_50 = ohlcv['close'].rolling(50).mean()
            sma_200 = ohlcv['close'].rolling(200).mean() if len(ohlcv) >= 200 else None
            current_price = ohlcv['close'].iloc[-1]

            if sma_200 is not None and not pd.isna(sma_200.iloc[-1]):
                if current_price > sma_200.iloc[-1]:
                    insights.append("Price above 200-day SMA (bullish long-term trend)")
                    score_components.append(0.3)
                else:
                    insights.append("Price below 200-day SMA (bearish long-term trend)")
                    score_components.append(-0.2)

            # RSI
            delta = ohlcv['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            if 40 <= current_rsi <= 60:
                insights.append(f"RSI neutral at {current_rsi:.1f} (ideal range)")
                score_components.append(0.2)
            elif current_rsi < 30:
                insights.append(f"RSI oversold at {current_rsi:.1f} (potential buy)")
                score_components.append(0.3)
            elif current_rsi > 70:
                insights.append(f"RSI overbought at {current_rsi:.1f} (caution)")
                score_components.append(-0.2)

            # Volume trend
            avg_volume_20 = ohlcv['volume'].rolling(20).mean()
            current_volume = ohlcv['volume'].iloc[-1]
            if current_volume > avg_volume_20.iloc[-1] * 1.5:
                insights.append("Above-average volume (strong interest)")
                score_components.append(0.2)

            # Calculate technical score (0-1)
            base_score = 0.5
            adjustment = sum(score_components)
            technical_score = max(0.0, min(1.0, base_score + adjustment))

            execution_time = (datetime.now() - start_time).total_seconds()

            return AnalysisResult(
                analysis_type="technical",
                success=True,
                score=technical_score,
                data={
                    "current_price": float(current_price),
                    "sma_50": float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None,
                    "sma_200": float(sma_200.iloc[-1]) if sma_200 is not None and not pd.isna(sma_200.iloc[-1]) else None,
                    "rsi": float(current_rsi),
                    "volume_ratio": float(current_volume / avg_volume_20.iloc[-1]) if not pd.isna(avg_volume_20.iloc[-1]) else 1.0
                },
                insights=insights,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return AnalysisResult(
                analysis_type="technical",
                success=False,
                score=0.0,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    async def _fundamental_analysis(
        self,
        symbol: str,
        exchange: str
    ) -> AnalysisResult:
        """Fundamental analysis: earnings, growth, quality"""
        start_time = datetime.now()

        try:
            # Search for earnings using hybrid search
            search_result = await self.hybrid_search.search(
                f"{symbol} earnings QoQ growth profit margin",
                sources=["local"],
                filters={"company": symbol.upper()},
                local_top_k=3
            )

            insights = []
            score = 0.5  # Neutral default

            if search_result.local_results and search_result.local_results.response:
                response = search_result.local_results.response.lower()

                # Analyze earnings response for positive indicators
                if any(word in response for word in ["strong", "beat", "growth", "improved", "exceeded"]):
                    insights.append("Positive earnings signals detected")
                    score += 0.2

                if any(word in response for word in ["revenue growth", "profit growth", "margin expansion"]):
                    insights.append("Revenue/profit growth mentioned")
                    score += 0.15

                if any(word in response for word in ["guidance", "outlook positive", "raised guidance"]):
                    insights.append("Positive guidance mentioned")
                    score += 0.15

                # Negative indicators
                if any(word in response for word in ["decline", "miss", "weak", "disappointed", "lower"]):
                    insights.append("Some negative earnings indicators")
                    score -= 0.2

                score = max(0.0, min(1.0, score))
            else:
                insights.append("No earnings data available")
                score = 0.5  # Neutral when no data

            execution_time = (datetime.now() - start_time).total_seconds()

            return AnalysisResult(
                analysis_type="fundamental",
                success=True,
                score=score,
                data={
                    "has_earnings_data": search_result.local_results is not None,
                    "earnings_summary": search_result.local_results.response[:200] if search_result.local_results else None
                },
                insights=insights,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Fundamental analysis failed: {e}")
            return AnalysisResult(
                analysis_type="fundamental",
                success=False,
                score=0.5,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    async def _sentiment_analysis(self, symbol: str) -> AnalysisResult:
        """Sentiment analysis: news, social media"""
        start_time = datetime.now()

        try:
            # Search for recent news using hybrid search
            search_result = await self.hybrid_search.search(
                f"{symbol} latest news announcement",
                sources=["web"],
                web_num_results=5
            )

            insights = []
            score = 0.5  # Neutral default

            if search_result.web_results and len(search_result.web_results) > 0:
                # Simple sentiment scoring based on titles/text
                positive_words = ["up", "gain", "surge", "beat", "strong", "growth", "profit", "buy", "upgrade"]
                negative_words = ["down", "fall", "drop", "miss", "weak", "loss", "sell", "downgrade", "concern"]

                positive_count = 0
                negative_count = 0

                for result in search_result.web_results:
                    text = (result.get('title', '') + ' ' + result.get('text', '')).lower()

                    positive_count += sum(1 for word in positive_words if word in text)
                    negative_count += sum(1 for word in negative_words if word in text)

                if positive_count > negative_count:
                    insights.append(f"Positive news sentiment ({positive_count} positive vs {negative_count} negative signals)")
                    score = 0.5 + min(0.3, (positive_count - negative_count) * 0.05)
                elif negative_count > positive_count:
                    insights.append(f"Negative news sentiment ({negative_count} negative vs {positive_count} positive signals)")
                    score = 0.5 - min(0.3, (negative_count - positive_count) * 0.05)
                else:
                    insights.append("Neutral news sentiment")

                insights.append(f"Analyzed {len(search_result.web_results)} recent news articles")
            else:
                insights.append("No recent news available")

            execution_time = (datetime.now() - start_time).total_seconds()

            return AnalysisResult(
                analysis_type="sentiment",
                success=True,
                score=score,
                data={
                    "news_count": len(search_result.web_results) if search_result.web_results else 0,
                    "has_web_data": search_result.web_results is not None
                },
                insights=insights,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return AnalysisResult(
                analysis_type="sentiment",
                success=False,
                score=0.5,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    async def _risk_analysis(
        self,
        symbol: str,
        ohlcv: Optional[pd.DataFrame]
    ) -> AnalysisResult:
        """Risk analysis: volatility, drawdown, beta"""
        start_time = datetime.now()

        try:
            if ohlcv is None or len(ohlcv) < 50:
                return AnalysisResult(
                    analysis_type="risk",
                    success=False,
                    score=0.5,
                    error="Insufficient data for risk analysis"
                )

            insights = []

            # Calculate volatility (annualized)
            returns = ohlcv['close'].pct_change()
            volatility = returns.std() * (252 ** 0.5)  # Annualized

            # Max drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            # Risk score (lower risk = higher score)
            risk_score = 0.5

            if volatility < 0.25:  # Low volatility
                insights.append(f"Low volatility ({volatility:.1%}) - stable stock")
                risk_score += 0.2
            elif volatility > 0.50:  # High volatility
                insights.append(f"High volatility ({volatility:.1%}) - risky stock")
                risk_score -= 0.2
            else:
                insights.append(f"Moderate volatility ({volatility:.1%})")

            if max_drawdown > -0.30:  # Small drawdown
                insights.append(f"Manageable max drawdown ({max_drawdown:.1%})")
                risk_score += 0.1
            else:
                insights.append(f"Large max drawdown ({max_drawdown:.1%})")
                risk_score -= 0.1

            risk_score = max(0.0, min(1.0, risk_score))

            execution_time = (datetime.now() - start_time).total_seconds()

            return AnalysisResult(
                analysis_type="risk",
                success=True,
                score=risk_score,
                data={
                    "volatility": float(volatility),
                    "max_drawdown": float(max_drawdown),
                    "current_return": float(returns.iloc[-1]) if len(returns) > 0 else 0.0
                },
                insights=insights,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            return AnalysisResult(
                analysis_type="risk",
                success=False,
                score=0.5,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )

    def _calculate_combined_score(
        self,
        technical: Optional[AnalysisResult],
        fundamental: Optional[AnalysisResult],
        sentiment: Optional[AnalysisResult],
        risk: Optional[AnalysisResult]
    ) -> float:
        """Calculate weighted combined score"""
        weights = {
            "technical": 0.35,
            "fundamental": 0.35,
            "sentiment": 0.15,
            "risk": 0.15
        }

        total_weight = 0.0
        weighted_sum = 0.0

        if technical and technical.success:
            weighted_sum += technical.score * weights["technical"]
            total_weight += weights["technical"]

        if fundamental and fundamental.success:
            weighted_sum += fundamental.score * weights["fundamental"]
            total_weight += weights["fundamental"]

        if sentiment and sentiment.success:
            weighted_sum += sentiment.score * weights["sentiment"]
            total_weight += weights["sentiment"]

        if risk and risk.success:
            weighted_sum += risk.score * weights["risk"]
            total_weight += weights["risk"]

        if total_weight == 0:
            return 0.5  # Neutral if no analyses succeeded

        return weighted_sum / total_weight

    def _generate_recommendation(
        self,
        combined_score: float,
        technical: Optional[AnalysisResult],
        fundamental: Optional[AnalysisResult],
        sentiment: Optional[AnalysisResult],
        risk: Optional[AnalysisResult]
    ) -> tuple[str, float]:
        """Generate recommendation and confidence"""

        # Count successful analyses for confidence
        successful_analyses = sum(1 for a in [technical, fundamental, sentiment, risk] if a and a.success)
        confidence = (successful_analyses / 4.0) * 0.5 + 0.5  # 0.5-1.0 range

        # Adjust confidence based on score consistency
        if combined_score > 0.7:
            recommendation = "BUY"
            confidence *= 0.95
        elif combined_score > 0.55:
            recommendation = "HOLD (Weak Buy)"
            confidence *= 0.85
        elif combined_score >= 0.45:
            recommendation = "HOLD"
            confidence *= 0.80
        elif combined_score >= 0.30:
            recommendation = "HOLD (Weak Sell)"
            confidence *= 0.85
        else:
            recommendation = "SELL"
            confidence *= 0.90

        return recommendation, confidence


# Convenience function
async def run_parallel_analysis(
    symbol: str,
    exchange: str = "NSE",
    analyses: Optional[List[str]] = None
) -> ParallelAnalysisResult:
    """
    Convenience function to run parallel analysis

    Args:
        symbol: Stock symbol
        exchange: Exchange (NSE/BSE)
        analyses: Which analyses to run (default: all)

    Returns:
        ParallelAnalysisResult
    """
    analyzer = ParallelFinancialAnalyzer()
    return await analyzer.analyze(symbol, exchange, analyses)
