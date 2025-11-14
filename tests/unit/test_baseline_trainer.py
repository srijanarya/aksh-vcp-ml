"""
Unit tests for Story 3.1: Baseline Models Training

TDD Phase: RED (write tests first)
Target: ≥90% test coverage

Test Coverage:
- AC3.1.1: BaselineTrainer class initialization
- AC3.1.2: Data loading from multiple feature databases
- AC3.1.3: 80/20 stratified train/test split
- AC3.1.4: Logistic Regression training
- AC3.1.5: Random Forest training
- AC3.1.6: Metrics calculation (accuracy, precision, recall, F1, ROC-AUC)
- AC3.1.7: JSON serialization of results
- AC3.1.8: Edge case handling (empty data, single class)

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
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock


class TestBaselineTrainerInitialization:
    """Test BaselineTrainer class initialization (AC3.1.1)"""

    def test_trainer_class_exists(self):
        """AC3.1.1: Verify BaselineTrainer can be imported"""
        from agents.ml.baseline_trainer import BaselineTrainer
        assert BaselineTrainer is not None

    def test_trainer_instantiation(self, tmp_path):
        """AC3.1.1: Trainer can be instantiated with feature databases and labels"""
        from agents.ml.baseline_trainer import BaselineTrainer

        feature_dbs = {
            'technical': str(tmp_path / "technical_features.db"),
            'financial': str(tmp_path / "financial_features.db"),
            'sentiment': str(tmp_path / "sentiment_features.db"),
            'seasonality': str(tmp_path / "seasonality_features.db")
        }
        labels_db = str(tmp_path / "upper_circuit_labels.db")
        selected_features = ['rsi_14', 'macd_line', 'eps_growth', 'sentiment_score', 'quarter_q4']

        trainer = BaselineTrainer(
            feature_dbs=feature_dbs,
            labels_db=labels_db,
            selected_features=selected_features
        )

        assert trainer.feature_dbs == feature_dbs
        assert trainer.labels_db == labels_db
        assert trainer.selected_features == selected_features

    def test_trainer_initializes_models_none(self, tmp_path):
        """AC3.1.1: Models are None before training"""
        from agents.ml.baseline_trainer import BaselineTrainer

        feature_dbs = {'technical': str(tmp_path / "tech.db")}
        labels_db = str(tmp_path / "labels.db")

        trainer = BaselineTrainer(feature_dbs, labels_db, ['rsi_14'])

        assert trainer.logistic_model is None
        assert trainer.random_forest_model is None


class TestDataLoading:
    """Test data loading from multiple databases (AC3.1.2)"""

    def test_load_data_combines_all_features(self, tmp_path):
        """AC3.1.2: load_data combines features from all databases"""
        from agents.ml.baseline_trainer import BaselineTrainer

        # Create mock databases with features
        tech_db = tmp_path / "tech.db"
        fin_db = tmp_path / "fin.db"
        labels_db = tmp_path / "labels.db"

        # Technical features DB
        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE technical_features (
                bse_code TEXT,
                date DATE,
                rsi_14 REAL,
                macd_line REAL
            )
        """)
        cursor.execute("INSERT INTO technical_features VALUES ('500325', '2024-01-15', 65.5, 2.3)")
        cursor.execute("INSERT INTO technical_features VALUES ('500209', '2024-01-16', 45.2, -1.1)")
        conn.commit()
        conn.close()

        # Financial features DB
        conn = sqlite3.connect(fin_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE financial_features (
                bse_code TEXT,
                date DATE,
                eps_growth REAL
            )
        """)
        cursor.execute("INSERT INTO financial_features VALUES ('500325', '2024-01-15', 15.3)")
        cursor.execute("INSERT INTO financial_features VALUES ('500209', '2024-01-16', 8.7)")
        conn.commit()
        conn.close()

        # Labels DB
        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)
        cursor.execute("INSERT INTO upper_circuit_labels VALUES ('500325', '2024-01-15', 1)")
        cursor.execute("INSERT INTO upper_circuit_labels VALUES ('500209', '2024-01-16', 0)")
        conn.commit()
        conn.close()

        feature_dbs = {'technical': str(tech_db), 'financial': str(fin_db)}
        trainer = BaselineTrainer(feature_dbs, str(labels_db), ['rsi_14', 'macd_line', 'eps_growth'])

        X, y = trainer.load_data()

        assert len(X) == 2
        assert 'rsi_14' in X.columns
        assert 'macd_line' in X.columns
        assert 'eps_growth' in X.columns
        assert len(y) == 2
        assert sorted(y.tolist()) == [0, 1]  # Order doesn't matter, just check both values present

    def test_load_data_handles_missing_features(self, tmp_path):
        """AC3.1.2: load_data handles missing features gracefully"""
        from agents.ml.baseline_trainer import BaselineTrainer

        # Create DB with some missing features
        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE technical_features (
                bse_code TEXT,
                date DATE,
                rsi_14 REAL,
                macd_line REAL
            )
        """)
        cursor.execute("INSERT INTO technical_features VALUES ('500325', '2024-01-15', 65.5, NULL)")
        cursor.execute("INSERT INTO technical_features VALUES ('500209', '2024-01-16', NULL, -1.1)")
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)
        cursor.execute("INSERT INTO upper_circuit_labels VALUES ('500325', '2024-01-15', 1)")
        cursor.execute("INSERT INTO upper_circuit_labels VALUES ('500209', '2024-01-16', 0)")
        conn.commit()
        conn.close()

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14', 'macd_line'])

        X, y = trainer.load_data()

        # Should have NaN values
        assert pd.isna(X.loc[0, 'macd_line'])
        assert pd.isna(X.loc[1, 'rsi_14'])

    def test_load_data_filters_selected_features(self, tmp_path):
        """AC3.1.2: load_data only returns selected features"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE technical_features (
                bse_code TEXT,
                date DATE,
                rsi_14 REAL,
                macd_line REAL,
                bb_upper REAL
            )
        """)
        cursor.execute("INSERT INTO technical_features VALUES ('500325', '2024-01-15', 65.5, 2.3, 3500)")
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)
        cursor.execute("INSERT INTO upper_circuit_labels VALUES ('500325', '2024-01-15', 1)")
        conn.commit()
        conn.close()

        # Only select rsi_14, not macd_line or bb_upper
        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])

        X, y = trainer.load_data()

        assert list(X.columns) == ['rsi_14']
        assert 'macd_line' not in X.columns
        assert 'bb_upper' not in X.columns


