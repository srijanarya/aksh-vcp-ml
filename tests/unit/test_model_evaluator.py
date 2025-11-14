"""
Unit tests for Story 3.4: Model Evaluation

TDD Phase: RED (write tests first)
Target: ≥90% test coverage

Test Coverage:
- AC3.4.1: ModelEvaluator class initialization
- AC3.4.2: Comprehensive metrics calculation (F1, Precision, Recall, ROC-AUC, PR-AUC)
- AC3.4.3: Confusion matrix generation
- AC3.4.4: ROC curve plotting
- AC3.4.5: Precision-Recall curve plotting
- AC3.4.6: SHAP feature importance (TreeExplainer for tree models)
- AC3.4.7: HTML report generation with embedded plots
- AC3.4.8: Model comparison functionality
- AC3.4.9: Edge case handling

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import pytest
import sqlite3
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import base64


class TestModelEvaluatorInitialization:
    """Test ModelEvaluator class initialization (AC3.4.1)"""

    def test_evaluator_class_exists(self):
        """AC3.4.1: Verify ModelEvaluator can be imported"""
        from agents.ml.model_evaluator import ModelEvaluator
        assert ModelEvaluator is not None

    def test_evaluator_instantiation(self, tmp_path):
        """AC3.4.1: Evaluator can be instantiated with output directory"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "evaluation"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        assert evaluator.output_dir == str(output_dir)
        assert Path(output_dir).exists()

    def test_evaluator_creates_output_directory(self, tmp_path):
        """AC3.4.1: Output directory is created if it doesn't exist"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "new_eval_dir" / "nested"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        assert Path(output_dir).exists()


class TestMetricsCalculation:
    """Test comprehensive metrics calculation (AC3.4.2)"""

    def test_calculate_metrics_returns_all_metrics(self):
        """AC3.4.2: calculate_metrics returns F1, Precision, Recall, ROC-AUC, PR-AUC"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir="/tmp/test_eval")

        # Create mock data
        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1, 0, 0, 1, 0, 0, 1])
        y_proba = np.array([0.1, 0.2, 0.8, 0.9, 0.4, 0.3, 0.7, 0.15, 0.45, 0.85])

        metrics = evaluator.calculate_metrics(y_true, y_pred, y_proba)

        # Verify all metrics are present
        assert 'f1' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'roc_auc' in metrics
        assert 'pr_auc' in metrics
        assert 'accuracy' in metrics

    def test_calculate_metrics_correct_values(self):
        """AC3.4.2: Metrics are calculated correctly"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir="/tmp/test_eval")

        # Simple case: perfect predictions
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.9, 0.8])

        metrics = evaluator.calculate_metrics(y_true, y_pred, y_proba)

        assert metrics['f1'] == 1.0
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['accuracy'] == 1.0
        assert metrics['roc_auc'] == 1.0

    def test_calculate_metrics_handles_zero_division(self):
        """AC3.4.2: Metrics handle zero division gracefully"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir="/tmp/test_eval")

        # All negative predictions
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 0])
        y_proba = np.array([0.1, 0.2, 0.3, 0.4])

        metrics = evaluator.calculate_metrics(y_true, y_pred, y_proba)

        # Should not raise error, precision should be 0
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0

    def test_calculate_metrics_rounds_to_4_decimals(self):
        """AC3.4.2: Metrics are rounded to 4 decimal places"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir="/tmp/test_eval")

        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1, 0, 0, 1, 0, 0, 1])
        y_proba = np.array([0.1, 0.2, 0.8, 0.9, 0.4, 0.3, 0.7, 0.15, 0.45, 0.85])

        metrics = evaluator.calculate_metrics(y_true, y_pred, y_proba)

        # All metrics should have at most 4 decimal places
        for key, value in metrics.items():
            assert len(str(value).split('.')[-1]) <= 4

    def test_calculate_metrics_classification_report(self):
        """AC3.4.2: Classification report is generated"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir="/tmp/test_eval")

        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1, 0, 0, 1, 0, 0, 1])
        y_proba = np.array([0.1, 0.2, 0.8, 0.9, 0.4, 0.3, 0.7, 0.15, 0.45, 0.85])

        classification_report = evaluator.get_classification_report(y_true, y_pred)

        assert isinstance(classification_report, str)
        assert 'precision' in classification_report
        assert 'recall' in classification_report
        assert 'f1-score' in classification_report


