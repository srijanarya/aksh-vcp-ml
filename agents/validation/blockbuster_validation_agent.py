"""
Blockbuster Scanner Validation Integration Agent
Enhances blockbuster detection with multi-source validation and confidence scoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

from data_sources.data_accuracy_validator import DataAccuracyValidator
from data_sources.validation_database import ValidationDatabase
from data_sources.screener_enhanced_fetcher import ScreenerEnhancedFetcher
from utils.fiscal_year_utils import IndianFiscalYear, DataTimestamp


class BlockbusterValidationAgent:
    """
    Integrates data validation into blockbuster scanning
    Ensures only high-confidence data is used for trading decisions
    """

    def __init__(self, min_confidence: float = 60.0):
        """
        Initialize the validation agent

        Args:
            min_confidence: Minimum confidence score to consider data reliable
        """
        self.min_confidence = min_confidence
        self.validator = DataAccuracyValidator()
        self.db = ValidationDatabase("blockbuster_validation.db")
        self.screener_fetcher = ScreenerEnhancedFetcher()

    def validate_blockbuster_candidate(self, bse_code: str, nse_symbol: str,
                                      existing_data: Dict = None) -> Dict:
        """
        Validate a potential blockbuster stock with multi-source verification

        Args:
            bse_code: BSE scrip code
            nse_symbol: NSE symbol
            existing_data: Any existing analysis data

        Returns:
            Enhanced validation report with blockbuster signals
        """
        timestamp = DataTimestamp.create_timestamp()

        # Get validated data from multiple sources
        validation_report = self.validator.validate_company_data(bse_code, nse_symbol)

        # Save validation to database
        self.db.save_confidence_score(nse_symbol, validation_report)

        # Enhance with Screener data if available
        screener_data = self.screener_fetcher.fetch_company_data(nse_symbol)
        if screener_data and screener_data.get('status') == 'success':
            validation_report['data_sources']['SCREENER_ENHANCED'] = screener_data

        # Calculate blockbuster signals
        blockbuster_signals = self._calculate_blockbuster_signals(validation_report, existing_data)

        # Build comprehensive report
        report = {
            'bse_code': bse_code,
            'nse_symbol': nse_symbol,
            'validation_timestamp': timestamp,
            'overall_confidence': validation_report.get('overall_confidence', 0),
            'data_quality': validation_report.get('data_quality', 'UNKNOWN'),
            'blockbuster_signals': blockbuster_signals,
            'validation_details': validation_report,
            'tradeable': self._is_tradeable(validation_report, blockbuster_signals),
            'risk_assessment': self._assess_risk(validation_report, blockbuster_signals)
        }

        # Save validation results
        for validation in validation_report.get('validation_results', []):
            validation['company_code'] = nse_symbol
            self.db.save_validation_result(validation)

        # Log any significant discrepancies
        self._log_discrepancies(nse_symbol, validation_report)

        return report

    def _calculate_blockbuster_signals(self, validation_report: Dict,
                                       existing_data: Dict = None) -> Dict:
        """
        Calculate blockbuster signals based on validated data

        Returns:
            Dictionary of blockbuster indicators
        """
        signals = {
            'earnings_momentum': False,
            'revenue_acceleration': False,
            'margin_expansion': False,
            'volume_surge': False,
            'technical_breakout': False,
            'confidence_weighted_score': 0.0
        }

        # Extract validated metrics
        validated_metrics = {}
        for validation in validation_report.get('validation_results', []):
            if validation.recommended_value is not None:
                validated_metrics[validation.metric] = {
                    'value': validation.recommended_value,
                    'confidence': validation.confidence_score
                }

        # Check earnings momentum (YoY growth > 25% with high confidence)
        if 'profit_yoy' in validated_metrics:
            profit_data = validated_metrics['profit_yoy']
            if profit_data['value'] > 25 and profit_data['confidence'] > 70:
                signals['earnings_momentum'] = True

        # Check revenue acceleration (YoY > 15% and QoQ > 5%)
        if 'revenue_yoy' in validated_metrics:
            revenue_data = validated_metrics['revenue_yoy']
            if revenue_data['value'] > 15 and revenue_data['confidence'] > 70:
                signals['revenue_acceleration'] = True

        # Check for margin expansion (if profit growth > revenue growth)
        if ('profit_yoy' in validated_metrics and 'revenue_yoy' in validated_metrics):
            profit_growth = validated_metrics['profit_yoy']['value']
            revenue_growth = validated_metrics['revenue_yoy']['value']
            if profit_growth > revenue_growth + 5:  # 5% margin expansion threshold
                signals['margin_expansion'] = True

        # Check volume and technical signals from existing data
        if existing_data:
            if existing_data.get('volume_ratio', 0) > 1.5:
                signals['volume_surge'] = True
            if existing_data.get('price_breakout', False):
                signals['technical_breakout'] = True

        # Calculate confidence-weighted composite score
        score = 0
        weights = {
            'earnings_momentum': 30,
            'revenue_acceleration': 25,
            'margin_expansion': 20,
            'volume_surge': 15,
            'technical_breakout': 10
        }

        for signal, weight in weights.items():
            if signals[signal]:
                # Weight by overall confidence
                confidence_multiplier = validation_report.get('overall_confidence', 50) / 100
                score += weight * confidence_multiplier

        signals['confidence_weighted_score'] = score
        signals['signal_count'] = sum(1 for k, v in signals.items()
                                     if k != 'confidence_weighted_score' and v)

        return signals

    def _is_tradeable(self, validation_report: Dict, signals: Dict) -> Dict:
        """
        Determine if the stock is tradeable based on validation and signals

        Returns:
            Tradeability assessment
        """
        confidence = validation_report.get('overall_confidence', 0)
        quality = validation_report.get('data_quality', 'UNKNOWN')
        signal_score = signals.get('confidence_weighted_score', 0)
        signal_count = signals.get('signal_count', 0)

        # Define tradeability criteria
        tradeable = {
            'is_tradeable': False,
            'confidence_pass': confidence >= self.min_confidence,
            'quality_pass': quality in ['HIGH', 'MEDIUM'],
            'signal_pass': signal_score >= 40 or signal_count >= 3,
            'reasons': []
        }

        if not tradeable['confidence_pass']:
            tradeable['reasons'].append(f"Confidence too low: {confidence:.1f}% < {self.min_confidence}%")

        if not tradeable['quality_pass']:
            tradeable['reasons'].append(f"Data quality insufficient: {quality}")

        if not tradeable['signal_pass']:
            tradeable['reasons'].append(f"Insufficient signals: Score {signal_score:.1f}, Count {signal_count}")

        # Overall tradeability
        tradeable['is_tradeable'] = (tradeable['confidence_pass'] and
                                    tradeable['quality_pass'] and
                                    tradeable['signal_pass'])

        if tradeable['is_tradeable']:
            tradeable['reasons'] = ["All validation criteria met"]

        return tradeable

    def _assess_risk(self, validation_report: Dict, signals: Dict) -> Dict:
        """
        Assess risk factors based on data quality and signals

        Returns:
            Risk assessment dictionary
        """
        risk = {
            'risk_level': 'UNKNOWN',
            'data_risk': 'LOW',
            'signal_risk': 'LOW',
            'factors': []
        }

        confidence = validation_report.get('overall_confidence', 0)

        # Assess data risk
        if confidence < 40:
            risk['data_risk'] = 'HIGH'
            risk['factors'].append("Very low data confidence")
        elif confidence < 60:
            risk['data_risk'] = 'MEDIUM'
            risk['factors'].append("Moderate data confidence")
        else:
            risk['data_risk'] = 'LOW'

        # Check for large discrepancies
        for validation in validation_report.get('validation_results', []):
            if validation.discrepancy_pct > 20:
                risk['factors'].append(f"High discrepancy in {validation.metric}: {validation.discrepancy_pct:.1f}%")
                if risk['data_risk'] == 'LOW':
                    risk['data_risk'] = 'MEDIUM'

        # Assess signal risk
        signal_count = signals.get('signal_count', 0)
        if signal_count < 2:
            risk['signal_risk'] = 'HIGH'
            risk['factors'].append("Insufficient confirming signals")
        elif signal_count < 3:
            risk['signal_risk'] = 'MEDIUM'
            risk['factors'].append("Limited confirming signals")
        else:
            risk['signal_risk'] = 'LOW'

        # Overall risk level
        if risk['data_risk'] == 'HIGH' or risk['signal_risk'] == 'HIGH':
            risk['risk_level'] = 'HIGH'
        elif risk['data_risk'] == 'MEDIUM' or risk['signal_risk'] == 'MEDIUM':
            risk['risk_level'] = 'MEDIUM'
        else:
            risk['risk_level'] = 'LOW'

        return risk

    def _log_discrepancies(self, company_code: str, validation_report: Dict):
        """Log significant discrepancies to database"""
        for validation in validation_report.get('validation_results', []):
            if validation.discrepancy_pct > 15:  # Log discrepancies > 15%
                sources = validation.sources
                if len(sources) >= 2:
                    source_items = list(sources.items())
                    self.db.log_discrepancy(
                        company_code,
                        validation.metric,
                        source_items[0][0], source_items[0][1],
                        source_items[1][0], source_items[1][1],
                        f"Resolved to {validation.recommended_value} - {validation.reason}"
                    )

    def batch_validate_blockbusters(self, candidates: List[Tuple[str, str]],
                                   existing_analysis: Dict = None) -> pd.DataFrame:
        """
        Validate multiple blockbuster candidates

        Args:
            candidates: List of (bse_code, nse_symbol) tuples
            existing_analysis: Dictionary of existing analysis by symbol

        Returns:
            DataFrame with validation results
        """
        results = []

        for bse_code, nse_symbol in candidates:
            print(f"Validating {nse_symbol}...")

            existing_data = None
            if existing_analysis and nse_symbol in existing_analysis:
                existing_data = existing_analysis[nse_symbol]

            try:
                validation = self.validate_blockbuster_candidate(
                    bse_code, nse_symbol, existing_data
                )

                # Extract key metrics for DataFrame
                result = {
                    'Symbol': nse_symbol,
                    'BSE_Code': bse_code,
                    'Confidence': validation['overall_confidence'],
                    'Quality': validation['data_quality'],
                    'Tradeable': validation['tradeable']['is_tradeable'],
                    'Risk': validation['risk_assessment']['risk_level'],
                    'Signal_Score': validation['blockbuster_signals']['confidence_weighted_score'],
                    'Signal_Count': validation['blockbuster_signals']['signal_count'],
                    'Earnings_Momentum': validation['blockbuster_signals']['earnings_momentum'],
                    'Revenue_Acceleration': validation['blockbuster_signals']['revenue_acceleration'],
                    'Margin_Expansion': validation['blockbuster_signals']['margin_expansion']
                }

                # Add validated metrics
                for v in validation['validation_details'].get('validation_results', []):
                    if v.recommended_value is not None:
                        result[f'{v.metric}_validated'] = v.recommended_value
                        result[f'{v.metric}_confidence'] = v.confidence_score

                results.append(result)

            except Exception as e:
                print(f"Error validating {nse_symbol}: {e}")
                results.append({
                    'Symbol': nse_symbol,
                    'BSE_Code': bse_code,
                    'Confidence': 0,
                    'Quality': 'ERROR',
                    'Tradeable': False,
                    'Risk': 'HIGH',
                    'Error': str(e)
                })

        # Create DataFrame and sort by signal score
        df = pd.DataFrame(results)
        if 'Signal_Score' in df.columns:
            df = df.sort_values('Signal_Score', ascending=False)

        return df

    def generate_validation_summary(self) -> Dict:
        """
        Generate summary of validation activities

        Returns:
            Summary report
        """
        summary = {
            'generated_at': DataTimestamp.create_timestamp(),
            'quality_report': self.db.generate_quality_report(),
            'statistics': {}
        }

        # Get validation statistics from last 24 hours
        cursor = self.db.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(DISTINCT company_code) as companies_validated,
                COUNT(*) as total_validations,
                AVG(confidence_score) as avg_confidence
            FROM validation_results
            WHERE validation_timestamp >= datetime('now', '-24 hours')
        """)

        result = cursor.fetchone()
        if result:
            summary['statistics']['24h'] = {
                'companies_validated': result[0],
                'total_validations': result[1],
                'avg_confidence': result[2]
            }

        # Get tradeable stocks count
        cursor.execute("""
            SELECT COUNT(DISTINCT company_code)
            FROM confidence_scores
            WHERE overall_confidence >= ? AND timestamp >= datetime('now', '-24 hours')
        """, (self.min_confidence,))

        result = cursor.fetchone()
        if result:
            summary['statistics']['tradeable_stocks'] = result[0]

        return summary

    def close(self):
        """Clean up resources"""
        self.db.close()