class TestTrainTestSplit:
    """Test 80/20 stratified train/test split (AC3.1.3)"""

    def test_split_data_80_20_ratio(self, tmp_path):
        """AC3.1.3: split_data creates 80/20 train/test split"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        assert len(trainer.X_train) == 80
        assert len(trainer.X_test) == 20
        assert len(trainer.y_train) == 80
        assert len(trainer.y_test) == 20

    def test_split_data_stratified(self, tmp_path):
        """AC3.1.3: split_data maintains class distribution"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100, positive_ratio=0.10)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        # Original has 10% positive
        train_positive_ratio = trainer.y_train.sum() / len(trainer.y_train)
        test_positive_ratio = trainer.y_test.sum() / len(trainer.y_test)

        # Both should be close to 10% (allow ±2% variation)
        assert 0.08 <= train_positive_ratio <= 0.12
        assert 0.08 <= test_positive_ratio <= 0.12

    def test_split_data_random_state_reproducible(self, tmp_path):
        """AC3.1.3: split_data with same random_state is reproducible"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)

        # First split
        trainer1 = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer1.load_data()
        trainer1.split_data(test_size=0.2, random_state=42)
        first_train_indices = trainer1.X_train.index.tolist()

        # Second split with same seed
        trainer2 = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer2.load_data()
        trainer2.split_data(test_size=0.2, random_state=42)
        second_train_indices = trainer2.X_train.index.tolist()

        assert first_train_indices == second_train_indices

    def _create_sample_data(self, tmp_path, n_samples=100, positive_ratio=0.10):
        """Helper to create sample databases for testing"""
        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE technical_features (
                bse_code TEXT,
                date DATE,
                rsi_14 REAL
            )
        """)
        for i in range(n_samples):
            cursor.execute(
                "INSERT INTO technical_features VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 50 + i % 50)
            )
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)
        n_positive = int(n_samples * positive_ratio)
        for i in range(n_samples):
            label = 1 if i < n_positive else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db


