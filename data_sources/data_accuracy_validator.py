"""
Data Accuracy Validator
Cross-validates data from multiple sources and provides confidence scores
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import json

from utils.fiscal_year_utils import DataTimestamp
from data_sources.bse_direct_fetcher import BSEDirectFetcher
from data_sources.nse_direct_fetcher import NSEDirectFetcher


@dataclass
class ValidationResult:
    """Result of data validation"""
    metric: str
    sources: Dict[str, any]
    discrepancy_pct: float
    confidence_score: float
    recommended_value: any
    reason: str
    timestamp: Dict


class DataAccuracyValidator:
    """
    Validates financial data across multiple sources
    Provides confidence scores and discrepancy detection
    """

    def __init__(self):
        self.bse_fetcher = BSEDirectFetcher()
        self.nse_fetcher = NSEDirectFetcher()
        self.validation_rules = self._setup_validation_rules()

    def _setup_validation_rules(self) -> Dict:
        """Define validation rules for different metrics"""
        return {
            'revenue_yoy': {
                'min': -50,  # Revenue shouldn't drop more than 50%
                'max': 200,  # Revenue shouldn't grow more than 200%
                'tolerance': 5  # 5% tolerance between sources
            },
            'profit_yoy': {
                'min': -100,  # Can have losses
                'max': 500,  # High profit growth possible
                'tolerance': 10  # 10% tolerance
            },
            'eps': {
                'min': -100,  # Can be negative
                'max': 1000,  # Reasonable EPS limit
                'tolerance': 2  # ₹2 tolerance
            },
            'market_cap': {
                'min': 0,
                'max': float('inf'),
                'tolerance': 5  # 5% tolerance
            }
        }

    def validate_company_data(self, bse_code: str, nse_symbol: str) -> Dict:
        """
        Validate company data from multiple sources

        Args:
            bse_code: BSE scrip code
            nse_symbol: NSE symbol

        Returns:
            Comprehensive validation report
        """
        timestamp = DataTimestamp.create_timestamp()
        report = {
            'bse_code': bse_code,
            'nse_symbol': nse_symbol,
            'validation_timestamp': timestamp,
            'data_sources': {},
            'validation_results': [],
            'overall_confidence': 0,
            'data_quality': 'UNKNOWN'
        }

        # Fetch from BSE
        bse_data = self._fetch_bse_data(bse_code)
        if bse_data:
            report['data_sources']['BSE'] = bse_data

        # Fetch from NSE
        nse_data = self._fetch_nse_data(nse_symbol)
        if nse_data:
            report['data_sources']['NSE'] = nse_data

        # Fetch from Yahoo Finance (using existing implementation)
        yahoo_data = self._fetch_yahoo_data(nse_symbol)
        if yahoo_data:
            report['data_sources']['YAHOO'] = yahoo_data

        # Validate revenue YoY
        revenue_validation = self._validate_metric(
            'revenue_yoy',
            report['data_sources']
        )
        report['validation_results'].append(revenue_validation)

        # Validate profit YoY
        profit_validation = self._validate_metric(
            'profit_yoy',
            report['data_sources']
        )
        report['validation_results'].append(profit_validation)

        # Validate EPS
        eps_validation = self._validate_metric(
            'eps',
            report['data_sources']
        )
        report['validation_results'].append(eps_validation)

        # Calculate overall confidence
        if report['validation_results']:
            confidence_scores = [v.confidence_score for v in report['validation_results']]
            report['overall_confidence'] = np.mean(confidence_scores)

            # Determine data quality
            if report['overall_confidence'] >= 80:
                report['data_quality'] = 'HIGH'
            elif report['overall_confidence'] >= 60:
                report['data_quality'] = 'MEDIUM'
            elif report['overall_confidence'] >= 40:
                report['data_quality'] = 'LOW'
            else:
                report['data_quality'] = 'UNRELIABLE'

        # Add recommendations
        report['recommendations'] = self._generate_recommendations(report)

        return report

    def _fetch_bse_data(self, bse_code: str) -> Optional[Dict]:
        """Fetch and structure BSE data"""
        try:
            results = self.bse_fetcher.fetch_latest_results(bse_code)
            if results and results.get('status') == 'success':
                return {
                    'revenue_yoy': results.get('revenue_yoy'),
                    'profit_yoy': results.get('profit_yoy'),
                    'fetch_time': results.get('fetch_timestamp', {}).get('timestamp'),
                    'source': 'BSE',
                    'raw_data': results
                }
        except Exception as e:
            print(f"BSE fetch error: {e}")
        return None

    def _fetch_nse_data(self, nse_symbol: str) -> Optional[Dict]:
        """Fetch and structure NSE data"""
        try:
            results = self.nse_fetcher.fetch_financial_results(nse_symbol)
            if results and results.get('status') == 'success':
                yoy = results.get('yoy_growth', {})
                latest_quarter = results.get('quarterly_results', [{}])[0] if results.get('quarterly_results') else {}

                return {
                    'revenue_yoy': yoy.get('revenue_yoy'),
                    'profit_yoy': yoy.get('profit_yoy'),
                    'eps': latest_quarter.get('eps'),
                    'fetch_time': results.get('fetch_timestamp', {}).get('timestamp'),
                    'source': 'NSE',
                    'raw_data': results
                }
        except Exception as e:
            print(f"NSE fetch error: {e}")
        return None

    def _fetch_yahoo_data(self, nse_symbol: str) -> Optional[Dict]:
        """Fetch and structure Yahoo Finance data"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{nse_symbol}.NS")
            info = ticker.info

            # Get quarterly financials
            financials = ticker.quarterly_financials

            if financials is not None and len(financials.columns) >= 5:
                # Calculate YoY from quarterly data
                latest = financials.iloc[:, 0]
                year_ago = financials.iloc[:, 4]

                revenue_latest = latest.get('Total Revenue', 0)
                revenue_year_ago = year_ago.get('Total Revenue', 0)

                if revenue_year_ago:
                    revenue_yoy = ((revenue_latest - revenue_year_ago) / abs(revenue_year_ago)) * 100
                else:
                    revenue_yoy = None

                return {
                    'revenue_yoy': revenue_yoy,
                    'market_cap': info.get('marketCap'),
                    'current_price': info.get('currentPrice'),
                    'eps': info.get('trailingEps'),
                    'fetch_time': datetime.now().isoformat(),
                    'source': 'YAHOO',
                    'raw_data': info
                }
        except Exception as e:
            print(f"Yahoo fetch error: {e}")
        return None

    def _validate_metric(self, metric: str, sources: Dict) -> ValidationResult:
        """
        Validate a specific metric across sources

        Args:
            metric: Name of metric to validate
            sources: Dict of source data

        Returns:
            ValidationResult with confidence score
        """
        values = {}
        for source_name, source_data in sources.items():
            if source_data and metric in source_data:
                value = source_data[metric]
                if value is not None:
                    values[source_name] = value

        # If no data available
        if not values:
            return ValidationResult(
                metric=metric,
                sources={},
                discrepancy_pct=100,
                confidence_score=0,
                recommended_value=None,
                reason="No data available from any source",
                timestamp=DataTimestamp.create_timestamp()
            )

        # If only one source
        if len(values) == 1:
            source = list(values.keys())[0]
            value = list(values.values())[0]

            # Check against validation rules
            rule = self.validation_rules.get(metric, {})
            if rule:
                if value < rule.get('min', float('-inf')) or value > rule.get('max', float('inf')):
                    confidence = 30  # Low confidence if outside bounds
                    reason = f"Value {value} outside expected range [{rule.get('min')}, {rule.get('max')}]"
                else:
                    confidence = 60  # Medium confidence with single source
                    reason = f"Only one source ({source}) available"
            else:
                confidence = 50
                reason = "Single source, no validation rules"

            return ValidationResult(
                metric=metric,
                sources=values,
                discrepancy_pct=0,
                confidence_score=confidence,
                recommended_value=value,
                reason=reason,
                timestamp=DataTimestamp.create_timestamp()
            )

        # Multiple sources - calculate discrepancy
        values_list = list(values.values())
        mean_value = np.mean(values_list)
        std_value = np.std(values_list)

        if mean_value != 0:
            discrepancy_pct = (std_value / abs(mean_value)) * 100
        else:
            discrepancy_pct = 0 if std_value == 0 else 100

        # Calculate confidence based on discrepancy
        rule = self.validation_rules.get(metric, {})
        tolerance = rule.get('tolerance', 10)

        if discrepancy_pct <= tolerance:
            confidence = 90  # High confidence if sources agree
            reason = f"Sources agree within {tolerance}% tolerance"
            recommended = mean_value
        elif discrepancy_pct <= tolerance * 2:
            confidence = 70  # Medium-high confidence
            reason = f"Moderate discrepancy ({discrepancy_pct:.1f}%) between sources"
            # Use median for robustness
            recommended = np.median(values_list)
        elif discrepancy_pct <= tolerance * 3:
            confidence = 50  # Medium confidence
            reason = f"High discrepancy ({discrepancy_pct:.1f}%) between sources"
            # Weight by source reliability
            recommended = self._weighted_average(values)
        else:
            confidence = 20  # Low confidence
            reason = f"Very high discrepancy ({discrepancy_pct:.1f}%) - data unreliable"
            recommended = None

        # Check if recommended value is within bounds
        if recommended is not None and rule:
            if recommended < rule.get('min', float('-inf')) or recommended > rule.get('max', float('inf')):
                confidence *= 0.5  # Halve confidence if outside bounds
                reason += f" | Value outside expected range"

        return ValidationResult(
            metric=metric,
            sources=values,
            discrepancy_pct=discrepancy_pct,
            confidence_score=confidence,
            recommended_value=recommended,
            reason=reason,
            timestamp=DataTimestamp.create_timestamp()
        )

    def _weighted_average(self, values: Dict) -> float:
        """Calculate weighted average based on source reliability"""
        weights = {
            'BSE': 0.35,
            'NSE': 0.35,
            'YAHOO': 0.20,
            'SCREENER': 0.10
        }

        weighted_sum = 0
        weight_total = 0

        for source, value in values.items():
            weight = weights.get(source, 0.1)
            weighted_sum += value * weight
            weight_total += weight

        return weighted_sum / weight_total if weight_total > 0 else np.mean(list(values.values()))

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate actionable recommendations based on validation"""
        recommendations = []

        confidence = report.get('overall_confidence', 0)
        quality = report.get('data_quality', 'UNKNOWN')

        if quality == 'UNRELIABLE':
            recommendations.append("⚠️ Data quality is unreliable. Manual verification required.")
            recommendations.append("📋 Check official company announcements on BSE/NSE.")

        elif quality == 'LOW':
            recommendations.append("⚠️ Data quality is low. Use with caution.")
            recommendations.append("🔍 Cross-check with company's investor presentation.")

        elif quality == 'MEDIUM':
            recommendations.append("✓ Data quality is acceptable for preliminary analysis.")
            recommendations.append("📊 Consider waiting for official quarterly results.")

        else:  # HIGH
            recommendations.append("✅ Data quality is high. Safe to use for analysis.")

        # Check for specific issues
        for validation in report.get('validation_results', []):
            if validation.discrepancy_pct > 20:
                recommendations.append(
                    f"🔍 Large discrepancy in {validation.metric}: {validation.discrepancy_pct:.1f}%"
                )

        return recommendations


# Test the validator
if __name__ == "__main__":
    validator = DataAccuracyValidator()

    print("Testing Data Accuracy Validator")
    print("=" * 60)

    # Test with TCS
    print("\nValidating TCS data...")
    report = validator.validate_company_data("532540", "TCS")

    print(f"\nValidation Report for TCS")
    print("-" * 60)
    print(f"Overall Confidence: {report['overall_confidence']:.1f}%")
    print(f"Data Quality: {report['data_quality']}")

    print(f"\nData Sources Found: {list(report['data_sources'].keys())}")

    print(f"\nValidation Results:")
    for validation in report['validation_results']:
        print(f"\n{validation.metric}:")
        print(f"  Sources: {validation.sources}")
        print(f"  Discrepancy: {validation.discrepancy_pct:.1f}%")
        print(f"  Confidence: {validation.confidence_score:.1f}%")
        print(f"  Recommended Value: {validation.recommended_value}")
        print(f"  Reason: {validation.reason}")

    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")