# Agent execution function for integration
def validate_blockbuster(bse_code: str, nse_symbol: str,
                         min_confidence: float = 60.0) -> Dict:
    """
    Standalone function to validate a blockbuster candidate

    Args:
        bse_code: BSE scrip code
        nse_symbol: NSE symbol
        min_confidence: Minimum confidence threshold

    Returns:
        Validation report
    """
    agent = BlockbusterValidationAgent(min_confidence)
    result = agent.validate_blockbuster_candidate(bse_code, nse_symbol)
    agent.close()
    return result


# Test the agent
if __name__ == "__main__":
    agent = BlockbusterValidationAgent(min_confidence=60.0)

    print("Testing Blockbuster Validation Agent")
    print("=" * 60)

    # Test single validation
    print("\nValidating TCS as blockbuster candidate...")
    validation = agent.validate_blockbuster_candidate("532540", "TCS")

    print(f"\nValidation Results:")
    print(f"Symbol: TCS")
    print(f"Overall Confidence: {validation['overall_confidence']:.1f}%")
    print(f"Data Quality: {validation['data_quality']}")
    print(f"Tradeable: {validation['tradeable']['is_tradeable']}")
    print(f"Risk Level: {validation['risk_assessment']['risk_level']}")

    print(f"\nBlockbuster Signals:")
    signals = validation['blockbuster_signals']
    print(f"  Earnings Momentum: {signals['earnings_momentum']}")
    print(f"  Revenue Acceleration: {signals['revenue_acceleration']}")
    print(f"  Margin Expansion: {signals['margin_expansion']}")
    print(f"  Signal Score: {signals['confidence_weighted_score']:.1f}/100")

    # Test batch validation
    print("\n\nTesting Batch Validation...")
    print("-" * 60)

    candidates = [
        ("532540", "TCS"),
        ("500325", "RELIANCE"),
        ("532174", "ICICIBANK")
    ]

    df = agent.batch_validate_blockbusters(candidates)
    print("\nBatch Validation Results:")
    print(df[['Symbol', 'Confidence', 'Quality', 'Tradeable', 'Risk', 'Signal_Score']].to_string())

    # Generate summary
    print("\n\nGenerating Validation Summary...")
    summary = agent.generate_validation_summary()
    if summary['statistics'].get('24h'):
        stats = summary['statistics']['24h']
        print(f"Last 24 Hours:")
        print(f"  Companies Validated: {stats.get('companies_validated', 0)}")
        print(f"  Total Validations: {stats.get('total_validations', 0)}")
        print(f"  Average Confidence: {stats.get('avg_confidence', 0):.1f}%")

    agent.close()
    print("\n✅ Blockbuster Validation Agent test complete!")