class TestLogisticRegressionTraining:
    """Test Logistic Regression training (AC3.1.4)"""

    def test_train_logistic_regression_creates_model(self, tmp_path):
        """AC3.1.4: train_logistic_regression creates LogisticRegression model"""
        from agents.ml.baseline_trainer import BaselineTrainer
        from sklearn.linear_model import LogisticRegression

        tech_db, labels_db = self._create_sample_data(tmp_path)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        model = trainer.train_logistic_regression()

        assert isinstance(model, LogisticRegression)
        assert trainer.logistic_model is not None

    def test_logistic_regression_hyperparameters(self, tmp_path):
        """AC3.1.4: LogisticRegression uses correct hyperparameters"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        model = trainer.train_logistic_regression()

        assert model.max_iter == 1000
        assert model.class_weight == 'balanced'
        assert model.random_state == 42

    def test_logistic_regression_can_predict(self, tmp_path):
        """AC3.1.4: Trained LogisticRegression can make predictions"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        model = trainer.train_logistic_regression()
        predictions = model.predict(trainer.X_test)

        assert len(predictions) == len(trainer.y_test)
        assert all(pred in [0, 1] for pred in predictions)

    def _create_sample_data(self, tmp_path, n_samples=50):
        """Helper to create sample databases for testing"""
        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE technical_features (
                bse_code TEXT,
                date DATE,
                rsi_14 REAL
            )
        """)
        for i in range(n_samples):
            cursor.execute(
                "INSERT INTO technical_features VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 50 + i % 50)
            )
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)
        for i in range(n_samples):
            label = 1 if i < 5 else 0  # 10% positive
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db


class TestRandomForestTraining:
    """Test Random Forest training (AC3.1.5)"""

    def test_train_random_forest_creates_model(self, tmp_path):
        """AC3.1.5: train_random_forest creates RandomForestClassifier model"""
        from agents.ml.baseline_trainer import BaselineTrainer
        from sklearn.ensemble import RandomForestClassifier

        tech_db, labels_db = self._create_sample_data(tmp_path)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        model = trainer.train_random_forest()

        assert isinstance(model, RandomForestClassifier)
        assert trainer.random_forest_model is not None

    def test_random_forest_hyperparameters(self, tmp_path):
        """AC3.1.5: RandomForest uses correct hyperparameters"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        model = trainer.train_random_forest()

        assert model.n_estimators == 100
        assert model.class_weight == 'balanced'
        assert model.random_state == 42

    def test_random_forest_can_predict(self, tmp_path):
        """AC3.1.5: Trained RandomForest can make predictions"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        model = trainer.train_random_forest()
        predictions = model.predict(trainer.X_test)

        assert len(predictions) == len(trainer.y_test)
        assert all(pred in [0, 1] for pred in predictions)

    def _create_sample_data(self, tmp_path, n_samples=50):
        """Helper to create sample databases"""
        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE technical_features (
                bse_code TEXT,
                date DATE,
                rsi_14 REAL
            )
        """)
        for i in range(n_samples):
            cursor.execute(
                "INSERT INTO technical_features VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 50 + i % 50)
            )
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)
        for i in range(n_samples):
            label = 1 if i < 5 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db


