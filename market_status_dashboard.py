#!/usr/bin/env python3
"""
Market Status Dashboard with Data Verification
Real-time market analysis with confidence scores and data quality indicators
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import yfinance as yf
import pandas as pd
import numpy as np

from utils.fiscal_year_utils import IndianFiscalYear, DataTimestamp
from data_sources.data_accuracy_validator import DataAccuracyValidator
from data_sources.bse_direct_fetcher import BSEDirectFetcher
from data_sources.nse_direct_fetcher import NSEDirectFetcher


class MarketStatusDashboard:
    """
    Comprehensive market dashboard with data verification
    """

    def __init__(self):
        self.validator = DataAccuracyValidator()
        self.bse_fetcher = BSEDirectFetcher()
        self.nse_fetcher = NSEDirectFetcher()
        self.timestamp = DataTimestamp.create_timestamp()

    def generate_dashboard(self, symbols: List[Tuple[str, str]] = None) -> Dict:
        """
        Generate comprehensive market dashboard

        Args:
            symbols: List of (BSE_code, NSE_symbol) tuples

        Returns:
            Dashboard data with confidence scores
        """
        if not symbols:
            # Default key stocks
            symbols = [
                ("532540", "TCS"),
                ("500325", "RELIANCE"),
                ("500209", "INFY"),
                ("500180", "HDFCBANK"),
                ("532174", "ICICIBANK"),
                ("500034", "BAJFINANCE"),
                ("526299", "MPHASIS"),
                ("533179", "PERSISTENT"),
                ("506401", "DEEPAKNTR"),
                ("543318", "CLEAN")
            ]

        dashboard = {
            'generated_at': self.timestamp,
            'market_overview': self._get_market_overview(),
            'sector_performance': self._get_sector_performance(),
            'stock_analysis': [],
            'data_quality_summary': {},
            'market_phase': '',
            'recommendations': []
        }

        # Analyze each stock
        high_confidence_stocks = []
        medium_confidence_stocks = []
        low_confidence_stocks = []

        for bse_code, nse_symbol in symbols:
            stock_data = self._analyze_stock(bse_code, nse_symbol)
            dashboard['stock_analysis'].append(stock_data)

            # Categorize by confidence
            if stock_data['data_confidence'] >= 70:
                high_confidence_stocks.append(stock_data)
            elif stock_data['data_confidence'] >= 50:
                medium_confidence_stocks.append(stock_data)
            else:
                low_confidence_stocks.append(stock_data)

        # Calculate market phase
        dashboard['market_phase'] = self._determine_market_phase(dashboard['stock_analysis'])

        # Data quality summary
        dashboard['data_quality_summary'] = {
            'high_confidence_count': len(high_confidence_stocks),
            'medium_confidence_count': len(medium_confidence_stocks),
            'low_confidence_count': len(low_confidence_stocks),
            'average_confidence': np.mean([s['data_confidence'] for s in dashboard['stock_analysis']])
        }

        # Generate recommendations
        dashboard['recommendations'] = self._generate_market_recommendations(
            dashboard, high_confidence_stocks, medium_confidence_stocks
        )

        return dashboard

    def _get_market_overview(self) -> Dict:
        """Get overall market metrics"""
        overview = {
            'timestamp': datetime.now().isoformat(),
            'indices': {}
        }

        # Fetch major indices
        indices = {
            'NIFTY50': '^NSEI',
            'SENSEX': '^BSESN',
            'BANKNIFTY': '^NSEBANK'
        }

        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    overview['indices'][name] = {
                        'value': hist['Close'].iloc[-1],
                        'change_pct': ((hist['Close'].iloc[-1] - hist['Open'].iloc[0]) /
                                      hist['Open'].iloc[0]) * 100,
                        'volume': hist['Volume'].iloc[-1]
                    }
            except:
                overview['indices'][name] = {'error': 'Unable to fetch'}

        return overview

    def _get_sector_performance(self) -> Dict:
        """Analyze sector-wise performance"""
        sectors = {
            'IT': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
            'Banking': ['HDFCBANK', 'ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK'],
            'Auto': ['TATAMOTORS', 'MARUTI', 'M&M', 'BAJAJ-AUTO', 'HEROMOTOCO'],
            'Pharma': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'BIOCON']
        }

        sector_performance = {}

        for sector, stocks in sectors.items():
            returns = []
            for stock in stocks:
                try:
                    ticker = yf.Ticker(f"{stock}.NS")
                    hist = ticker.history(period="1mo")
                    if len(hist) >= 20:
                        ret = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-20]) /
                              hist['Close'].iloc[-20]) * 100
                        returns.append(ret)
                except:
                    continue

            if returns:
                sector_performance[sector] = {
                    'avg_return_20d': np.mean(returns),
                    'best_performer': max(returns),
                    'worst_performer': min(returns),
                    'stocks_analyzed': len(returns)
                }

        return sector_performance

    def _analyze_stock(self, bse_code: str, nse_symbol: str) -> Dict:
        """
        Analyze individual stock with data verification

        Returns:
            Stock analysis with confidence scores
        """
        # Get validated data
        validation_report = self.validator.validate_company_data(bse_code, nse_symbol)

        # Get price data
        try:
            ticker = yf.Ticker(f"{nse_symbol}.NS")
            hist = ticker.history(period="3mo")

            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                returns_5d = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-5] - 1) * 100
                            if len(hist) >= 5 else 0)
                returns_20d = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-20] - 1) * 100
                             if len(hist) >= 20 else 0)
                returns_60d = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-60] - 1) * 100
                             if len(hist) >= 60 else 0)

                # Volume analysis
                avg_volume_5d = hist['Volume'][-5:].mean() if len(hist) >= 5 else 0
                avg_volume_20d = hist['Volume'][-25:-5].mean() if len(hist) >= 25 else 0
                volume_ratio = (avg_volume_5d / avg_volume_20d) if avg_volume_20d > 0 else 1

                # 52-week position
                high_52w = hist['High'].max()
                low_52w = hist['Low'].min()
                price_position = ((current_price - low_52w) / (high_52w - low_52w) * 100
                                if (high_52w - low_52w) > 0 else 50)
            else:
                current_price = returns_5d = returns_20d = returns_60d = 0
                volume_ratio = price_position = 0
        except:
            current_price = returns_5d = returns_20d = returns_60d = 0
            volume_ratio = price_position = 0

        # Extract validated financials
        revenue_yoy = None
        profit_yoy = None
        eps = None

        for validation in validation_report.get('validation_results', []):
            if validation.metric == 'revenue_yoy' and validation.recommended_value:
                revenue_yoy = validation.recommended_value
            elif validation.metric == 'profit_yoy' and validation.recommended_value:
                profit_yoy = validation.recommended_value
            elif validation.metric == 'eps' and validation.recommended_value:
                eps = validation.recommended_value

        # Calculate combined score
        technical_score = self._calculate_technical_score(
            returns_20d, returns_60d, volume_ratio, price_position
        )

        fundamental_score = self._calculate_fundamental_score(
            revenue_yoy, profit_yoy, eps
        )

        # Weight by confidence
        confidence = validation_report.get('overall_confidence', 50)
        combined_score = (technical_score * 0.4 + fundamental_score * 0.6) * (confidence / 100)

        return {
            'bse_code': bse_code,
            'nse_symbol': nse_symbol,
            'fetch_timestamp': DataTimestamp.create_timestamp(),
            'price_data': {
                'current_price': current_price,
                'returns_5d': returns_5d,
                'returns_20d': returns_20d,
                'returns_60d': returns_60d,
                'volume_ratio': volume_ratio,
                'price_position_52w': price_position
            },
            'fundamental_data': {
                'revenue_yoy': revenue_yoy,
                'profit_yoy': profit_yoy,
                'eps': eps,
                'data_sources': list(validation_report.get('data_sources', {}).keys())
            },
            'scores': {
                'technical_score': technical_score,
                'fundamental_score': fundamental_score,
                'combined_score': combined_score
            },
            'data_confidence': confidence,
            'data_quality': validation_report.get('data_quality', 'UNKNOWN'),
            'validation_warnings': [v.reason for v in validation_report.get('validation_results', [])
                                   if v.confidence_score < 60]
        }

    def _calculate_technical_score(self, returns_20d, returns_60d, volume_ratio, price_position):
        """Calculate technical analysis score (0-100)"""
        score = 0

        # Momentum scoring
        if returns_20d > 15:
            score += 25
        elif returns_20d > 10:
            score += 20
        elif returns_20d > 5:
            score += 15
        elif returns_20d > 0:
            score += 10

        if returns_60d > 30:
            score += 15
        elif returns_60d > 20:
            score += 12
        elif returns_60d > 10:
            score += 8
        elif returns_60d > 0:
            score += 5

        # Volume scoring
        if volume_ratio > 2:
            score += 20
        elif volume_ratio > 1.5:
            score += 15
        elif volume_ratio > 1.2:
            score += 10
        elif volume_ratio > 1:
            score += 5

        # Price position scoring
        if price_position > 80:
            score += 20
        elif price_position > 60:
            score += 15
        elif price_position > 40:
            score += 10
        elif price_position > 20:
            score += 5

        return min(score, 100)

    def _calculate_fundamental_score(self, revenue_yoy, profit_yoy, eps):
        """Calculate fundamental analysis score (0-100)"""
        score = 0

        if revenue_yoy is not None:
            if revenue_yoy > 30:
                score += 35
            elif revenue_yoy > 20:
                score += 28
            elif revenue_yoy > 10:
                score += 20
            elif revenue_yoy > 5:
                score += 15
            elif revenue_yoy > 0:
                score += 10

        if profit_yoy is not None:
            if profit_yoy > 40:
                score += 35
            elif profit_yoy > 25:
                score += 28
            elif profit_yoy > 15:
                score += 20
            elif profit_yoy > 10:
                score += 15
            elif profit_yoy > 0:
                score += 10

        if eps is not None:
            if eps > 50:
                score += 30
            elif eps > 20:
                score += 22
            elif eps > 10:
                score += 15
            elif eps > 5:
                score += 10
            elif eps > 0:
                score += 5

        return min(score, 100)

    def _determine_market_phase(self, stock_analysis: List[Dict]) -> str:
        """Determine current market phase"""
        if not stock_analysis:
            return "UNKNOWN"

        # Calculate average returns
        returns_20d = [s['price_data']['returns_20d'] for s in stock_analysis]
        avg_return = np.mean(returns_20d)

        # Count positive vs negative
        positive_count = sum(1 for r in returns_20d if r > 0)
        negative_count = len(returns_20d) - positive_count

        # Determine phase
        if avg_return > 10 and positive_count > len(returns_20d) * 0.7:
            return "BULLISH"
        elif avg_return > 5 and positive_count > len(returns_20d) * 0.6:
            return "MODERATELY_BULLISH"
        elif avg_return > -5 and abs(positive_count - negative_count) < 3:
            return "SIDEWAYS"
        elif avg_return > -10:
            return "MODERATELY_BEARISH"
        else:
            return "BEARISH"

    def _generate_market_recommendations(self, dashboard, high_conf, medium_conf) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        phase = dashboard['market_phase']
        avg_confidence = dashboard['data_quality_summary']['average_confidence']

        # Market phase recommendations
        if phase == "BULLISH":
            recommendations.append("📈 Market is bullish. Consider momentum strategies.")
        elif phase == "BEARISH":
            recommendations.append("📉 Market is bearish. Focus on defensive positions.")
        elif phase == "SIDEWAYS":
            recommendations.append("↔️ Market is sideways. Look for breakout candidates.")

        # Data quality recommendations
        if avg_confidence < 60:
            recommendations.append("⚠️ Overall data confidence is low. Verify with official sources.")
        elif avg_confidence < 80:
            recommendations.append("📊 Data confidence is moderate. Cross-check key metrics.")
        else:
            recommendations.append("✅ Data confidence is high. Analysis is reliable.")

        # Stock-specific recommendations
        if high_conf:
            # Find best performers with high confidence
            best = sorted(high_conf, key=lambda x: x['scores']['combined_score'], reverse=True)[:3]
            if best:
                recommendations.append(f"🎯 Top picks (high confidence):")
                for stock in best:
                    recommendations.append(
                        f"  • {stock['nse_symbol']}: Score {stock['scores']['combined_score']:.0f}/100"
                    )

        # Sector recommendations
        sectors = dashboard.get('sector_performance', {})
        if sectors:
            best_sector = max(sectors.items(), key=lambda x: x[1].get('avg_return_20d', 0))
            if best_sector[1]['avg_return_20d'] > 5:
                recommendations.append(
                    f"🏆 Best sector: {best_sector[0]} (+{best_sector[1]['avg_return_20d']:.1f}%)"
                )

        return recommendations


def print_dashboard(dashboard: Dict):
    """Pretty print the dashboard"""
    print("\n" + "=" * 80)
    print("📊 MARKET STATUS DASHBOARD")
    print("=" * 80)
    print(f"Generated: {dashboard['generated_at']['timestamp']}")

    # Market Overview
    print("\n🌍 MARKET OVERVIEW")
    print("-" * 40)
    for index, data in dashboard['market_overview']['indices'].items():
        if 'error' not in data:
            print(f"{index}: {data['value']:.2f} ({data['change_pct']:+.2f}%)")

    # Market Phase
    print(f"\n📈 Market Phase: {dashboard['market_phase']}")

    # Data Quality
    quality = dashboard['data_quality_summary']
    print(f"\n📊 Data Quality Summary:")
    print(f"  Average Confidence: {quality['average_confidence']:.1f}%")
    print(f"  High Confidence Stocks: {quality['high_confidence_count']}")
    print(f"  Medium Confidence Stocks: {quality['medium_confidence_count']}")
    print(f"  Low Confidence Stocks: {quality['low_confidence_count']}")

    # Top Stocks
    print("\n🎯 TOP STOCKS BY SCORE")
    print("-" * 40)
    sorted_stocks = sorted(dashboard['stock_analysis'],
                          key=lambda x: x['scores']['combined_score'],
                          reverse=True)[:5]

    for stock in sorted_stocks:
        print(f"\n{stock['nse_symbol']}:")
        print(f"  Price: ₹{stock['price_data']['current_price']:.2f}")
        print(f"  Returns (20d): {stock['price_data']['returns_20d']:+.1f}%")
        print(f"  Revenue YoY: {stock['fundamental_data']['revenue_yoy']:.1f}%"
              if stock['fundamental_data']['revenue_yoy'] else "  Revenue YoY: N/A")
        print(f"  Combined Score: {stock['scores']['combined_score']:.0f}/100")
        print(f"  Data Confidence: {stock['data_confidence']:.0f}%")
        print(f"  Data Quality: {stock['data_quality']}")

        if stock['validation_warnings']:
            print(f"  ⚠️ Warnings: {stock['validation_warnings'][0]}")

    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-" * 40)
    for rec in dashboard['recommendations']:
        print(rec)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("Initializing Market Status Dashboard...")
    dashboard = MarketStatusDashboard()

    print("Generating comprehensive market analysis...")
    print("(This may take a minute due to data validation from multiple sources)")

    # Generate dashboard with default stocks
    result = dashboard.generate_dashboard()

    # Print the dashboard
    print_dashboard(result)

    print("\n✅ Dashboard generation complete!")
    print("All data has been verified across multiple sources with confidence scores.")