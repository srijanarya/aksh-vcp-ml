"""
Story 3.3: Hyperparameter Tuning

Uses Optuna framework to optimize hyperparameters for XGBoost, LightGBM, and Neural Network
models to achieve F1 ≥ 0.70 on upper circuit prediction task.

Optimization Strategy:
- TPE (Tree-structured Parzen Estimator) sampler for efficient search
- 5-fold stratified cross-validation in objective function
- n_trials ≥ 50 per model (default, configurable for testing)
- Random state for reproducibility

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, Tuple, List, Optional
import numpy as np
import pandas as pd
from pathlib import Path

# Optuna for hyperparameter tuning
import optuna
from optuna.samplers import TPESampler

# Advanced models
import xgboost as xgb
import lightgbm as lgb
from sklearn.neural_network import MLPClassifier

# Utilities
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import f1_score

# Inherit from AdvancedTrainer to reuse data loading
from agents.ml.advanced_trainer import AdvancedTrainer

logger = logging.getLogger(__name__)


class HyperparameterTuner(AdvancedTrainer):
    """
    Hyperparameter tuning using Optuna for advanced models.

    Inherits from AdvancedTrainer to reuse:
    - Data loading from multiple databases
    - Train/test splitting
    - Feature selection

    Adds:
    - Optuna study creation with TPE sampler
    - Cross-validation objective functions
    - Hyperparameter optimization for XGBoost, LightGBM, Neural Network
    - Results serialization with best parameters

    Performance Target:
    - F1 Score ≥ 0.70 (exceed advanced models baseline: 0.65)
    """

    def __init__(
        self,
        technical_db_path: str,
        financial_db_path: str,
        sentiment_db_path: str,
        seasonality_db_path: str,
        selected_features_path: str,
        labels_db_path: str,
        random_state: int = 42,
        n_trials: int = 50,
        cv_folds: int = 5,
        verbose: bool = False
    ):
        """
        Initialize hyperparameter tuner (AC3.3.1)

        Args:
            technical_db_path: Path to technical_features.db
            financial_db_path: Path to financial_features.db
            sentiment_db_path: Path to sentiment_features.db
            seasonality_db_path: Path to seasonality_features.db
            selected_features_path: Path to selected_features.json (25 features)
            labels_db_path: Path to upper_circuit_labels.db
            random_state: Random seed for reproducibility (default: 42)
            n_trials: Number of Optuna trials per model (default: 50)
            cv_folds: Number of cross-validation folds (default: 5)
            verbose: Whether to show Optuna logs (default: False)
        """
        # Initialize parent class
        super().__init__(
            technical_db_path=technical_db_path,
            financial_db_path=financial_db_path,
            sentiment_db_path=sentiment_db_path,
            seasonality_db_path=seasonality_db_path,
            selected_features_path=selected_features_path,
            labels_db_path=labels_db_path,
            random_state=random_state
        )

        self.n_trials = n_trials
        self.cv_folds = cv_folds
        self.verbose = verbose

        # Storage for best parameters and scores
        self.xgboost_best_params = None
        self.xgboost_best_score = None
        self.xgboost_n_trials = None

        self.lightgbm_best_params = None
        self.lightgbm_best_score = None
        self.lightgbm_n_trials = None

        self.neural_network_best_params = None
        self.neural_network_best_score = None
        self.neural_network_n_trials = None

        # Suppress Optuna logs if not verbose
        if not self.verbose:
            optuna.logging.set_verbosity(optuna.logging.WARNING)

        logger.info(
            f"HyperparameterTuner initialized: n_trials={n_trials}, "
            f"cv_folds={cv_folds}, random_state={random_state}"
        )

    def _create_study(self, direction: str = 'maximize') -> optuna.Study:
        """
        Create Optuna study with TPE sampler (AC3.3.2)

        Args:
            direction: Optimization direction ('maximize' for F1 score)

        Returns:
            Optuna study configured with TPE sampler
        """
        sampler = TPESampler(seed=self.random_state)
        study = optuna.create_study(direction=direction, sampler=sampler)
        return study

    def _cross_validate_f1(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        params: Dict,
        model_type: str
    ) -> float:
        """
        Cross-validate model with given parameters (AC3.3.6)

        Args:
            X: Training features
            y: Training labels
            params: Hyperparameters to evaluate
            model_type: 'xgboost', 'lightgbm', or 'neural_network'

        Returns:
            Mean F1 score across CV folds
        """
        cv = StratifiedKFold(n_splits=self.cv_folds, shuffle=True, random_state=self.random_state)
        f1_scores = []

        for train_idx, val_idx in cv.split(X, y):
            X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
            y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]

            # Train model based on type
            if model_type == 'xgboost':
                # Calculate scale_pos_weight for this fold
                n_negative = (y_train_fold == 0).sum()
                n_positive = (y_train_fold == 1).sum()
                scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1.0

                model = xgb.XGBClassifier(
                    max_depth=params['max_depth'],
                    n_estimators=params['n_estimators'],
                    learning_rate=params['learning_rate'],
                    min_child_weight=params['min_child_weight'],
                    scale_pos_weight=scale_pos_weight,
                    random_state=self.random_state,
                    eval_metric='logloss',
                    use_label_encoder=False
                )

            elif model_type == 'lightgbm':
                model = lgb.LGBMClassifier(
                    num_leaves=params['num_leaves'],
                    n_estimators=params['n_estimators'],
                    learning_rate=params['learning_rate'],
                    min_child_samples=params['min_child_samples'],
                    class_weight='balanced',
                    random_state=self.random_state,
                    verbose=-1
                )

            elif model_type == 'neural_network':
                model = MLPClassifier(
                    hidden_layer_sizes=params['hidden_layer_sizes'],
                    learning_rate_init=params['learning_rate_init'],
                    alpha=params['alpha'],
                    activation='relu',
                    max_iter=500,
                    early_stopping=True,
                    random_state=self.random_state,
                    verbose=False
                )

            else:
                raise ValueError(f"Unknown model_type: {model_type}")

            # Train and evaluate
            model.fit(X_train_fold, y_train_fold)
            y_pred = model.predict(X_val_fold)
            f1 = f1_score(y_val_fold, y_pred, zero_division=0)
            f1_scores.append(f1)

        # Return mean F1 score
        mean_f1 = np.mean(f1_scores)
        return mean_f1

    def tune_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict:
        """
        Tune XGBoost hyperparameters using Optuna (AC3.3.3)

        Hyperparameter ranges:
        - max_depth: 3-10 (tree depth)
        - n_estimators: 100-300 (number of trees)
        - learning_rate: 0.01-0.3 (step size)
        - min_child_weight: 1-10 (minimum sum of instance weight in child)

        Args:
            X_train: Training features
            y_train: Training labels

        Returns:
            Dictionary with best hyperparameters
        """
        logger.info(f"Starting XGBoost hyperparameter tuning: {self.n_trials} trials")

        def objective(trial):
            params = {
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'n_estimators': trial.suggest_int('n_estimators', 100, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10)
            }

            # Cross-validate with these parameters
            f1 = self._cross_validate_f1(X_train, y_train, params, 'xgboost')
            return f1

        # Create and run study
        study = self._create_study(direction='maximize')
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=self.verbose)

        # Store results
        self.xgboost_best_params = study.best_params
        self.xgboost_best_score = study.best_value
        self.xgboost_n_trials = len(study.trials)

        logger.info(
            f"XGBoost tuning complete: best_f1={self.xgboost_best_score:.4f}, "
            f"params={self.xgboost_best_params}"
        )

        return self.xgboost_best_params

    def tune_lightgbm(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict:
        """
        Tune LightGBM hyperparameters using Optuna (AC3.3.4)

        Hyperparameter ranges:
        - num_leaves: 20-50 (tree complexity)
        - n_estimators: 100-300 (number of trees)
        - learning_rate: 0.01-0.3 (step size)
        - min_child_samples: 5-50 (minimum data in leaf)

        Args:
            X_train: Training features
            y_train: Training labels

        Returns:
            Dictionary with best hyperparameters
        """
        logger.info(f"Starting LightGBM hyperparameter tuning: {self.n_trials} trials")

        def objective(trial):
            params = {
                'num_leaves': trial.suggest_int('num_leaves', 20, 50),
                'n_estimators': trial.suggest_int('n_estimators', 100, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 50)
            }

            # Cross-validate with these parameters
            f1 = self._cross_validate_f1(X_train, y_train, params, 'lightgbm')
            return f1

        # Create and run study
        study = self._create_study(direction='maximize')
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=self.verbose)

        # Store results
        self.lightgbm_best_params = study.best_params
        self.lightgbm_best_score = study.best_value
        self.lightgbm_n_trials = len(study.trials)

        logger.info(
            f"LightGBM tuning complete: best_f1={self.lightgbm_best_score:.4f}, "
            f"params={self.lightgbm_best_params}"
        )

        return self.lightgbm_best_params

    def tune_neural_network(self, X_train: pd.DataFrame, y_train: pd.Series) -> Dict:
        """
        Tune Neural Network hyperparameters using Optuna (AC3.3.5)

        Hyperparameter ranges:
        - hidden_layer_sizes: Various architectures (50), (100), (100,50), (150,75), (200,100)
        - learning_rate_init: 0.0001-0.01 (initial learning rate)
        - alpha: 0.0001-0.01 (L2 regularization)

        Args:
            X_train: Training features
            y_train: Training labels

        Returns:
            Dictionary with best hyperparameters
        """
        logger.info(f"Starting Neural Network hyperparameter tuning: {self.n_trials} trials")

        def objective(trial):
            # Suggest architecture
            architecture_idx = trial.suggest_categorical('architecture', [0, 1, 2, 3, 4])
            architectures = [
                (50,),
                (100,),
                (100, 50),
                (150, 75),
                (200, 100)
            ]
            hidden_layer_sizes = architectures[architecture_idx]

            params = {
                'hidden_layer_sizes': hidden_layer_sizes,
                'learning_rate_init': trial.suggest_float('learning_rate_init', 0.0001, 0.01, log=True),
                'alpha': trial.suggest_float('alpha', 0.0001, 0.01, log=True)
            }

            # Cross-validate with these parameters
            f1 = self._cross_validate_f1(X_train, y_train, params, 'neural_network')
            return f1

        # Create and run study
        study = self._create_study(direction='maximize')
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=self.verbose)

        # Store results (convert architecture index back to tuple)
        best_params = study.best_params.copy()
        architectures = [(50,), (100,), (100, 50), (150, 75), (200, 100)]
        best_params['hidden_layer_sizes'] = architectures[best_params['architecture']]
        del best_params['architecture']

        self.neural_network_best_params = best_params
        self.neural_network_best_score = study.best_value
        self.neural_network_n_trials = len(study.trials)

        logger.info(
            f"Neural Network tuning complete: best_f1={self.neural_network_best_score:.4f}, "
            f"params={self.neural_network_best_params}"
        )

        return self.neural_network_best_params

    def get_all_results(self) -> Dict:
        """
        Compile all tuning results into a single dictionary

        Returns:
            Dictionary with results for all models and metadata
        """
        results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'n_trials': self.n_trials,
                'cv_folds': self.cv_folds,
                'random_state': self.random_state,
                'story': '3.3',
                'description': 'Hyperparameter Tuning with Optuna (TPE Sampler)'
            },
            'xgboost': {
                'best_params': self.xgboost_best_params,
                'best_score': round(self.xgboost_best_score, 4) if self.xgboost_best_score is not None else None,
                'n_trials': self.xgboost_n_trials
            },
            'lightgbm': {
                'best_params': self.lightgbm_best_params,
                'best_score': round(self.lightgbm_best_score, 4) if self.lightgbm_best_score is not None else None,
                'n_trials': self.lightgbm_n_trials
            },
            'neural_network': {
                'best_params': self.neural_network_best_params,
                'best_score': round(self.neural_network_best_score, 4) if self.neural_network_best_score is not None else None,
                'n_trials': self.neural_network_n_trials
            }
        }

        return results

    def save_results(self, results: Dict, output_path: str):
        """
        Save tuning results to JSON (AC3.3.7)

        Args:
            results: Dict with tuning results (from get_all_results)
            output_path: Path to save JSON file

        Output format:
        {
            "metadata": {
                "timestamp": "2025-11-14T10:30:00",
                "n_trials": 50,
                "cv_folds": 5,
                "random_state": 42,
                "story": "3.3"
            },
            "xgboost": {
                "best_params": {"max_depth": 8, "n_estimators": 250, ...},
                "best_score": 0.72,
                "n_trials": 50
            },
            "lightgbm": {...},
            "neural_network": {...}
        }
        """
        logger.info(f"Saving tuning results to {output_path}...")

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Tuning results saved successfully to {output_path}")

        # Log comparison table
        logger.info("\n" + "="*80)
        logger.info("HYPERPARAMETER TUNING RESULTS")
        logger.info("="*80)
        logger.info(f"{'Model':<20} {'Best F1':<15} {'n_trials':<10}")
        logger.info("-"*80)

        xgb_score = results['xgboost']['best_score']
        lgb_score = results['lightgbm']['best_score']
        nn_score = results['neural_network']['best_score']

        # Handle None values gracefully
        xgb_str = f"{xgb_score:.4f}" if xgb_score is not None else "N/A"
        lgb_str = f"{lgb_score:.4f}" if lgb_score is not None else "N/A"
        nn_str = f"{nn_score:.4f}" if nn_score is not None else "N/A"

        logger.info(f"{'XGBoost':<20} {xgb_str:<15} {self.n_trials:<10}")
        logger.info(f"{'LightGBM':<20} {lgb_str:<15} {self.n_trials:<10}")
        logger.info(f"{'Neural Network':<20} {nn_str:<15} {self.n_trials:<10}")

        logger.info("="*80)

        # Check if F1 target met (filter out None values)
        scores = [s for s in [xgb_score, lgb_score, nn_score] if s is not None]
        if scores:
            best_f1 = max(scores)
        else:
            logger.warning("No valid scores to compare")
            return
        if best_f1 >= 0.70:
            logger.info(f"SUCCESS: Best F1 score {best_f1:.4f} meets target >= 0.70")
        else:
            logger.warning(f"WARNING: Best F1 score {best_f1:.4f} below target 0.70")

        logger.info(f"\nBest hyperparameters saved to: {output_path}")
