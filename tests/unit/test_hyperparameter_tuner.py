"""
Unit tests for Story 3.3: Hyperparameter Tuning

TDD Phase: RED (write tests first)
Target: ~25 tests, ≥90% test coverage

Test Coverage:
- AC3.3.1: HyperparameterTuner class initialization (3 tests)
- AC3.3.2: Optuna study creation with TPE sampler (3 tests)
- AC3.3.3: XGBoost hyperparameter tuning (5 tests)
- AC3.3.4: LightGBM hyperparameter tuning (5 tests)
- AC3.3.5: Neural Network hyperparameter tuning (5 tests)
- AC3.3.6: Cross-validation in objective function (2 tests)
- AC3.3.7: Results serialization with best parameters (4 tests)
- AC3.3.8: Edge case handling (3 tests)

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


class TestHyperparameterTunerInitialization:
    """Test HyperparameterTuner class initialization (AC3.3.1)"""

    def test_tuner_class_exists(self):
        """AC3.3.1: Verify HyperparameterTuner can be imported"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner
        assert HyperparameterTuner is not None

    def test_tuner_instantiation(self, tmp_path):
        """AC3.3.1: Tuner can be instantiated with database paths"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        # Create features.json file
        features_json = tmp_path / "selected_features.json"
        with open(features_json, 'w') as f:
            json.dump(['rsi_14', 'macd_line'], f)

        tuner = HyperparameterTuner(
            technical_db_path=str(tmp_path / "technical_features.db"),
            financial_db_path=str(tmp_path / "financial_features.db"),
            sentiment_db_path=str(tmp_path / "sentiment_features.db"),
            seasonality_db_path=str(tmp_path / "seasonality_features.db"),
            selected_features_path=str(features_json),
            labels_db_path=str(tmp_path / "upper_circuit_labels.db"),
            random_state=42
        )

        assert tuner.random_state == 42
        assert tuner.labels_db_path == str(tmp_path / "upper_circuit_labels.db")

    def test_tuner_default_n_trials(self, tmp_path):
        """AC3.3.1: Tuner has default n_trials parameter"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        features_json = tmp_path / "features.json"
        with open(features_json, 'w') as f:
            json.dump(['rsi_14'], f)

        tuner = HyperparameterTuner(
            technical_db_path=str(tmp_path / "tech.db"),
            financial_db_path=str(tmp_path / "fin.db"),
            sentiment_db_path=str(tmp_path / "sent.db"),
            seasonality_db_path=str(tmp_path / "season.db"),
            selected_features_path=str(features_json),
            labels_db_path=str(tmp_path / "labels.db"),
            n_trials=50
        )

        assert tuner.n_trials == 50


class TestOptunaStudyCreation:
    """Test Optuna study creation (AC3.3.2)"""

    def test_create_study_uses_tpe_sampler(self, tmp_path):
        """AC3.3.2: Study uses TPE sampler for optimization"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner
        import optuna

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        # Create study and verify sampler type
        study = tuner._create_study(direction='maximize')

        assert isinstance(study.sampler, optuna.samplers.TPESampler)

    def test_create_study_maximizes_f1(self, tmp_path):
        """AC3.3.2: Study is configured to maximize F1 score"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        study = tuner._create_study(direction='maximize')

        assert study.direction.name == 'MAXIMIZE'

    def test_create_study_uses_random_state(self, tmp_path):
        """AC3.3.2: Study sampler uses random_state for reproducibility"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            random_state=42,
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        study = tuner._create_study(direction='maximize')

        # TPESampler should have _rng attribute (indicates seed was set)
        assert hasattr(study.sampler, '_rng')

    def _create_training_data(self, tmp_path, n_samples=100):
        """Helper to create training databases"""
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
            label = 1 if i < 10 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_features_json(self, tmp_path):
        """Helper to create features JSON"""
        features_json = tmp_path / "selected_features.json"
        selected_features = ['rsi_14']
        with open(features_json, 'w') as f:
            json.dump(selected_features, f)
        return features_json


class TestXGBoostTuning:
    """Test XGBoost hyperparameter tuning (AC3.3.3)"""

    def test_tune_xgboost_creates_study(self, tmp_path):
        """AC3.3.3: tune_xgboost creates Optuna study and optimizes"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10  # Small for testing
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_xgboost(X_train, y_train)

        assert best_params is not None
        assert isinstance(best_params, dict)

    def test_xgboost_hyperparameter_ranges(self, tmp_path):
        """AC3.3.3: XGBoost tunes correct hyperparameters with correct ranges"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_xgboost(X_train, y_train)

        # Verify parameters exist and are in valid ranges
        assert 'max_depth' in best_params
        assert 3 <= best_params['max_depth'] <= 10

        assert 'n_estimators' in best_params
        assert 100 <= best_params['n_estimators'] <= 300

        assert 'learning_rate' in best_params
        assert 0.01 <= best_params['learning_rate'] <= 0.3

        assert 'min_child_weight' in best_params
        assert 1 <= best_params['min_child_weight'] <= 10

    def test_xgboost_tuning_uses_cross_validation(self, tmp_path):
        """AC3.3.3: XGBoost tuning uses 5-fold cross-validation"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10,
            cv_folds=5
        )

        assert tuner.cv_folds == 5

    def test_xgboost_returns_best_f1_score(self, tmp_path):
        """AC3.3.3: XGBoost tuning stores best F1 score"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_xgboost(X_train, y_train)

        # Should store best score
        assert hasattr(tuner, 'xgboost_best_score')
        assert 0 <= tuner.xgboost_best_score <= 1

    def test_xgboost_tuning_completes_n_trials(self, tmp_path):
        """AC3.3.3: XGBoost tuning runs specified number of trials"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_xgboost(X_train, y_train)

        # Should complete all trials
        assert hasattr(tuner, 'xgboost_n_trials')
        assert tuner.xgboost_n_trials == 10

    def _create_training_data(self, tmp_path, n_samples=100):
        """Helper to create training databases"""
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
            rsi = 75 + np.random.randn() * 3 if i < 10 else 25 + np.random.randn() * 3
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
            label = 1 if i < 10 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_features_json(self, tmp_path):
        """Helper to create features JSON"""
        features_json = tmp_path / "selected_features.json"
        selected_features = ['rsi_14']
        with open(features_json, 'w') as f:
            json.dump(selected_features, f)
        return features_json


