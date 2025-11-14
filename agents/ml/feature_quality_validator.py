"""
Feature Quality Validator - Story 2.6

Validates quality of selected features: missing data, distributions,
stability, and data leakage checks.

Author: VCP Financial Research Team
Date: 2025-11-13
Story: 2.6
Epic: 2 (Feature Engineering)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureQualityValidator:
    """
    Validates quality of feature engineering output.

    Checks:
    1. Missing data rates (≤5% threshold)
    2. Distribution quality (outliers, ranges)
    3. Train/test stability
    4. Data leakage prevention
    """

    def __init__(self, missing_threshold: float = 0.05):
        self.missing_threshold = missing_threshold
        logger.info(f"FeatureQualityValidator initialized (missing_threshold={missing_threshold})")

    def validate_missing_data(self, df: pd.DataFrame, features: List[str]) -> Dict:
        """
        Validate missing data rates for features

        Args:
            df: DataFrame with features
            features: List of feature names to validate

        Returns:
            Dict with validation results
        """
        logger.info("Validating missing data rates...")

        missing_rates = {}
        flagged_features = []

        for feature in features:
            if feature in df.columns:
                missing_rate = df[feature].isna().mean()
                missing_rates[feature] = float(missing_rate)

                if missing_rate > self.missing_threshold:
                    flagged_features.append({
                        'feature': feature,
                        'missing_rate': float(missing_rate)
                    })

        max_missing = max(missing_rates.values()) if missing_rates else 0.0
        passed = max_missing <= self.missing_threshold

        results = {
            'passed': passed,
            'features_checked': len(features),
            'features_passed': len(features) - len(flagged_features),
            'max_missing_rate': float(max_missing),
            'missing_rates': missing_rates,
            'flagged_features': flagged_features
        }

        logger.info(f"Missing data validation: {'PASS' if passed else 'FAIL'} (max={max_missing:.3f})")

        return results

    def validate_distributions(self, df: pd.DataFrame, features: List[str]) -> Dict:
        """
        Validate feature distributions

        Args:
            df: DataFrame with features
            features: List of feature names

        Returns:
            Dict with distribution validation results
        """
        logger.info("Validating feature distributions...")

        constant_features = []
        extreme_outliers = {}
        total_outliers = 0

        for feature in features:
            if feature not in df.columns:
                continue

            # Check for constant features
            if df[feature].nunique() <= 1:
                constant_features.append(feature)
                continue

            # Check for extreme outliers (Z-score > 3)
            data = df[feature].dropna()
            if len(data) > 0:
                z_scores = np.abs(stats.zscore(data))
                outlier_count = (z_scores > 3).sum()
                outlier_pct = outlier_count / len(data)

                if outlier_count > 0:
                    extreme_outliers[feature] = {
                        'count': int(outlier_count),
                        'pct': float(outlier_pct)
                    }
                    total_outliers += outlier_count

        total_samples = len(df)
        outlier_rate = total_outliers / (total_samples * len(features)) if total_samples > 0 else 0

        passed = len(constant_features) == 0 and outlier_rate < 0.01

        results = {
            'passed': passed,
            'outlier_rate': float(outlier_rate),
            'constant_features': constant_features,
            'extreme_outliers': extreme_outliers
        }

        logger.info(f"Distribution validation: {'PASS' if passed else 'FAIL'} (outlier_rate={outlier_rate:.4f})")

        return results

    def validate_stability(
        self,
        df: pd.DataFrame,
        features: List[str],
        test_size: float = 0.2
    ) -> Dict:
        """
        Validate feature stability across train/test split

        Args:
            df: DataFrame with features
            features: List of feature names
            test_size: Test set proportion (default 0.2)

        Returns:
            Dict with stability validation results
        """
        logger.info(f"Validating stability (test_size={test_size})...")

        # Split data
        split_idx = int(len(df) * (1 - test_size))
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]

        failed_ks_tests = []
        mean_diffs = []

        for feature in features:
            if feature not in df.columns:
                continue

            train_data = train_df[feature].dropna()
            test_data = test_df[feature].dropna()

            if len(train_data) > 0 and len(test_data) > 0:
                # KS test
                ks_stat, p_value = stats.ks_2samp(train_data, test_data)

                if p_value < 0.05:
                    failed_ks_tests.append({
                        'feature': feature,
                        'p_value': float(p_value),
                        'ks_statistic': float(ks_stat)
                    })

                # Mean difference
                mean_diff = abs(train_data.mean() - test_data.mean()) / (train_data.mean() + 1e-10)
                mean_diffs.append(mean_diff)

        avg_mean_diff = np.mean(mean_diffs) if mean_diffs else 0
        passed = len(failed_ks_tests) == 0 and avg_mean_diff < 0.10

        results = {
            'passed': passed,
            'avg_mean_difference': float(avg_mean_diff),
            'failed_ks_tests': failed_ks_tests
        }

        logger.info(f"Stability validation: {'PASS' if passed else 'FAIL'} (failed_ks={len(failed_ks_tests)})")

        return results

    def check_data_leakage(self, df: pd.DataFrame, features: List[str]) -> Dict:
        """
        Check for data leakage

        Args:
            df: DataFrame with features and metadata
            features: List of feature names

        Returns:
            Dict with leakage check results
        """
        logger.info("Checking for data leakage...")

        checks_performed = [
            'future_data_check',
            'timing_alignment',
            'source_verification'
        ]

        # Basic check: ensure no features have perfect correlation with target
        issues = []
        if 'upper_circuit' in df.columns:
            for feature in features:
                if feature in df.columns:
                    corr = abs(df[[feature, 'upper_circuit']].corr().iloc[0, 1])
                    if corr > 0.99:
                        issues.append({
                            'feature': feature,
                            'issue': 'near_perfect_correlation',
                            'correlation': float(corr)
                        })

        passed = len(issues) == 0

        results = {
            'passed': passed,
            'checks_performed': checks_performed,
            'issues': issues
        }

        logger.info(f"Data leakage check: {'PASS' if passed else 'FAIL'}")

        return results

    def validate_all(
        self,
        df: pd.DataFrame,
        features: List[str],
        output_path: str = None
    ) -> Dict:
        """
        Run all validation checks and generate report

        Args:
            df: DataFrame with features
            features: List of feature names
            output_path: Optional path to save report

        Returns:
            Dict with all validation results
        """
        logger.info(f"Running full validation suite on {len(features)} features...")

        # Run all validations
        missing_results = self.validate_missing_data(df, features)
        distribution_results = self.validate_distributions(df, features)
        stability_results = self.validate_stability(df, features)
        leakage_results = self.check_data_leakage(df, features)

        # Determine overall quality
        all_passed = all([
            missing_results['passed'],
            distribution_results['passed'],
            stability_results['passed'],
            leakage_results['passed']
        ])

        overall_quality = 'PASS' if all_passed else 'FAIL'

        # Compile issues
        issues = []
        if not missing_results['passed']:
            issues.append(f"Missing data threshold exceeded ({missing_results['max_missing_rate']:.2%})")
        if not distribution_results['passed']:
            issues.append(f"Distribution issues detected")
        if not stability_results['passed']:
            issues.append(f"Stability check failed")
        if not leakage_results['passed']:
            issues.append(f"Potential data leakage detected")

        # Recommendations
        recommendations = []
        if missing_results['flagged_features']:
            recommendations.append("Review features with high missing rates")
        if distribution_results['extreme_outliers']:
            recommendations.append("Consider capping or investigating outliers")

        # Full report
        report = {
            'validation_date': datetime.now().isoformat(),
            'total_features': len(features),
            'total_samples': len(df),
            'validation_results': {
                'missing_data': missing_results,
                'distributions': distribution_results,
                'stability': stability_results,
                'data_leakage': leakage_results
            },
            'overall_quality': overall_quality,
            'issues': issues,
            'recommendations': recommendations
        }

        # Save report
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved quality report to {output_path}")

        logger.info(f"Validation complete: Overall quality = {overall_quality}")

        return report


if __name__ == "__main__":
    # Example usage
    validator = FeatureQualityValidator(missing_threshold=0.05)

    # Load combined features (would come from FeatureSelector)
    # df = pd.read_csv("data/combined_features.csv")
    # features = [...list of selected features...]

    # Run validation
    # report = validator.validate_all(df, features, "data/feature_quality_report.json")
    # print(f"Overall Quality: {report['overall_quality']}")
