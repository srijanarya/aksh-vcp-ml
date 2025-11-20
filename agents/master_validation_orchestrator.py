"""
Master Validation Orchestrator Agent
Coordinates all validation components for comprehensive data quality management
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional, Tuple, Any
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Import all validation components
from data_sources.data_accuracy_validator import DataAccuracyValidator
from data_sources.validation_database import ValidationDatabase
from data_sources.screener_enhanced_fetcher import ScreenerEnhancedFetcher
from data_sources.bse_direct_fetcher import BSEDirectFetcher
from data_sources.nse_direct_fetcher import NSEDirectFetcher
from agents.validation.blockbuster_validation_agent import BlockbusterValidationAgent
from agents.ml.ml_data_quality_filter import MLDataQualityFilter
from reports.data_quality_report_generator import DataQualityReportGenerator
from utils.fiscal_year_utils import DataTimestamp, IndianFiscalYear
from market_status_dashboard import MarketStatusDashboard


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MasterValidationOrchestrator')


class MasterValidationOrchestrator:
    """
    Master orchestrator that coordinates all validation activities
    Provides unified interface for data quality management
    """

    def __init__(self, config: Dict = None):
        """
        Initialize the master orchestrator

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()

        # Initialize all components
        self.validator = DataAccuracyValidator()
        self.db = ValidationDatabase(self.config['db_path'])
        self.screener = ScreenerEnhancedFetcher()
        self.bse_fetcher = BSEDirectFetcher()
        self.nse_fetcher = NSEDirectFetcher()
        self.blockbuster_agent = BlockbusterValidationAgent(self.config['min_confidence'])
        self.ml_filter = MLDataQualityFilter(self.config['min_confidence'])
        self.report_generator = DataQualityReportGenerator(
            self.config['db_path'],
            self.config['report_dir']
        )
        self.dashboard = MarketStatusDashboard()

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.config['max_workers'])

        # Tracking metrics
        self.metrics = {
            'validations_performed': 0,
            'companies_processed': 0,
            'reports_generated': 0,
            'errors_encountered': 0,
            'start_time': datetime.now()
        }

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'db_path': 'master_validation.db',
            'report_dir': 'validation_reports',
            'min_confidence': 60.0,
            'max_workers': 4,
            'cache_ttl_hours': 6,
            'batch_size': 10,
            'enable_ml_filter': True,
            'enable_blockbuster': True,
            'enable_reporting': True
        }

    async def validate_company_async(self, bse_code: str, nse_symbol: str,
                                    include_peers: bool = False) -> Dict:
        """
        Asynchronously validate a company with all available validators

        Args:
            bse_code: BSE scrip code
            nse_symbol: NSE symbol
            include_peers: Whether to include peer comparison

        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting validation for {nse_symbol}")

        validation_report = {
            'company': {
                'bse_code': bse_code,
                'nse_symbol': nse_symbol
            },
            'timestamp': DataTimestamp.create_timestamp(),
            'validation_results': {},
            'errors': []
        }

        # Run validations in parallel
        futures = []

        # Core validation
        futures.append(
            self.executor.submit(self._run_core_validation, bse_code, nse_symbol)
        )

        # Blockbuster validation if enabled
        if self.config['enable_blockbuster']:
            futures.append(
                self.executor.submit(self._run_blockbuster_validation, bse_code, nse_symbol)
            )

        # Screener enhancement
        futures.append(
            self.executor.submit(self._run_screener_validation, nse_symbol)
        )

        # Peer comparison if requested
        if include_peers:
            futures.append(
                self.executor.submit(self._run_peer_comparison, nse_symbol)
            )

        # Collect results
        for future in as_completed(futures):
            try:
                result_type, result_data = future.result(timeout=30)
                validation_report['validation_results'][result_type] = result_data
            except Exception as e:
                logger.error(f"Validation error: {e}")
                validation_report['errors'].append(str(e))
                self.metrics['errors_encountered'] += 1

        # Calculate overall confidence
        validation_report['overall_assessment'] = self._assess_overall_quality(
            validation_report['validation_results']
        )

        # Save to database
        self.db.save_confidence_score(nse_symbol, validation_report['overall_assessment'])

        self.metrics['validations_performed'] += 1
        self.metrics['companies_processed'] += 1

        logger.info(f"Completed validation for {nse_symbol}")
        return validation_report

    def _run_core_validation(self, bse_code: str, nse_symbol: str) -> Tuple[str, Dict]:
        """Run core data validation"""
        try:
            result = self.validator.validate_company_data(bse_code, nse_symbol)
            return ('core_validation', result)
        except Exception as e:
            logger.error(f"Core validation failed: {e}")
            return ('core_validation', {'error': str(e)})

    def _run_blockbuster_validation(self, bse_code: str, nse_symbol: str) -> Tuple[str, Dict]:
        """Run blockbuster validation"""
        try:
            result = self.blockbuster_agent.validate_blockbuster_candidate(bse_code, nse_symbol)
            return ('blockbuster_validation', result)
        except Exception as e:
            logger.error(f"Blockbuster validation failed: {e}")
            return ('blockbuster_validation', {'error': str(e)})

    def _run_screener_validation(self, nse_symbol: str) -> Tuple[str, Dict]:
        """Run Screener.in validation"""
        try:
            result = self.screener.fetch_company_data(nse_symbol)
            return ('screener_validation', result)
        except Exception as e:
            logger.error(f"Screener validation failed: {e}")
            return ('screener_validation', {'error': str(e)})

    def _run_peer_comparison(self, nse_symbol: str) -> Tuple[str, Dict]:
        """Run peer comparison"""
        try:
            # Get default peers based on sector
            peers = self._get_default_peers(nse_symbol)
            result = self.screener.fetch_peer_comparison(nse_symbol, peers)
            return ('peer_comparison', result)
        except Exception as e:
            logger.error(f"Peer comparison failed: {e}")
            return ('peer_comparison', {'error': str(e)})

    def _get_default_peers(self, nse_symbol: str) -> List[str]:
        """Get default peer companies"""
        # Sector-based peer mapping
        peer_groups = {
            'TCS': ['INFY', 'WIPRO', 'HCLTECH', 'TECHM'],
            'INFY': ['TCS', 'WIPRO', 'HCLTECH', 'TECHM'],
            'RELIANCE': ['IOC', 'BPCL', 'ONGC'],
            'HDFCBANK': ['ICICIBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK'],
            'ICICIBANK': ['HDFCBANK', 'SBIN', 'AXISBANK', 'KOTAKBANK']
        }

        return peer_groups.get(nse_symbol, [])

    def _assess_overall_quality(self, validation_results: Dict) -> Dict:
        """Assess overall data quality from all validations"""
        assessment = {
            'overall_confidence': 0,
            'data_quality': 'UNKNOWN',
            'sources_validated': 0,
            'validation_summary': []
        }

        confidence_scores = []

        # Extract confidence from core validation
        if 'core_validation' in validation_results:
            core = validation_results['core_validation']
            if 'overall_confidence' in core:
                confidence_scores.append(core['overall_confidence'])
                assessment['validation_summary'].append({
                    'type': 'core',
                    'confidence': core['overall_confidence'],
                    'quality': core.get('data_quality', 'UNKNOWN')
                })

        # Extract confidence from blockbuster validation
        if 'blockbuster_validation' in validation_results:
            blockbuster = validation_results['blockbuster_validation']
            if 'overall_confidence' in blockbuster:
                confidence_scores.append(blockbuster['overall_confidence'])
                assessment['validation_summary'].append({
                    'type': 'blockbuster',
                    'confidence': blockbuster['overall_confidence'],
                    'tradeable': blockbuster.get('tradeable', {}).get('is_tradeable', False)
                })

        # Extract confidence from screener validation
        if 'screener_validation' in validation_results:
            screener = validation_results['screener_validation']
            if 'confidence_score' in screener:
                confidence_scores.append(screener['confidence_score'])
                assessment['validation_summary'].append({
                    'type': 'screener',
                    'confidence': screener['confidence_score'],
                    'completeness': screener.get('data_completeness', 0)
                })

        # Calculate overall confidence
        if confidence_scores:
            assessment['overall_confidence'] = sum(confidence_scores) / len(confidence_scores)

            # Determine quality level
            if assessment['overall_confidence'] >= 80:
                assessment['data_quality'] = 'HIGH'
            elif assessment['overall_confidence'] >= 60:
                assessment['data_quality'] = 'MEDIUM'
            elif assessment['overall_confidence'] >= 40:
                assessment['data_quality'] = 'LOW'
            else:
                assessment['data_quality'] = 'UNRELIABLE'

        assessment['sources_validated'] = len(confidence_scores)

        return assessment

    def batch_validate(self, companies: List[Tuple[str, str]],
                      parallel: bool = True) -> pd.DataFrame:
        """
        Validate multiple companies in batch

        Args:
            companies: List of (bse_code, nse_symbol) tuples
            parallel: Whether to process in parallel

        Returns:
            DataFrame with validation results
        """
        logger.info(f"Starting batch validation for {len(companies)} companies")

        results = []

        if parallel:
            # Process in parallel batches
            batch_size = self.config['batch_size']
            for i in range(0, len(companies), batch_size):
                batch = companies[i:i+batch_size]

                # Create async tasks for batch
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                tasks = [
                    self.validate_company_async(bse_code, nse_symbol)
                    for bse_code, nse_symbol in batch
                ]

                batch_results = loop.run_until_complete(
                    asyncio.gather(*tasks, return_exceptions=True)
                )

                for (bse_code, nse_symbol), result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Failed to validate {nse_symbol}: {result}")
                        results.append({
                            'BSE_Code': bse_code,
                            'Symbol': nse_symbol,
                            'Status': 'ERROR',
                            'Error': str(result)
                        })
                    else:
                        results.append(self._extract_summary(result))

                loop.close()
        else:
            # Sequential processing
            for bse_code, nse_symbol in companies:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        self.validate_company_async(bse_code, nse_symbol)
                    )
                    results.append(self._extract_summary(result))
                    loop.close()
                except Exception as e:
                    logger.error(f"Failed to validate {nse_symbol}: {e}")
                    results.append({
                        'BSE_Code': bse_code,
                        'Symbol': nse_symbol,
                        'Status': 'ERROR',
                        'Error': str(e)
                    })

        # Create DataFrame
        df = pd.DataFrame(results)

        # Sort by confidence
        if 'Overall_Confidence' in df.columns:
            df = df.sort_values('Overall_Confidence', ascending=False)

        logger.info(f"Completed batch validation for {len(companies)} companies")
        return df

    def _extract_summary(self, validation_report: Dict) -> Dict:
        """Extract summary from validation report"""
        company = validation_report.get('company', {})
        assessment = validation_report.get('overall_assessment', {})

        summary = {
            'BSE_Code': company.get('bse_code'),
            'Symbol': company.get('nse_symbol'),
            'Overall_Confidence': assessment.get('overall_confidence', 0),
            'Data_Quality': assessment.get('data_quality', 'UNKNOWN'),
            'Sources_Validated': assessment.get('sources_validated', 0),
            'Status': 'SUCCESS'
        }

        # Add validation-specific results
        validations = validation_report.get('validation_results', {})

        if 'core_validation' in validations:
            core = validations['core_validation']
            for result in core.get('validation_results', []):
                if result.metric and result.recommended_value is not None:
                    summary[f'{result.metric}_validated'] = result.recommended_value
                    summary[f'{result.metric}_confidence'] = result.confidence_score

        if 'blockbuster_validation' in validations:
            blockbuster = validations['blockbuster_validation']
            if 'blockbuster_signals' in blockbuster:
                signals = blockbuster['blockbuster_signals']
                summary['Blockbuster_Score'] = signals.get('confidence_weighted_score', 0)
                summary['Tradeable'] = blockbuster.get('tradeable', {}).get('is_tradeable', False)

        return summary

    def generate_market_dashboard(self, symbols: List[Tuple[str, str]] = None) -> Dict:
        """
        Generate comprehensive market dashboard with validation

        Args:
            symbols: Optional list of (bse_code, nse_symbol) tuples

        Returns:
            Market dashboard data
        """
        logger.info("Generating market dashboard")

        dashboard = self.dashboard.generate_dashboard(symbols)

        # Enhance with validation data
        for stock in dashboard.get('stock_analysis', []):
            bse_code = stock.get('bse_code')
            nse_symbol = stock.get('nse_symbol')

            # Get latest validation from database
            validation = self.db.get_latest_validation(nse_symbol)
            if validation:
                stock['last_validated'] = validation.get('validation_timestamp')
                stock['validation_confidence'] = validation.get('confidence_score')

        self.metrics['reports_generated'] += 1

        return dashboard

    def generate_quality_report(self, company_code: str = None,
                              period_days: int = 7,
                              format: str = 'all') -> Dict[str, str]:
        """
        Generate comprehensive quality report

        Args:
            company_code: Optional company filter
            period_days: Period to analyze
            format: Output format

        Returns:
            Paths to generated reports
        """
        logger.info(f"Generating quality report for {company_code or 'system'}")

        files = self.report_generator.generate_comprehensive_report(
            company_code, period_days, format
        )

        self.metrics['reports_generated'] += 1

        return files

    def prepare_ml_data(self, df: pd.DataFrame,
                       feature_columns: List[str],
                       target_column: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Prepare data for ML training with quality filtering

        Args:
            df: Input DataFrame
            feature_columns: Feature column names
            target_column: Target column name

        Returns:
            Tuple of (filtered_df, quality_report)
        """
        logger.info("Preparing ML data with quality filtering")

        if self.config['enable_ml_filter']:
            return self.ml_filter.filter_training_data(df, feature_columns, target_column)
        else:
            return df, {'quality_filtering': 'disabled'}

    def get_orchestrator_metrics(self) -> Dict:
        """Get orchestrator performance metrics"""
        runtime = (datetime.now() - self.metrics['start_time']).total_seconds()

        return {
            'runtime_seconds': runtime,
            'validations_performed': self.metrics['validations_performed'],
            'companies_processed': self.metrics['companies_processed'],
            'reports_generated': self.metrics['reports_generated'],
            'errors_encountered': self.metrics['errors_encountered'],
            'avg_validation_time': runtime / max(1, self.metrics['validations_performed']),
            'success_rate': 1 - (self.metrics['errors_encountered'] /
                               max(1, self.metrics['validations_performed']))
        }

    def close(self):
        """Clean up resources"""
        logger.info("Shutting down master orchestrator")

        # Close all components
        self.db.close()
        self.blockbuster_agent.close()
        self.ml_filter.close()
        self.report_generator.close()
        self.executor.shutdown(wait=True)

        # Log final metrics
        metrics = self.get_orchestrator_metrics()
        logger.info(f"Final metrics: {metrics}")


