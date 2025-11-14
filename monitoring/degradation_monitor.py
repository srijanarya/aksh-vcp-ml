"""
Model Degradation Monitor (Story 5.3)

Monitors model performance degradation in production:
- Tracks production F1, precision, recall, ROC-AUC
- Compares against baseline test set metrics
- Detects degradation with severity levels
- Generates performance reports
- Recommends model rollback when needed

Author: VCP ML Team
Created: 2025-11-14
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
import numpy as np


class ModelMonitor:
    """
    Model performance degradation monitor.

    Tracks production metrics and compares to baseline.
    Alerts when F1 drops >5% from baseline.
    """

    def __init__(
        self,
        predictions_db: str,
        baseline_metrics: Dict[str, float],
        model_version: str
    ):
        """
        Initialize model monitor.

        Args:
            predictions_db: Path to SQLite database for production labels
            baseline_metrics: Baseline test set metrics (f1, precision, recall, roc_auc)
            model_version: Current model version
        """
        self.predictions_db = predictions_db
        self.baseline_metrics = baseline_metrics
        self.model_version = model_version

        # Create schema
        self._create_schema()

    def _create_schema(self):
        """Create database schema for production labels (AC5.3.2)"""
        conn = sqlite3.connect(self.predictions_db)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS production_labels (
                label_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bse_code TEXT NOT NULL,
                prediction_date DATE NOT NULL,
                earnings_date DATE NOT NULL,
                actual_label INTEGER NOT NULL CHECK(actual_label IN (0, 1)),
                predicted_label INTEGER NOT NULL CHECK(predicted_label IN (0, 1)),
                predicted_probability REAL,
                model_version TEXT,
                labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bse_code, prediction_date)
            )
        """)

        conn.commit()
        conn.close()

    def store_production_label(
        self,
        bse_code: str,
        prediction_date: str,
        earnings_date: str,
        actual_label: int,
        predicted_label: int,
        predicted_probability: float,
        model_version: Optional[str] = None
    ):
        """
        Store production label (AC5.3.2).

        Args:
            bse_code: BSE code of stock
            prediction_date: Date prediction was made
            earnings_date: Date earnings were announced
            actual_label: Actual outcome (0 or 1)
            predicted_label: Predicted label (0 or 1)
            predicted_probability: Predicted probability
            model_version: Model version (defaults to self.model_version)
        """
        if model_version is None:
            model_version = self.model_version

        conn = sqlite3.connect(self.predictions_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO production_labels
            (bse_code, prediction_date, earnings_date, actual_label, predicted_label, predicted_probability, model_version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            bse_code,
            prediction_date,
            earnings_date,
            actual_label,
            predicted_label,
            predicted_probability,
            model_version
        ))

        conn.commit()
        conn.close()

    def load_production_labels(
        self,
        start_date: str,
        end_date: str,
        model_version: Optional[str] = None
    ) -> List[Dict]:
        """
        Load production labels for date range (AC5.3.2).

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            model_version: Model version filter (defaults to self.model_version)

        Returns:
            List of label dictionaries
        """
        if model_version is None:
            model_version = self.model_version

        conn = sqlite3.connect(self.predictions_db)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT bse_code, prediction_date, actual_label, predicted_label, predicted_probability
            FROM production_labels
            WHERE prediction_date BETWEEN ? AND ?
            AND model_version = ?
        """, (start_date, end_date, model_version))

        rows = cursor.fetchall()
        conn.close()

        labels = []
        for row in rows:
            labels.append({
                'bse_code': row[0],
                'prediction_date': row[1],
                'actual_label': row[2],
                'predicted_label': row[3],
                'predicted_probability': row[4]
            })

        return labels

    def calculate_production_metrics(
        self,
        start_date: str,
        end_date: str,
        min_predictions: int = 100
    ) -> Optional[Dict[str, float]]:
        """
        Calculate production metrics (AC5.3.3).

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            min_predictions: Minimum predictions required

        Returns:
            Metrics dictionary or None if insufficient data
        """
        labels = self.load_production_labels(start_date, end_date)

        if len(labels) < min_predictions:
            return {'insufficient_data': True, 'count': len(labels)}

        # Extract arrays
        y_true = [label['actual_label'] for label in labels]
        y_pred = [label['predicted_label'] for label in labels]

        # Calculate metrics
        f1 = f1_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)

        metrics = {
            'f1': f1,
            'precision': precision,
            'recall': recall,
            'predictions': len(labels)
        }

        # Calculate ROC-AUC if we have probabilities
        if all('predicted_probability' in label for label in labels):
            y_proba = [label['predicted_probability'] for label in labels]
            try:
                roc_auc = roc_auc_score(y_true, y_proba)
                metrics['roc_auc'] = roc_auc
            except:
                pass

        return metrics

    def calculate_rolling_metrics(
        self,
        window_days: int = 30
    ) -> Optional[Dict[str, float]]:
        """
        Calculate rolling window metrics (AC5.3.3).

        Args:
            window_days: Rolling window size in days (7, 30, or 90)

        Returns:
            Metrics for rolling window
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=window_days)).strftime('%Y-%m-%d')

        return self.calculate_production_metrics(start_date, end_date)

    def detect_degradation(
        self,
        current_metrics: Dict[str, float]
    ) -> str:
        """
        Detect performance degradation (AC5.3.4).

        Thresholds:
        - Minor: 3-5% F1 drop
        - Moderate: 5-10% F1 drop
        - Severe: >10% F1 drop

        Args:
            current_metrics: Current production metrics

        Returns:
            Degradation status: 'none', 'minor', 'moderate', 'severe'
        """
        baseline_f1 = self.baseline_metrics['f1']
        current_f1 = current_metrics.get('f1', baseline_f1)

        # Calculate percentage drop
        drop_pct = ((baseline_f1 - current_f1) / baseline_f1) * 100

        if drop_pct > 10:
            return 'severe'
        elif drop_pct >= 5:
            return 'moderate'
        elif drop_pct >= 3:
            return 'minor'
        else:
            return 'none'

    def generate_performance_report(
        self,
        current_metrics: Dict[str, float],
        date: str
    ) -> str:
        """
        Generate performance report (AC5.3.5).

        Args:
            current_metrics: Current production metrics
            date: Report date (YYYY-MM-DD)

        Returns:
            Formatted performance report
        """
        # Calculate degradation
        status = self.detect_degradation(current_metrics)

        # Calculate percentage changes
        baseline_f1 = self.baseline_metrics['f1']
        current_f1 = current_metrics.get('f1', baseline_f1)
        f1_change = ((current_f1 - baseline_f1) / baseline_f1) * 100

        baseline_precision = self.baseline_metrics.get('precision', 0)
        current_precision = current_metrics.get('precision', baseline_precision)
        precision_change = ((current_precision - baseline_precision) / baseline_precision) * 100 if baseline_precision > 0 else 0

        baseline_recall = self.baseline_metrics.get('recall', 0)
        current_recall = current_metrics.get('recall', baseline_recall)
        recall_change = ((current_recall - baseline_recall) / baseline_recall) * 100 if baseline_recall > 0 else 0

        # Build report
        report = f"""========================================
MODEL PERFORMANCE REPORT
========================================
Date: {date}
Model Version: {self.model_version}

BASELINE PERFORMANCE (Test Set):
- F1 Score: {baseline_f1:.2f}
- Precision: {baseline_precision:.2f}
- Recall: {baseline_recall:.2f}
"""

        if 'roc_auc' in self.baseline_metrics:
            report += f"- ROC-AUC: {self.baseline_metrics['roc_auc']:.2f}\n"

        report += f"""
PRODUCTION PERFORMANCE (Last 30 Days):
- F1 Score: {current_f1:.2f} ({"↓" if f1_change < 0 else "↑"} {abs(f1_change):.0f}%)
- Precision: {current_precision:.2f} ({"↓" if precision_change < 0 else "↑"} {abs(precision_change):.0f}%)
- Recall: {current_recall:.2f} ({"↓" if recall_change < 0 else "↑"} {abs(recall_change):.0f}%)
"""

        if 'roc_auc' in current_metrics:
            baseline_auc = self.baseline_metrics.get('roc_auc', current_metrics['roc_auc'])
            auc_change = ((current_metrics['roc_auc'] - baseline_auc) / baseline_auc) * 100
            report += f"- ROC-AUC: {current_metrics['roc_auc']:.2f} ({"↓" if auc_change < 0 else "↑"} {abs(auc_change):.0f}%)\n"

        if 'predictions' in current_metrics:
            report += f"- Predictions: {current_metrics['predictions']:,}\n"

        # Add status
        report += f"\nSTATUS: {status.upper()}"
        if status != 'none':
            report += " DEGRADATION"

        report += f"""

RECOMMENDATIONS:
"""

        if status == 'severe':
            report += "1. URGENT: Consider model rollback to previous stable version\n"
            report += "2. Retrain model on last 90 days of data\n"
            report += "3. Review drift report for feature changes\n"
        elif status == 'moderate':
            report += "1. Retrain model on last 90 days of data\n"
            report += "2. Review drift report for feature changes\n"
            report += "3. Monitor performance closely next 7 days\n"
        elif status == 'minor':
            report += "1. Monitor performance closely\n"
            report += "2. Review recent data patterns\n"
        else:
            report += "1. Continue monitoring\n"

        report += "========================================\n"

        return report

    def recommend_rollback(
        self,
        degradation_status: str
    ) -> Optional[str]:
        """
        Recommend model rollback if needed (AC5.3.6).

        Args:
            degradation_status: Degradation status from detect_degradation()

        Returns:
            Rollback recommendation message or None
        """
        if degradation_status == 'severe':
            return f"Recommend rollback from {self.model_version} to previous stable version"
        else:
            return None

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for dashboard (AC5.3.7).

        Returns:
            Dictionary with current metrics and degradation severity
        """
        # Get 30-day metrics
        metrics = self.calculate_rolling_metrics(window_days=30)

        if metrics is None or metrics.get('insufficient_data', False):
            return {
                'f1_score': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'roc_auc': 0.0,
                'degradation_severity': 'unknown',
                'insufficient_data': True
            }

        # Detect degradation
        status = self.detect_degradation(metrics)

        return {
            'f1_score': metrics.get('f1', 0.0),
            'precision': metrics.get('precision', 0.0),
            'recall': metrics.get('recall', 0.0),
            'roc_auc': metrics.get('roc_auc', 0.0),
            'degradation_severity': status,
            'predictions': metrics.get('predictions', 0)
        }