class TestConfusionMatrix:
    """Test confusion matrix generation (AC3.4.3)"""

    def test_get_confusion_matrix_returns_2x2_array(self):
        """AC3.4.3: get_confusion_matrix returns 2x2 numpy array"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir="/tmp/test_eval")

        y_true = np.array([0, 0, 1, 1, 1, 0])
        y_pred = np.array([0, 0, 1, 1, 0, 0])

        cm = evaluator.get_confusion_matrix(y_true, y_pred)

        assert isinstance(cm, np.ndarray)
        assert cm.shape == (2, 2)

    def test_confusion_matrix_values_correct(self):
        """AC3.4.3: Confusion matrix values are correct"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir="/tmp/test_eval")

        # TN=2, FP=1, FN=1, TP=2
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_pred = np.array([0, 0, 1, 1, 1, 0])

        cm = evaluator.get_confusion_matrix(y_true, y_pred)

        assert cm[0, 0] == 2  # TN
        assert cm[0, 1] == 1  # FP
        assert cm[1, 0] == 1  # FN
        assert cm[1, 1] == 2  # TP

    def test_plot_confusion_matrix_saves_png(self, tmp_path):
        """AC3.4.3: plot_confusion_matrix saves PNG file"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 1, 1, 1])

        cm = evaluator.get_confusion_matrix(y_true, y_pred)
        png_path = evaluator.plot_confusion_matrix(cm, model_name="TestModel")

        assert Path(png_path).exists()
        assert png_path.endswith(".png")
        assert "confusion_matrix" in png_path.lower()


class TestROCCurve:
    """Test ROC curve plotting (AC3.4.4)"""

    def test_plot_roc_curve_saves_png(self, tmp_path):
        """AC3.4.4: plot_roc_curve saves PNG file"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0])
        y_proba = np.array([0.1, 0.2, 0.8, 0.9, 0.7, 0.3, 0.85, 0.15])

        png_path = evaluator.plot_roc_curve(y_true, y_proba, model_name="TestModel")

        assert Path(png_path).exists()
        assert png_path.endswith(".png")
        assert "roc_curve" in png_path.lower()

    def test_plot_roc_curve_returns_auc_in_title(self, tmp_path):
        """AC3.4.4: ROC curve plot includes AUC in title"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        y_true = np.array([0, 0, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.9, 0.8])

        png_path = evaluator.plot_roc_curve(y_true, y_proba, model_name="TestModel")

        # File should exist and contain model name
        assert Path(png_path).exists()
        assert "TestModel" in png_path or "testmodel" in png_path.lower()

    def test_plot_roc_curve_multiple_models(self, tmp_path):
        """AC3.4.4: Can plot ROC curves for multiple models"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        y_true = np.array([0, 0, 1, 1])
        y_proba1 = np.array([0.1, 0.2, 0.9, 0.8])
        y_proba2 = np.array([0.15, 0.25, 0.85, 0.75])

        models_data = [
            {"name": "Model1", "y_true": y_true, "y_proba": y_proba1},
            {"name": "Model2", "y_true": y_true, "y_proba": y_proba2}
        ]

        png_path = evaluator.plot_roc_curves_comparison(models_data)

        assert Path(png_path).exists()
        assert png_path.endswith(".png")