# Convenience functions for standalone use
def validate_company(bse_code: str, nse_symbol: str) -> Dict:
    """Validate a single company"""
    orchestrator = MasterValidationOrchestrator()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        orchestrator.validate_company_async(bse_code, nse_symbol)
    )
    loop.close()
    orchestrator.close()
    return result


def validate_batch(companies: List[Tuple[str, str]]) -> pd.DataFrame:
    """Validate a batch of companies"""
    orchestrator = MasterValidationOrchestrator()
    df = orchestrator.batch_validate(companies)
    orchestrator.close()
    return df


# Test the orchestrator
if __name__ == "__main__":
    print("Testing Master Validation Orchestrator")
    print("=" * 60)

    # Initialize orchestrator
    config = {
        'min_confidence': 60.0,
        'enable_blockbuster': True,
        'enable_ml_filter': True,
        'enable_reporting': True
    }

    orchestrator = MasterValidationOrchestrator(config)

    # Test single company validation
    print("\nValidating TCS...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        orchestrator.validate_company_async("532540", "TCS", include_peers=True)
    )

    print(f"\nValidation Results for TCS:")
    print(f"Overall Confidence: {result['overall_assessment']['overall_confidence']:.1f}%")
    print(f"Data Quality: {result['overall_assessment']['data_quality']}")
    print(f"Sources Validated: {result['overall_assessment']['sources_validated']}")

    # Test batch validation
    print("\n\nTesting Batch Validation...")
    companies = [
        ("532540", "TCS"),
        ("500325", "RELIANCE"),
        ("532174", "ICICIBANK"),
        ("500209", "INFY")
    ]

    df = orchestrator.batch_validate(companies, parallel=True)
    print("\nBatch Validation Results:")
    print(df[['Symbol', 'Overall_Confidence', 'Data_Quality', 'Tradeable']].to_string())

    # Generate quality report
    print("\n\nGenerating Quality Report...")
    report_files = orchestrator.generate_quality_report(period_days=7, format='markdown')
    print(f"Generated reports: {report_files}")

    # Get orchestrator metrics
    print("\n\nOrchestrator Metrics:")
    metrics = orchestrator.get_orchestrator_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    loop.close()
    orchestrator.close()

    print("\n✅ Master Validation Orchestrator test complete!")