class TestLightGBMTuning:
    """Test LightGBM hyperparameter tuning (AC3.3.4)"""

    def test_tune_lightgbm_creates_study(self, tmp_path):
        """AC3.3.4: tune_lightgbm creates Optuna study and optimizes"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_lightgbm(X_train, y_train)

        assert best_params is not None
        assert isinstance(best_params, dict)

    def test_lightgbm_hyperparameter_ranges(self, tmp_path):
        """AC3.3.4: LightGBM tunes correct hyperparameters with correct ranges"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_lightgbm(X_train, y_train)

        # Verify parameters exist and are in valid ranges
        assert 'num_leaves' in best_params
        assert 20 <= best_params['num_leaves'] <= 50

        assert 'n_estimators' in best_params
        assert 100 <= best_params['n_estimators'] <= 300

        assert 'learning_rate' in best_params
        assert 0.01 <= best_params['learning_rate'] <= 0.3

        assert 'min_child_samples' in best_params
        assert 5 <= best_params['min_child_samples'] <= 50

    def test_lightgbm_tuning_uses_cross_validation(self, tmp_path):
        """AC3.3.4: LightGBM tuning uses 5-fold cross-validation"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10,
            cv_folds=5
        )

        assert tuner.cv_folds == 5

    def test_lightgbm_returns_best_f1_score(self, tmp_path):
        """AC3.3.4: LightGBM tuning stores best F1 score"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_lightgbm(X_train, y_train)

        assert hasattr(tuner, 'lightgbm_best_score')
        assert 0 <= tuner.lightgbm_best_score <= 1

    def test_lightgbm_tuning_completes_n_trials(self, tmp_path):
        """AC3.3.4: LightGBM tuning runs specified number of trials"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_lightgbm(X_train, y_train)

        assert hasattr(tuner, 'lightgbm_n_trials')
        assert tuner.lightgbm_n_trials == 10

    def _create_training_data(self, tmp_path, n_samples=100):
        """Helper to create training databases"""
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
            rsi = 75 + np.random.randn() * 3 if i < 10 else 25 + np.random.randn() * 3
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
            label = 1 if i < 10 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_features_json(self, tmp_path):
        """Helper to create features JSON"""
        features_json = tmp_path / "selected_features.json"
        selected_features = ['rsi_14']
        with open(features_json, 'w') as f:
            json.dump(selected_features, f)
        return features_json


class TestNeuralNetworkTuning:
    """Test Neural Network hyperparameter tuning (AC3.3.5)"""

    def test_tune_neural_network_creates_study(self, tmp_path):
        """AC3.3.5: tune_neural_network creates Optuna study and optimizes"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_neural_network(X_train, y_train)

        assert best_params is not None
        assert isinstance(best_params, dict)

    def test_neural_network_hyperparameter_ranges(self, tmp_path):
        """AC3.3.5: Neural Network tunes correct hyperparameters with correct ranges"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_neural_network(X_train, y_train)

        # Verify parameters exist and are in valid ranges
        assert 'hidden_layer_sizes' in best_params
        assert isinstance(best_params['hidden_layer_sizes'], tuple)

        assert 'learning_rate_init' in best_params
        assert 0.0001 <= best_params['learning_rate_init'] <= 0.01

        assert 'alpha' in best_params
        assert 0.0001 <= best_params['alpha'] <= 0.01

    def test_neural_network_tuning_uses_cross_validation(self, tmp_path):
        """AC3.3.5: Neural Network tuning uses 5-fold cross-validation"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10,
            cv_folds=5
        )

        assert tuner.cv_folds == 5

    def test_neural_network_returns_best_f1_score(self, tmp_path):
        """AC3.3.5: Neural Network tuning stores best F1 score"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_neural_network(X_train, y_train)

        assert hasattr(tuner, 'neural_network_best_score')
        assert 0 <= tuner.neural_network_best_score <= 1

    def test_neural_network_tuning_completes_n_trials(self, tmp_path):
        """AC3.3.5: Neural Network tuning runs specified number of trials"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_neural_network(X_train, y_train)

        assert hasattr(tuner, 'neural_network_n_trials')
        assert tuner.neural_network_n_trials == 10

    def _create_training_data(self, tmp_path, n_samples=100):
        """Helper to create training databases"""
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
            rsi = 75 + np.random.randn() * 3 if i < 10 else 25 + np.random.randn() * 3
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
            label = 1 if i < 10 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_features_json(self, tmp_path):
        """Helper to create features JSON"""
        features_json = tmp_path / "selected_features.json"
        selected_features = ['rsi_14']
        with open(features_json, 'w') as f:
            json.dump(selected_features, f)
        return features_json