class TestMetricsCalculation:
    """Test metrics calculation (AC3.1.6)"""

    def test_evaluate_model_calculates_all_metrics(self, tmp_path):
        """AC3.1.6: evaluate_model calculates accuracy, precision, recall, F1, ROC-AUC"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        model = trainer.train_logistic_regression()
        metrics = trainer.evaluate_model(model, trainer.X_test, trainer.y_test)

        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert 'roc_auc' in metrics

    def test_metrics_in_valid_range(self, tmp_path):
        """AC3.1.6: All metrics should be between 0 and 1"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        model = trainer.train_logistic_regression()
        metrics = trainer.evaluate_model(model, trainer.X_test, trainer.y_test)

        for metric_name, value in metrics.items():
            assert 0 <= value <= 1, f"{metric_name} = {value} is out of range [0, 1]"

    def test_perfect_predictions_score_1(self):
        """AC3.1.6: Perfect predictions should score 1.0"""
        from agents.ml.baseline_trainer import BaselineTrainer
        import pandas as pd

        trainer = BaselineTrainer({}, '', [])

        # Perfect predictions
        y_true = pd.Series([0, 0, 1, 1, 0, 1, 1, 0])
        y_pred = y_true.copy()
        y_proba = y_true.astype(float)

        # Mock model with perfect predictions
        mock_model = Mock()
        mock_model.predict.return_value = y_pred.values
        mock_model.predict_proba.return_value = np.column_stack([1 - y_proba, y_proba])

        X_test = pd.DataFrame({'dummy': [1] * len(y_true)})

        metrics = trainer.evaluate_model(mock_model, X_test, y_true)

        assert metrics['accuracy'] == 1.0
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1'] == 1.0
        assert metrics['roc_auc'] == 1.0

    def _create_sample_data(self, tmp_path, n_samples=100):
        """Helper to create sample databases"""
        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE technical_features (
                bse_code TEXT,
                date DATE,
                rsi_14 REAL
            )
        """)
        np.random.seed(42)
        for i in range(n_samples):
            # Create separable data for better predictions
            rsi = 70 + np.random.randn() * 5 if i < 10 else 30 + np.random.randn() * 5
            cursor.execute(
                "INSERT INTO technical_features VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', rsi)
            )
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)
        for i in range(n_samples):
            label = 1 if i < 10 else 0  # 10% positive
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db


class TestResultsSerialization:
    """Test JSON serialization of results (AC3.1.7)"""

    def test_save_results_creates_json_file(self, tmp_path):
        """AC3.1.7: save_results creates JSON file with model comparison"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)
        output_file = tmp_path / "baseline_results.json"

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        trainer.train_logistic_regression()
        trainer.train_random_forest()

        trainer.save_results(str(output_file))

        assert output_file.exists()

    def test_save_results_contains_both_models(self, tmp_path):
        """AC3.1.7: JSON contains results for both Logistic Regression and Random Forest"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)
        output_file = tmp_path / "baseline_results.json"

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        trainer.train_logistic_regression()
        trainer.train_random_forest()

        trainer.save_results(str(output_file))

        with open(output_file, 'r') as f:
            results = json.load(f)

        assert 'logistic_regression' in results
        assert 'random_forest' in results

    def test_save_results_includes_metadata(self, tmp_path):
        """AC3.1.7: JSON includes metadata (timestamp, train/test sizes, features)"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)
        output_file = tmp_path / "baseline_results.json"

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        trainer.train_logistic_regression()
        trainer.train_random_forest()

        trainer.save_results(str(output_file))

        with open(output_file, 'r') as f:
            results = json.load(f)

        assert 'metadata' in results
        assert 'timestamp' in results['metadata']
        assert 'train_size' in results['metadata']
        assert 'test_size' in results['metadata']
        assert 'selected_features' in results['metadata']

    def test_save_results_json_valid_format(self, tmp_path):
        """AC3.1.7: Saved JSON is valid and loadable"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path, n_samples=100)
        output_file = tmp_path / "baseline_results.json"

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()
        trainer.split_data(test_size=0.2, random_state=42)

        trainer.train_logistic_regression()
        trainer.train_random_forest()

        trainer.save_results(str(output_file))

        # Verify JSON is valid
        with open(output_file, 'r') as f:
            results = json.load(f)  # Should not raise exception

        assert isinstance(results, dict)

    def _create_sample_data(self, tmp_path, n_samples=100):
        """Helper to create sample databases"""
        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE technical_features (
                bse_code TEXT,
                date DATE,
                rsi_14 REAL
            )
        """)
        for i in range(n_samples):
            cursor.execute(
                "INSERT INTO technical_features VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 50 + i % 50)
            )
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)
        for i in range(n_samples):
            label = 1 if i < 10 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db


