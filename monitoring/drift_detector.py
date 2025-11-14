"""
Data Drift Detector (Story 5.2)

Detects data drift in production using:
- Kolmogorov-Smirnov (KS) test for continuous features
- Population Stability Index (PSI) for all features
- Baseline distribution storage and comparison
- Automated daily drift detection
- Alert generation based on drift severity

Author: VCP ML Team
Created: 2025-11-14
"""

import numpy as np
import pandas as pd
import sqlite3
import json
from typing import Dict, Tuple, Optional, List, Any
from scipy.stats import ks_2samp
from datetime import datetime


class DriftDetector:
    """
    Data drift detector for production monitoring.

    Implements:
    - KS test for continuous distributions
    - PSI calculation for all features
    - Baseline storage in SQLite
    - Drift report generation
    - Alert severity determination
    """

    def __init__(
        self,
        baseline_db: str,
        model_version: str
    ):
        """
        Initialize drift detector.

        Args:
            baseline_db: Path to SQLite database for baseline storage
            model_version: Model version for baseline tracking
        """
        self.baseline_db = baseline_db
        self.model_version = model_version

        # Create schema if needed
        self._create_schema()

    def _create_schema(self):
        """Create database schema for drift baselines (AC5.2.4)"""
        conn = sqlite3.connect(self.baseline_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drift_baselines (
                baseline_id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                distribution_type TEXT CHECK(distribution_type IN ('histogram', 'summary')) DEFAULT 'histogram',
                bins TEXT,
                counts TEXT,
                mean REAL,
                std REAL,
                min REAL,
                max REAL,
                percentiles TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(feature_name, model_version)
            )
        """)

        conn.commit()
        conn.close()

    def calculate_ks_statistic(
        self,
        baseline_dist: np.ndarray,
        production_dist: np.ndarray
    ) -> float:
        """
        Kolmogorov-Smirnov test for continuous distributions (AC5.2.2).

        Args:
            baseline_dist: Training data distribution
            production_dist: Production data distribution

        Returns:
            KS statistic (0 to 1, higher = more drift)
        """
        statistic, _ = ks_2samp(baseline_dist, production_dist)
        return statistic

    def calculate_ks_statistic_with_pvalue(
        self,
        baseline_dist: np.ndarray,
        production_dist: np.ndarray
    ) -> Tuple[float, float]:
        """
        KS test with p-value.

        Args:
            baseline_dist: Training data distribution
            production_dist: Production data distribution

        Returns:
            Tuple of (ks_statistic, p_value)
        """
        statistic, p_value = ks_2samp(baseline_dist, production_dist)
        return statistic, p_value

    def calculate_psi(
        self,
        baseline_dist: np.ndarray,
        production_dist: np.ndarray,
        bins: int = 10
    ) -> float:
        """
        Population Stability Index (AC5.2.3).

        Formula: PSI = Σ (actual% - expected%) * ln(actual% / expected%)

        Interpretation:
        - PSI < 0.1: No significant drift
        - 0.1 ≤ PSI < 0.25: Moderate drift
        - PSI ≥ 0.25: Significant drift

        Args:
            baseline_dist: Training data distribution
            production_dist: Production data distribution
            bins: Number of bins for discretization

        Returns:
            PSI score (0 to infinity, typically 0 to 1)
        """
        # Discretize into bins
        baseline_binned, bin_edges = np.histogram(baseline_dist, bins=bins)
        production_binned, _ = np.histogram(production_dist, bins=bin_edges)

        # Calculate percentages (add small epsilon to avoid division by zero)
        epsilon = 1e-10
        baseline_pct = (baseline_binned + epsilon) / (len(baseline_dist) + epsilon * bins)
        production_pct = (production_binned + epsilon) / (len(production_dist) + epsilon * bins)

        # PSI formula
        psi = np.sum((production_pct - baseline_pct) * np.log(production_pct / baseline_pct))

        return psi

    def store_baseline_distribution(
        self,
        feature_name: str,
        distribution: np.ndarray
    ):
        """
        Store baseline feature distribution (AC5.2.4).

        Args:
            feature_name: Name of the feature
            distribution: Baseline distribution array
        """
        # Calculate statistics
        mean = float(np.mean(distribution))
        std = float(np.std(distribution))
        min_val = float(np.min(distribution))
        max_val = float(np.max(distribution))

        # Calculate percentiles
        percentiles = {
            'p5': float(np.percentile(distribution, 5)),
            'p25': float(np.percentile(distribution, 25)),
            'p50': float(np.percentile(distribution, 50)),
            'p75': float(np.percentile(distribution, 75)),
            'p95': float(np.percentile(distribution, 95))
        }

        # Create histogram
        counts, bin_edges = np.histogram(distribution, bins=20)

        # Store in database
        conn = sqlite3.connect(self.baseline_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO drift_baselines
            (feature_name, model_version, distribution_type, bins, counts, mean, std, min, max, percentiles)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feature_name,
            self.model_version,
            'histogram',
            json.dumps(bin_edges.tolist()),
            json.dumps(counts.tolist()),
            mean,
            std,
            min_val,
            max_val,
            json.dumps(percentiles)
        ))

        conn.commit()
        conn.close()

    def load_baseline_distribution(
        self,
        feature_name: str
    ) -> Optional[np.ndarray]:
        """
        Load baseline feature distribution (AC5.2.4).

        Args:
            feature_name: Name of the feature

        Returns:
            Baseline distribution array or None if not found
        """
        conn = sqlite3.connect(self.baseline_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT bins, counts FROM drift_baselines
            WHERE feature_name = ? AND model_version = ?
        """, (feature_name, self.model_version))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            return None

        # Reconstruct distribution from histogram
        bins = json.loads(result[0])
        counts = json.loads(result[1])

        # Sample from histogram to reconstruct approximate distribution
        bin_centers = [(bins[i] + bins[i+1]) / 2 for i in range(len(bins) - 1)]
        distribution = []
        for center, count in zip(bin_centers, counts):
            distribution.extend([center] * count)

        return np.array(distribution)

    def detect_drift(
        self,
        production_data: Dict[str, np.ndarray]
    ) -> Dict[str, Dict[str, float]]:
        """
        Detect drift across all features (AC5.2.5).

        Args:
            production_data: Dictionary of feature_name -> production distribution

        Returns:
            Dictionary of feature_name -> {ks_statistic, psi, status}
        """
        drift_results = {}

        for feature_name, production_dist in production_data.items():
            # Load baseline
            baseline_dist = self.load_baseline_distribution(feature_name)

            if baseline_dist is None:
                continue

            # Calculate KS statistic
            ks_stat = self.calculate_ks_statistic(baseline_dist, production_dist)

            # Calculate PSI
            psi = self.calculate_psi(baseline_dist, production_dist)

            # Determine status
            if psi >= 0.25:
                status = 'DRIFT'
            elif psi >= 0.1:
                status = 'MODERATE'
            else:
                status = 'OK'

            drift_results[feature_name] = {
                'ks_statistic': ks_stat,
                'psi': psi,
                'status': status
            }

        return drift_results

    def generate_drift_report(
        self,
        drift_results: Dict[str, Dict[str, float]],
        date: str
    ) -> str:
        """
        Generate human-readable drift report (AC5.2.6).

        Args:
            drift_results: Results from detect_drift()
            date: Date of drift detection (YYYY-MM-DD)

        Returns:
            Formatted drift report string
        """
        # Count features by status
        total_features = len(drift_results)
        drifted_features = sum(1 for r in drift_results.values() if r['status'] == 'DRIFT')

        # Determine overall severity
        if drifted_features > total_features * 0.3:
            overall_severity = 'CRITICAL'
        elif drifted_features > 0:
            overall_severity = 'MODERATE'
        else:
            overall_severity = 'OK'

        # Build report
        report = f"""========================================
DATA DRIFT DETECTION REPORT
========================================
Date: {date}
Model Version: {self.model_version}

SUMMARY:
- Features Tested: {total_features}
- Features with Drift: {drifted_features} ({drifted_features/total_features*100:.0f}%)
- Severity: {overall_severity}

DETAILED RESULTS:
Feature Name           | KS Stat | PSI   | Status      | Action
-----------------------|---------|-------|-------------|------------------
"""

        # Add feature details
        for feature_name, result in sorted(drift_results.items()):
            action = 'Retrain recommended' if result['status'] == 'DRIFT' else 'Monitor' if result['status'] == 'MODERATE' else '-'
            report += f"{feature_name:<22} | {result['ks_statistic']:>7.2f} | {result['psi']:>5.2f} | {result['status']:<11} | {action}\n"

        # Add recommendations
        report += f"""
DRIFT SEVERITY: {overall_severity}
"""

        if drifted_features > 0:
            drifted_names = [name for name, r in drift_results.items() if r['status'] == 'DRIFT']
            report += f"- {drifted_features} features show significant drift (PSI ≥ 0.25)\n"
            report += f"- Affected features: {', '.join(drifted_names[:5])}\n"
            report += "\nRECOMMENDATIONS:\n"
            report += "1. Retrain model on last 90 days of data\n"
            report += "2. Monitor model performance closely next 7 days\n"
            report += "3. Consider adaptive feature normalization\n"

        report += "========================================\n"

        return report

    def determine_alert_severity(
        self,
        psi: float,
        ks_stat: float
    ) -> str:
        """
        Determine alert severity (AC5.2.7).

        Thresholds:
        - Low drift: PSI < 0.1 → No alert
        - Moderate drift: 0.1 ≤ PSI < 0.25 → Slack notification
        - High drift: PSI ≥ 0.25 → Email + Slack
        - Critical drift: PSI ≥ 0.4 → Page on-call

        Args:
            psi: PSI score
            ks_stat: KS statistic

        Returns:
            Severity level: 'none', 'low', 'moderate', 'high', 'critical'
        """
        if psi >= 0.4:
            return 'critical'
        elif psi >= 0.25:
            return 'high'
        elif psi >= 0.1:
            return 'moderate'
        elif psi < 0.1:
            return 'low'
        else:
            return 'none'