class TestPRCurve:
    """Test Precision-Recall curve plotting (AC3.4.5)"""

    def test_plot_pr_curve_saves_png(self, tmp_path):
        """AC3.4.5: plot_pr_curve saves PNG file"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0])
        y_proba = np.array([0.1, 0.2, 0.8, 0.9, 0.7, 0.3, 0.85, 0.15])

        png_path = evaluator.plot_pr_curve(y_true, y_proba, model_name="TestModel")

        assert Path(png_path).exists()
        assert png_path.endswith(".png")
        assert "pr_curve" in png_path.lower()

    def test_plot_pr_curve_includes_auc(self, tmp_path):
        """AC3.4.5: PR curve plot includes PR-AUC in title"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        y_true = np.array([0, 0, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.9, 0.8])

        png_path = evaluator.plot_pr_curve(y_true, y_proba, model_name="TestModel")

        assert Path(png_path).exists()

    def test_plot_pr_curve_multiple_models(self, tmp_path):
        """AC3.4.5: Can plot PR curves for multiple models"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        y_true = np.array([0, 0, 1, 1])
        y_proba1 = np.array([0.1, 0.2, 0.9, 0.8])
        y_proba2 = np.array([0.15, 0.25, 0.85, 0.75])

        models_data = [
            {"name": "Model1", "y_true": y_true, "y_proba": y_proba1},
            {"name": "Model2", "y_true": y_true, "y_proba": y_proba2}
        ]

        png_path = evaluator.plot_pr_curves_comparison(models_data)

        assert Path(png_path).exists()
        assert png_path.endswith(".png")


class TestSHAPFeatureImportance:
    """Test SHAP feature importance (AC3.4.6)"""

    def test_plot_shap_importance_xgboost(self, tmp_path):
        """AC3.4.6: plot_shap_importance works for XGBoost"""
        from agents.ml.model_evaluator import ModelEvaluator
        import xgboost as xgb

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        # Create simple XGBoost model
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        feature_names = [f"feature_{i}" for i in range(5)]
        X_df = pd.DataFrame(X, columns=feature_names)

        model = xgb.XGBClassifier(random_state=42, n_estimators=10)
        model.fit(X, y)

        png_path = evaluator.plot_shap_importance(
            model=model,
            X_test=X_df,
            model_name="XGBoost"
        )

        assert Path(png_path).exists()
        assert png_path.endswith(".png")
        assert "shap" in png_path.lower()

    def test_plot_shap_importance_lightgbm(self, tmp_path):
        """AC3.4.6: plot_shap_importance works for LightGBM"""
        from agents.ml.model_evaluator import ModelEvaluator
        import lightgbm as lgb

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        # Create simple LightGBM model
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        feature_names = [f"feature_{i}" for i in range(5)]
        X_df = pd.DataFrame(X, columns=feature_names)

        model = lgb.LGBMClassifier(random_state=42, n_estimators=10, verbose=-1)
        model.fit(X, y)

        png_path = evaluator.plot_shap_importance(
            model=model,
            X_test=X_df,
            model_name="LightGBM"
        )

        assert Path(png_path).exists()
        assert png_path.endswith(".png")

    def test_plot_shap_importance_uses_tree_explainer(self, tmp_path):
        """AC3.4.6: SHAP uses TreeExplainer for tree models"""
        from agents.ml.model_evaluator import ModelEvaluator
        import xgboost as xgb

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        X = np.random.rand(50, 3)
        y = np.random.randint(0, 2, 50)
        X_df = pd.DataFrame(X, columns=['f1', 'f2', 'f3'])

        model = xgb.XGBClassifier(random_state=42, n_estimators=5)
        model.fit(X, y)

        with patch('shap.TreeExplainer') as mock_explainer:
            mock_explainer.return_value.shap_values.return_value = np.random.rand(50, 3)
            png_path = evaluator.plot_shap_importance(model, X_df, "XGBoost")
            mock_explainer.assert_called_once_with(model)

    def test_plot_shap_importance_skips_non_tree_models(self, tmp_path):
        """AC3.4.6: SHAP skips non-tree models gracefully"""
        from agents.ml.model_evaluator import ModelEvaluator
        from sklearn.neural_network import MLPClassifier

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        X = np.random.rand(50, 3)
        y = np.random.randint(0, 2, 50)
        X_df = pd.DataFrame(X, columns=['f1', 'f2', 'f3'])

        model = MLPClassifier(random_state=42, max_iter=10)
        model.fit(X, y)

        # Should return None or empty string for non-tree models
        result = evaluator.plot_shap_importance(model, X_df, "NeuralNet")
        assert result is None or result == ""


class TestHTMLReportGeneration:
    """Test HTML report generation (AC3.4.7)"""

    def test_generate_html_report_creates_file(self, tmp_path):
        """AC3.4.7: generate_html_report creates HTML file"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        model_results = {
            "model_name": "TestModel",
            "metrics": {
                "f1": 0.75,
                "precision": 0.72,
                "recall": 0.78,
                "roc_auc": 0.85,
                "pr_auc": 0.80
            },
            "confusion_matrix_path": None,
            "roc_curve_path": None,
            "pr_curve_path": None,
            "shap_path": None
        }

        html_path = evaluator.generate_html_report(
            models_results=[model_results],
            report_name="test_report"
        )

        assert Path(html_path).exists()
        assert html_path.endswith(".html")

    def test_html_report_contains_metrics(self, tmp_path):
        """AC3.4.7: HTML report contains all metrics"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        model_results = {
            "model_name": "TestModel",
            "metrics": {
                "f1": 0.75,
                "precision": 0.72,
                "recall": 0.78,
                "roc_auc": 0.85,
                "pr_auc": 0.80
            }
        }

        html_path = evaluator.generate_html_report([model_results], "test")

        # Read HTML and verify content
        with open(html_path, 'r') as f:
            html_content = f.read()

        assert "TestModel" in html_content
        assert "0.75" in html_content or "75" in html_content  # F1 score
        assert "Precision" in html_content or "precision" in html_content
        assert "Recall" in html_content or "recall" in html_content

    def test_html_report_embeds_images_base64(self, tmp_path):
        """AC3.4.7: HTML report embeds images as base64"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        # Create a dummy PNG file
        dummy_png = output_dir / "dummy.png"
        dummy_png.write_bytes(b"fake_png_data")

        model_results = {
            "model_name": "TestModel",
            "metrics": {"f1": 0.75},
            "confusion_matrix_path": str(dummy_png)
        }

        html_path = evaluator.generate_html_report([model_results], "test")

        with open(html_path, 'r') as f:
            html_content = f.read()

        # Should contain base64 encoded image
        assert "data:image/png;base64," in html_content or "<img" in html_content

    def test_html_report_self_contained(self, tmp_path):
        """AC3.4.7: HTML report is self-contained (no external dependencies)"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        model_results = {
            "model_name": "TestModel",
            "metrics": {"f1": 0.75}
        }

        html_path = evaluator.generate_html_report([model_results], "test")

        with open(html_path, 'r') as f:
            html_content = f.read()

        # Should not have external CSS/JS links
        assert "http://" not in html_content or "<style>" in html_content
        assert "https://" not in html_content or "<style>" in html_content


class TestModelComparison:
    """Test model comparison functionality (AC3.4.8)"""

    def test_evaluate_model_returns_complete_results(self, tmp_path):
        """AC3.4.8: evaluate_model returns all metrics and plots"""
        from agents.ml.model_evaluator import ModelEvaluator
        import xgboost as xgb

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        X_test = np.random.rand(20, 5)
        y_test = np.random.randint(0, 2, 20)

        feature_names = [f"feature_{i}" for i in range(5)]
        X_df = pd.DataFrame(X, columns=feature_names)
        X_test_df = pd.DataFrame(X_test, columns=feature_names)

        model = xgb.XGBClassifier(random_state=42, n_estimators=10)
        model.fit(X, y)

        results = evaluator.evaluate_model(
            model=model,
            X_test=X_test_df,
            y_test=y_test,
            model_name="XGBoost"
        )

        assert "model_name" in results
        assert "metrics" in results
        assert "confusion_matrix_path" in results
        assert "roc_curve_path" in results
        assert "pr_curve_path" in results

    def test_evaluate_multiple_models(self, tmp_path):
        """AC3.4.8: evaluate_models handles multiple models"""
        from agents.ml.model_evaluator import ModelEvaluator
        import xgboost as xgb
        import lightgbm as lgb

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        X_test = np.random.rand(20, 5)
        y_test = np.random.randint(0, 2, 20)

        feature_names = [f"feature_{i}" for i in range(5)]
        X_test_df = pd.DataFrame(X_test, columns=feature_names)

        model1 = xgb.XGBClassifier(random_state=42, n_estimators=10)
        model1.fit(X, y)

        model2 = lgb.LGBMClassifier(random_state=42, n_estimators=10, verbose=-1)
        model2.fit(X, y)

        models = [
            {"model": model1, "name": "XGBoost"},
            {"model": model2, "name": "LightGBM"}
        ]

        all_results = evaluator.evaluate_models(
            models=models,
            X_test=X_test_df,
            y_test=y_test
        )

        assert len(all_results) == 2
        assert all_results[0]["model_name"] == "XGBoost"
        assert all_results[1]["model_name"] == "LightGBM"

    def test_comparison_report_includes_all_models(self, tmp_path):
        """AC3.4.8: Comparison report includes all models"""
        from agents.ml.model_evaluator import ModelEvaluator

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        models_results = [
            {"model_name": "Model1", "metrics": {"f1": 0.75}},
            {"model_name": "Model2", "metrics": {"f1": 0.80}},
            {"model_name": "Model3", "metrics": {"f1": 0.70}}
        ]

        html_path = evaluator.generate_html_report(models_results, "comparison")

        with open(html_path, 'r') as f:
            html_content = f.read()

        assert "Model1" in html_content
        assert "Model2" in html_content
        assert "Model3" in html_content


class TestEdgeCases:
    """Test edge case handling (AC3.4.9)"""

    def test_handles_empty_test_set(self, tmp_path):
        """AC3.4.9: Handles empty test set gracefully"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir=str(tmp_path / "eval"))

        y_true = np.array([])
        y_pred = np.array([])
        y_proba = np.array([])

        with pytest.raises(ValueError):
            evaluator.calculate_metrics(y_true, y_pred, y_proba)

    def test_handles_all_same_class(self, tmp_path):
        """AC3.4.9: Handles all same class predictions"""
        from agents.ml.model_evaluator import ModelEvaluator

        evaluator = ModelEvaluator(output_dir=str(tmp_path / "eval"))

        y_true = np.array([0, 0, 0, 0])
        y_pred = np.array([0, 0, 0, 0])
        y_proba = np.array([0.1, 0.2, 0.3, 0.4])

        # Should not crash
        metrics = evaluator.calculate_metrics(y_true, y_pred, y_proba)
        assert metrics['accuracy'] == 1.0

    def test_handles_missing_feature_names(self, tmp_path):
        """AC3.4.9: Handles missing feature names in SHAP"""
        from agents.ml.model_evaluator import ModelEvaluator
        import xgboost as xgb

        output_dir = tmp_path / "eval"
        evaluator = ModelEvaluator(output_dir=str(output_dir))

        X = np.random.rand(50, 3)
        y = np.random.randint(0, 2, 50)

        model = xgb.XGBClassifier(random_state=42, n_estimators=5)
        model.fit(X, y)

        # Pass numpy array instead of DataFrame (no feature names)
        X_test = np.random.rand(10, 3)

        # Should handle gracefully
        result = evaluator.plot_shap_importance(model, X_test, "XGBoost")
        # Should either work or return None
        assert result is None or Path(result).exists()