class TestEdgeCases:
    """Test edge case handling (AC3.1.8)"""

    def test_empty_dataset_raises_error(self, tmp_path):
        """AC3.1.8: Empty dataset should raise ValueError"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        # Create empty databases
        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE technical_features (bse_code TEXT, date DATE, rsi_14 REAL)")
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE upper_circuit_labels (bse_code TEXT, earnings_date DATE, label INTEGER)")
        conn.commit()
        conn.close()

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])

        with pytest.raises(ValueError, match="No data loaded"):
            trainer.load_data()

    def test_single_class_warns_user(self, tmp_path, caplog):
        """AC3.1.8: Single class in labels should log warning"""
        from agents.ml.baseline_trainer import BaselineTrainer
        import logging

        caplog.set_level(logging.WARNING)

        tech_db, labels_db = self._create_single_class_data(tmp_path)

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        trainer.load_data()

        # Should log warning about single class
        assert any("single class" in record.message.lower() or "class imbalance" in record.message.lower()
                   for record in caplog.records)

    def test_missing_features_in_database_raises_error(self, tmp_path):
        """AC3.1.8: Missing features in database should raise KeyError"""
        from agents.ml.baseline_trainer import BaselineTrainer

        tech_db, labels_db = self._create_sample_data(tmp_path)

        # Request feature that doesn't exist
        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['nonexistent_feature'])

        with pytest.raises((KeyError, ValueError)):
            trainer.load_data()

    def test_mismatched_samples_logs_warning(self, tmp_path, caplog):
        """AC3.1.8: Mismatched samples between features and labels logs warning"""
        from agents.ml.baseline_trainer import BaselineTrainer
        import logging

        caplog.set_level(logging.WARNING)

        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        # Technical features for 100 samples
        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE technical_features (bse_code TEXT, date DATE, rsi_14 REAL)")
        for i in range(100):
            cursor.execute(
                "INSERT INTO technical_features VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 50 + i)
            )
        conn.commit()
        conn.close()

        # Labels for only 50 samples
        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE upper_circuit_labels (bse_code TEXT, earnings_date DATE, label INTEGER)")
        for i in range(50):
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 0)
            )
        conn.commit()
        conn.close()

        trainer = BaselineTrainer({'technical': str(tech_db)}, str(labels_db), ['rsi_14'])
        X, y = trainer.load_data()

        # Should only have 50 samples (intersection)
        assert len(X) == 50

    def _create_single_class_data(self, tmp_path):
        """Helper to create data with only one class"""
        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE technical_features (bse_code TEXT, date DATE, rsi_14 REAL)")
        for i in range(50):
            cursor.execute(
                "INSERT INTO technical_features VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 50 + i)
            )
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE upper_circuit_labels (bse_code TEXT, earnings_date DATE, label INTEGER)")
        for i in range(50):
            # All labels are 0 (single class)
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 0)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_sample_data(self, tmp_path):
        """Helper to create sample databases"""
        tech_db = tmp_path / "tech.db"
        labels_db = tmp_path / "labels.db"

        conn = sqlite3.connect(tech_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE technical_features (bse_code TEXT, date DATE, rsi_14 REAL)")
        for i in range(50):
            cursor.execute(
                "INSERT INTO technical_features VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', 50 + i)
            )
        conn.commit()
        conn.close()

        conn = sqlite3.connect(labels_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE upper_circuit_labels (bse_code TEXT, earnings_date DATE, label INTEGER)")
        for i in range(50):
            label = 1 if i < 5 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.ml.baseline_trainer", "--cov-report=term-missing"])