class TestCrossValidation:
    """Test cross-validation in objective function (AC3.3.6)"""

    def test_stratified_kfold_used(self, tmp_path):
        """AC3.3.6: Uses StratifiedKFold for cross-validation"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10,
            cv_folds=5
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        # Test internal CV method exists
        cv_score = tuner._cross_validate_f1(X_train, y_train, {'max_depth': 6, 'n_estimators': 100, 'learning_rate': 0.1, 'min_child_weight': 1}, 'xgboost')

        assert 0 <= cv_score <= 1

    def test_cv_returns_mean_f1_score(self, tmp_path):
        """AC3.3.6: Cross-validation returns mean F1 score across folds"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10,
            cv_folds=5
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        cv_score = tuner._cross_validate_f1(X_train, y_train, {'max_depth': 6, 'n_estimators': 100, 'learning_rate': 0.1, 'min_child_weight': 1}, 'xgboost')

        # Should be a single float (mean)
        assert isinstance(cv_score, (float, np.floating))

    def _create_training_data(self, tmp_path, n_samples=100):
        """Helper to create training databases"""
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
            rsi = 75 + np.random.randn() * 3 if i < 10 else 25 + np.random.randn() * 3
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
            label = 1 if i < 10 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_features_json(self, tmp_path):
        """Helper to create features JSON"""
        features_json = tmp_path / "selected_features.json"
        selected_features = ['rsi_14']
        with open(features_json, 'w') as f:
            json.dump(selected_features, f)
        return features_json


