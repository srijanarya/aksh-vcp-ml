"""
Story 3.4: Model Evaluation

Comprehensive model evaluation with metrics, visualizations, and HTML reporting.

Features:
- F1, Precision, Recall, ROC-AUC, PR-AUC metrics
- Confusion matrix heatmap
- ROC and Precision-Recall curves
- SHAP feature importance for tree models
- Self-contained HTML evaluation report

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import base64
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for servers
import matplotlib.pyplot as plt
import seaborn as sns

# Metrics
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    precision_recall_curve
)

# SHAP for feature importance
import shap

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Comprehensive model evaluation with metrics and visualizations.

    Capabilities:
    - Calculate F1, Precision, Recall, ROC-AUC, PR-AUC
    - Generate confusion matrix heatmap
    - Plot ROC and Precision-Recall curves
    - SHAP feature importance (TreeExplainer for tree models)
    - HTML report with embedded base64 images

    Performance Target:
    - Identify best model with F1 ≥ 0.70
    - ROC-AUC ≥ 0.75
    """

    def __init__(self, output_dir: str):
        """
        Initialize model evaluator (AC3.4.1)

        Args:
            output_dir: Directory to save plots and reports
        """
        self.output_dir = str(output_dir)
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"ModelEvaluator initialized: output_dir={output_dir}")

    def calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate comprehensive metrics (AC3.4.2)

        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Predicted probabilities (positive class)

        Returns:
            Dict with metrics: f1, precision, recall, roc_auc, pr_auc, accuracy

        Raises:
            ValueError: If arrays are empty
        """
        if len(y_true) == 0:
            raise ValueError("Cannot calculate metrics on empty arrays")

        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_true, y_proba),
            'pr_auc': average_precision_score(y_true, y_proba)
        }

        # Round to 4 decimal places
        metrics = {k: round(v, 4) for k, v in metrics.items()}

        return metrics

    def get_classification_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> str:
        """
        Generate classification report (AC3.4.2)

        Args:
            y_true: True labels
            y_pred: Predicted labels

        Returns:
            Classification report as string
        """
        return classification_report(y_true, y_pred, zero_division=0)

    def get_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> np.ndarray:
        """
        Calculate confusion matrix (AC3.4.3)

        Args:
            y_true: True labels
            y_pred: Predicted labels

        Returns:
            2x2 confusion matrix [[TN, FP], [FN, TP]]
        """
        return confusion_matrix(y_true, y_pred)

    def plot_confusion_matrix(
        self,
        cm: np.ndarray,
        model_name: str
    ) -> str:
        """
        Plot confusion matrix heatmap (AC3.4.3)

        Args:
            cm: Confusion matrix from get_confusion_matrix
            model_name: Name of the model for title

        Returns:
            Path to saved PNG file
        """
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=['Negative', 'Positive'],
            yticklabels=['Negative', 'Positive']
        )
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')

        output_path = Path(self.output_dir) / f"{model_name.lower().replace(' ', '_')}_confusion_matrix.png"
        plt.savefig(output_path, bbox_inches='tight', dpi=100)
        plt.close()

        logger.info(f"Confusion matrix saved: {output_path}")
        return str(output_path)

    def plot_roc_curve(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        model_name: str
    ) -> str:
        """
        Plot ROC curve (AC3.4.4)

        Args:
            y_true: True labels
            y_proba: Predicted probabilities (positive class)
            model_name: Name of the model

        Returns:
            Path to saved PNG file
        """
        fpr, tpr, _ = roc_curve(y_true, y_proba)
        auc = roc_auc_score(y_true, y_proba)

        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'{model_name} (AUC = {auc:.4f})', linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve - {model_name}')
        plt.legend(loc='lower right')
        plt.grid(alpha=0.3)

        output_path = Path(self.output_dir) / f"{model_name.lower().replace(' ', '_')}_roc_curve.png"
        plt.savefig(output_path, bbox_inches='tight', dpi=100)
        plt.close()

        logger.info(f"ROC curve saved: {output_path}")
        return str(output_path)

    def plot_roc_curves_comparison(
        self,
        models_data: List[Dict[str, Any]]
    ) -> str:
        """
        Plot ROC curves for multiple models (AC3.4.4)

        Args:
            models_data: List of dicts with keys: name, y_true, y_proba

        Returns:
            Path to saved PNG file
        """
        plt.figure(figsize=(10, 7))

        for model_data in models_data:
            name = model_data['name']
            y_true = model_data['y_true']
            y_proba = model_data['y_proba']

            fpr, tpr, _ = roc_curve(y_true, y_proba)
            auc = roc_auc_score(y_true, y_proba)

            plt.plot(fpr, tpr, label=f'{name} (AUC = {auc:.4f})', linewidth=2)

        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curves Comparison')
        plt.legend(loc='lower right')
        plt.grid(alpha=0.3)

        output_path = Path(self.output_dir) / "roc_curves_comparison.png"
        plt.savefig(output_path, bbox_inches='tight', dpi=100)
        plt.close()

        logger.info(f"ROC curves comparison saved: {output_path}")
        return str(output_path)

    def plot_pr_curve(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        model_name: str
    ) -> str:
        """
        Plot Precision-Recall curve (AC3.4.5)

        Args:
            y_true: True labels
            y_proba: Predicted probabilities (positive class)
            model_name: Name of the model

        Returns:
            Path to saved PNG file
        """
        precision, recall, _ = precision_recall_curve(y_true, y_proba)
        pr_auc = average_precision_score(y_true, y_proba)

        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision, label=f'{model_name} (PR-AUC = {pr_auc:.4f})', linewidth=2)
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title(f'Precision-Recall Curve - {model_name}')
        plt.legend(loc='lower left')
        plt.grid(alpha=0.3)

        output_path = Path(self.output_dir) / f"{model_name.lower().replace(' ', '_')}_pr_curve.png"
        plt.savefig(output_path, bbox_inches='tight', dpi=100)
        plt.close()

        logger.info(f"PR curve saved: {output_path}")
        return str(output_path)

    def plot_pr_curves_comparison(
        self,
        models_data: List[Dict[str, Any]]
    ) -> str:
        """
        Plot Precision-Recall curves for multiple models (AC3.4.5)

        Args:
            models_data: List of dicts with keys: name, y_true, y_proba

        Returns:
            Path to saved PNG file
        """
        plt.figure(figsize=(10, 7))

        for model_data in models_data:
            name = model_data['name']
            y_true = model_data['y_true']
            y_proba = model_data['y_proba']

            precision, recall, _ = precision_recall_curve(y_true, y_proba)
            pr_auc = average_precision_score(y_true, y_proba)

            plt.plot(recall, precision, label=f'{name} (PR-AUC = {pr_auc:.4f})', linewidth=2)

        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curves Comparison')
        plt.legend(loc='lower left')
        plt.grid(alpha=0.3)

        output_path = Path(self.output_dir) / "pr_curves_comparison.png"
        plt.savefig(output_path, bbox_inches='tight', dpi=100)
        plt.close()

        logger.info(f"PR curves comparison saved: {output_path}")
        return str(output_path)

    def plot_shap_importance(
        self,
        model: Any,
        X_test: Union[pd.DataFrame, np.ndarray],
        model_name: str,
        max_display: int = 20
    ) -> Optional[str]:
        """
        Plot SHAP feature importance (AC3.4.6)

        Uses TreeExplainer for tree-based models (XGBoost, LightGBM, RandomForest).
        Skips non-tree models gracefully.

        Args:
            model: Trained model
            X_test: Test features (DataFrame with feature names or numpy array)
            model_name: Name of the model
            max_display: Maximum number of features to display (default: 20)

        Returns:
            Path to saved PNG file, or None if model doesn't support SHAP
        """
        # Check if model is tree-based
        model_type = type(model).__name__
        tree_models = ['XGBClassifier', 'LGBMClassifier', 'RandomForestClassifier']

        if model_type not in tree_models:
            logger.info(f"SHAP skipped for {model_name}: {model_type} is not a tree-based model")
            return None

        try:
            # Convert to DataFrame if numpy array
            if isinstance(X_test, np.ndarray):
                X_test = pd.DataFrame(X_test, columns=[f"feature_{i}" for i in range(X_test.shape[1])])

            # Sample if too many rows (SHAP can be slow)
            if len(X_test) > 100:
                X_test_sample = X_test.sample(n=100, random_state=42)
            else:
                X_test_sample = X_test

            # Create TreeExplainer
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_test_sample)

            # For binary classification, shap_values might be a list
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class

            # Create summary plot
            plt.figure(figsize=(10, 8))
            shap.summary_plot(
                shap_values,
                X_test_sample,
                plot_type="bar",
                max_display=max_display,
                show=False
            )
            plt.title(f'SHAP Feature Importance - {model_name}')

            output_path = Path(self.output_dir) / f"{model_name.lower().replace(' ', '_')}_shap_importance.png"
            plt.savefig(output_path, bbox_inches='tight', dpi=100)
            plt.close()

            logger.info(f"SHAP importance saved: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.warning(f"SHAP importance failed for {model_name}: {e}")
            return None

    def evaluate_model(
        self,
        model: Any,
        X_test: pd.DataFrame,
        y_test: np.ndarray,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Comprehensive evaluation of a single model (AC3.4.8)

        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            model_name: Name of the model

        Returns:
            Dict with model_name, metrics, and paths to all plots
        """
        logger.info(f"Evaluating model: {model_name}")

        # Get predictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        # Calculate metrics
        metrics = self.calculate_metrics(y_test, y_pred, y_proba)

        # Get confusion matrix
        cm = self.get_confusion_matrix(y_test, y_pred)
        cm_path = self.plot_confusion_matrix(cm, model_name)

        # Plot ROC curve
        roc_path = self.plot_roc_curve(y_test, y_proba, model_name)

        # Plot PR curve
        pr_path = self.plot_pr_curve(y_test, y_proba, model_name)

        # SHAP feature importance (if applicable)
        shap_path = self.plot_shap_importance(model, X_test, model_name)

        results = {
            'model_name': model_name,
            'metrics': metrics,
            'confusion_matrix_path': cm_path,
            'roc_curve_path': roc_path,
            'pr_curve_path': pr_path,
            'shap_path': shap_path,
            'classification_report': self.get_classification_report(y_test, y_pred)
        }

        logger.info(f"{model_name} evaluation complete: F1={metrics['f1']:.4f}, ROC-AUC={metrics['roc_auc']:.4f}")

        return results

    def evaluate_models(
        self,
        models: List[Dict[str, Any]],
        X_test: pd.DataFrame,
        y_test: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple models (AC3.4.8)

        Args:
            models: List of dicts with keys: model, name
            X_test: Test features
            y_test: Test labels

        Returns:
            List of evaluation results for each model
        """
        all_results = []

        for model_data in models:
            model = model_data['model']
            name = model_data['name']

            results = self.evaluate_model(model, X_test, y_test, name)
            all_results.append(results)

        return all_results

    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode PNG image to base64 for HTML embedding

        Args:
            image_path: Path to PNG file

        Returns:
            Base64 encoded string
        """
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def generate_html_report(
        self,
        models_results: List[Dict[str, Any]],
        report_name: str = "model_evaluation"
    ) -> str:
        """
        Generate self-contained HTML evaluation report (AC3.4.7)

        Args:
            models_results: List of evaluation results from evaluate_models
            report_name: Name for the HTML file

        Returns:
            Path to saved HTML file
        """
        logger.info(f"Generating HTML report: {report_name}")

        # Start HTML
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Model Evaluation Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .model-section {
            background-color: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .model-title {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .metrics-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .metrics-table th, .metrics-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        .metrics-table th {
            background-color: #3498db;
            color: white;
        }
        .metrics-table tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .image-container {
            margin: 20px 0;
            text-align: center;
        }
        .image-container img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .classification-report {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        .footer {
            text-align: center;
            color: #7f8c8d;
            margin-top: 40px;
            padding: 20px;
        }
    </style>
</head>
<body>
"""

        # Header
        html += f"""
    <div class="header">
        <h1>Model Evaluation Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Number of Models: {len(models_results)}</p>
    </div>
"""

        # Summary table
        html += """
    <div class="model-section">
        <h2>Models Comparison</h2>
        <table class="metrics-table">
            <tr>
                <th>Model</th>
                <th>F1 Score</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>ROC-AUC</th>
                <th>PR-AUC</th>
                <th>Accuracy</th>
            </tr>
"""

        for result in models_results:
            metrics = result.get('metrics', {})
            html += f"""
            <tr>
                <td><strong>{result['model_name']}</strong></td>
                <td>{metrics.get('f1', 0):.4f}</td>
                <td>{metrics.get('precision', 0):.4f}</td>
                <td>{metrics.get('recall', 0):.4f}</td>
                <td>{metrics.get('roc_auc', 0):.4f}</td>
                <td>{metrics.get('pr_auc', 0):.4f}</td>
                <td>{metrics.get('accuracy', 0):.4f}</td>
            </tr>
"""

        html += """
        </table>
    </div>
"""

        # Individual model sections
        for result in models_results:
            model_name = result['model_name']
            metrics = result['metrics']

            html += f"""
    <div class="model-section">
        <h2 class="model-title">{model_name}</h2>

        <h3>Metrics</h3>
        <table class="metrics-table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
"""

            for metric_name, metric_value in metrics.items():
                html += f"""
            <tr>
                <td>{metric_name.upper()}</td>
                <td>{metric_value:.4f}</td>
            </tr>
"""

            html += """
        </table>
"""

            # Embed images
            if result.get('confusion_matrix_path') and Path(result['confusion_matrix_path']).exists():
                img_base64 = self._encode_image_to_base64(result['confusion_matrix_path'])
                html += f"""
        <div class="image-container">
            <h3>Confusion Matrix</h3>
            <img src="data:image/png;base64,{img_base64}" alt="Confusion Matrix">
        </div>
"""

            if result.get('roc_curve_path') and Path(result['roc_curve_path']).exists():
                img_base64 = self._encode_image_to_base64(result['roc_curve_path'])
                html += f"""
        <div class="image-container">
            <h3>ROC Curve</h3>
            <img src="data:image/png;base64,{img_base64}" alt="ROC Curve">
        </div>
"""

            if result.get('pr_curve_path') and Path(result['pr_curve_path']).exists():
                img_base64 = self._encode_image_to_base64(result['pr_curve_path'])
                html += f"""
        <div class="image-container">
            <h3>Precision-Recall Curve</h3>
            <img src="data:image/png;base64,{img_base64}" alt="PR Curve">
        </div>
"""

            if result.get('shap_path') and result['shap_path'] and Path(result['shap_path']).exists():
                img_base64 = self._encode_image_to_base64(result['shap_path'])
                html += f"""
        <div class="image-container">
            <h3>SHAP Feature Importance</h3>
            <img src="data:image/png;base64,{img_base64}" alt="SHAP Importance">
        </div>
"""

            # Classification report
            if result.get('classification_report'):
                html += f"""
        <h3>Classification Report</h3>
        <div class="classification-report">
{result['classification_report']}
        </div>
"""

            html += """
    </div>
"""

        # Footer
        html += """
    <div class="footer">
        <p>VCP Financial Research System - ML Model Evaluation</p>
        <p>Epic 3: Model Training & Hyperparameter Optimization - Story 3.4</p>
    </div>
</body>
</html>
"""

        # Save HTML
        output_path = Path(self.output_dir) / f"{report_name}.html"
        with open(output_path, 'w') as f:
            f.write(html)

        logger.info(f"HTML report saved: {output_path}")

        return str(output_path)