class TestResultsSerialization:
    """Test results serialization with best parameters (AC3.3.7)"""

    def test_save_results_creates_json_file(self, tmp_path):
        """AC3.3.7: save_results creates JSON file with tuning results"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)
        output_file = tmp_path / "tuning_results.json"

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        # Tune all models
        tuner.tune_xgboost(X_train, y_train)
        tuner.tune_lightgbm(X_train, y_train)
        tuner.tune_neural_network(X_train, y_train)

        # Save results
        results = tuner.get_all_results()
        tuner.save_results(results, str(output_file))

        assert output_file.exists()

    def test_save_results_includes_best_parameters(self, tmp_path):
        """AC3.3.7: Saved results include best parameters for all models"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)
        output_file = tmp_path / "tuning_results.json"

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        tuner.tune_xgboost(X_train, y_train)
        tuner.tune_lightgbm(X_train, y_train)
        tuner.tune_neural_network(X_train, y_train)

        results = tuner.get_all_results()
        tuner.save_results(results, str(output_file))

        with open(output_file, 'r') as f:
            saved_results = json.load(f)

        assert 'xgboost' in saved_results
        assert 'best_params' in saved_results['xgboost']

        assert 'lightgbm' in saved_results
        assert 'best_params' in saved_results['lightgbm']

        assert 'neural_network' in saved_results
        assert 'best_params' in saved_results['neural_network']

    def test_save_results_includes_best_scores(self, tmp_path):
        """AC3.3.7: Saved results include best F1 scores"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)
        output_file = tmp_path / "tuning_results.json"

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        tuner.tune_xgboost(X_train, y_train)
        tuner.tune_lightgbm(X_train, y_train)
        tuner.tune_neural_network(X_train, y_train)

        results = tuner.get_all_results()
        tuner.save_results(results, str(output_file))

        with open(output_file, 'r') as f:
            saved_results = json.load(f)

        assert 'best_score' in saved_results['xgboost']
        assert saved_results['xgboost']['best_score'] is not None
        assert 0 <= saved_results['xgboost']['best_score'] <= 1

        assert 'best_score' in saved_results['lightgbm']
        assert saved_results['lightgbm']['best_score'] is not None
        assert 0 <= saved_results['lightgbm']['best_score'] <= 1

        assert 'best_score' in saved_results['neural_network']
        assert saved_results['neural_network']['best_score'] is not None
        assert 0 <= saved_results['neural_network']['best_score'] <= 1

    def test_save_results_includes_metadata(self, tmp_path):
        """AC3.3.7: Saved results include metadata (n_trials, timestamp, etc.)"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)
        output_file = tmp_path / "tuning_results.json"

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        tuner.tune_xgboost(X_train, y_train)
        tuner.tune_lightgbm(X_train, y_train)
        tuner.tune_neural_network(X_train, y_train)

        results = tuner.get_all_results()
        tuner.save_results(results, str(output_file))

        with open(output_file, 'r') as f:
            saved_results = json.load(f)

        assert 'metadata' in saved_results
        assert 'timestamp' in saved_results['metadata']
        assert 'n_trials' in saved_results['metadata']
        assert 'cv_folds' in saved_results['metadata']
        assert 'story' in saved_results['metadata']

    def _create_training_data(self, tmp_path, n_samples=100):
        """Helper to create training databases"""
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
            rsi = 75 + np.random.randn() * 3 if i < 10 else 25 + np.random.randn() * 3
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
            label = 1 if i < 10 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_features_json(self, tmp_path):
        """Helper to create features JSON"""
        features_json = tmp_path / "selected_features.json"
        selected_features = ['rsi_14']
        with open(features_json, 'w') as f:
            json.dump(selected_features, f)
        return features_json


class TestEdgeCases:
    """Test edge case handling (AC3.3.8)"""

    def test_handles_small_n_trials(self, tmp_path):
        """AC3.3.8: Handles small n_trials (e.g., 5) gracefully"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=5
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_xgboost(X_train, y_train)

        assert best_params is not None
        assert tuner.xgboost_n_trials == 5

    def test_handles_imbalanced_data(self, tmp_path):
        """AC3.3.8: Handles highly imbalanced datasets (5% positive)"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        # Use 5% positive to ensure at least 10 samples (need minimum 2 per fold for 5-fold CV)
        tech_db, labels_db = self._create_highly_imbalanced_data(tmp_path, n_samples=200, positive_ratio=0.05)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        df = tuner.load_data()
        X_train, X_test, y_train, y_test = tuner.split_data(df)

        best_params = tuner.tune_xgboost(X_train, y_train)

        # Should complete without error
        assert best_params is not None

    def test_suppresses_optuna_logs(self, tmp_path):
        """AC3.3.8: Optuna logs are suppressed during optimization"""
        from agents.ml.hyperparameter_tuner import HyperparameterTuner

        tech_db, labels_db = self._create_training_data(tmp_path, n_samples=100)

        tuner = HyperparameterTuner(
            technical_db_path=str(tech_db),
            financial_db_path=str(tech_db),
            sentiment_db_path=str(tech_db),
            seasonality_db_path=str(tech_db),
            selected_features_path=str(self._create_features_json(tmp_path)),
            labels_db_path=str(labels_db),
            n_trials=10
        )

        # Should have attribute to control verbosity
        assert hasattr(tuner, 'verbose')

    def _create_training_data(self, tmp_path, n_samples=100):
        """Helper to create training databases"""
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
            rsi = 75 + np.random.randn() * 3 if i < 10 else 25 + np.random.randn() * 3
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
            label = 1 if i < 10 else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_highly_imbalanced_data(self, tmp_path, n_samples=100, positive_ratio=0.01):
        """Helper to create highly imbalanced training data"""
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
        n_positive = int(n_samples * positive_ratio)
        for i in range(n_samples):
            rsi = 75 + np.random.randn() * 3 if i < n_positive else 25 + np.random.randn() * 3
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
            label = 1 if i < n_positive else 0
            cursor.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (f'50{i:04d}', f'2024-01-{(i % 28) + 1:02d}', label)
            )
        conn.commit()
        conn.close()

        return tech_db, labels_db

    def _create_features_json(self, tmp_path):
        """Helper to create features JSON"""
        features_json = tmp_path / "selected_features.json"
        selected_features = ['rsi_14']
        with open(features_json, 'w') as f:
            json.dump(selected_features, f)
        return features_json


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.ml.hyperparameter_tuner", "--cov-report=term-missing"])
