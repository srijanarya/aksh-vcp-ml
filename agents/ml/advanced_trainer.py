"""
Story 3.2: Advanced Models Training

Trains advanced XGBoost, LightGBM, and Neural Network models on 25 selected features
to predict upper circuit events. Target: F1 ≥ 0.65 (exceed baseline performance).

Models:
- XGBoost: Gradient boosting with trees (high performance)
- LightGBM: Efficient gradient boosting (faster training)
- Neural Network: MLPClassifier with 2 hidden layers (non-linear patterns)

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

# Advanced models
import xgboost as xgb
import lightgbm as lgb
from sklearn.neural_network import MLPClassifier

# Utilities
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)

logger = logging.getLogger(__name__)


class AdvancedTrainer:
    """
    Trains advanced models for upper circuit prediction.

    Supports:
    - XGBoost (gradient boosting with trees)
    - LightGBM (efficient gradient boosting)
    - Neural Network (MLP with 2 hidden layers)

    Performance Target:
    - F1 Score ≥ 0.65 (exceed baseline Random Forest: 0.60)
    - ROC-AUC ≥ 0.92 (exceed baseline)
    """

    def __init__(
        self,
        technical_db_path: str,
        financial_db_path: str,
        sentiment_db_path: str,
        seasonality_db_path: str,
        selected_features_path: str,
        labels_db_path: str,
        random_state: int = 42
    ):
        """
        Initialize advanced trainer (AC3.2.1)

        Args:
            technical_db_path: Path to technical_features.db
            financial_db_path: Path to financial_features.db
            sentiment_db_path: Path to sentiment_features.db
            seasonality_db_path: Path to seasonality_features.db
            selected_features_path: Path to selected_features.json (25 features)
            labels_db_path: Path to upper_circuit_labels.db
            random_state: Random seed for reproducibility (default: 42)
        """
        self.technical_db_path = technical_db_path
        self.financial_db_path = financial_db_path
        self.sentiment_db_path = sentiment_db_path
        self.seasonality_db_path = seasonality_db_path
        self.selected_features_path = selected_features_path
        self.labels_db_path = labels_db_path
        self.random_state = random_state

        # Load selected features
        self.selected_features = self._load_selected_features()

        # Data storage
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

        # Models (initialized as None before training)
        self.xgboost_model = None
        self.lightgbm_model = None
        self.neural_network_model = None

        # Results
        self.xgboost_metrics = None
        self.lightgbm_metrics = None
        self.neural_network_metrics = None

        logger.info(
            f"AdvancedTrainer initialized: {len(self.selected_features)} features, "
            f"random_state={random_state}"
        )

    def _load_selected_features(self) -> List[str]:
        """Load selected features from JSON file"""
        with open(self.selected_features_path, 'r') as f:
            features = json.load(f)
        logger.info(f"Loaded {len(features)} selected features from {self.selected_features_path}")
        return features

    def load_data(self) -> pd.DataFrame:
        """
        Load and combine features from multiple databases (AC3.2.2)

        Returns:
            DataFrame with selected features + label column

        Raises:
            ValueError: If no data loaded or missing features
        """
        logger.info("Loading data from feature databases...")

        # Step 1: Load labels
        labels_df = self._load_labels()

        if labels_df.empty:
            raise ValueError("No data loaded: labels database is empty")

        # Step 2: Load features from each DB
        # Define mapping of DB path to table name
        db_map = {
            self.technical_db_path: 'technical_features',
            self.financial_db_path: 'financial_features',
            self.sentiment_db_path: 'sentiment_features',
            self.seasonality_db_path: 'seasonality_features'
        }
        
        cleaned_dfs = []
        for db_path, table_name in db_map.items():
            df = self._load_features_from_db(db_path, table_name)
            if not df.empty:
                # Drop feature_id if present to avoid merge conflicts
                if 'feature_id' in df.columns:
                    df = df.drop(columns=['feature_id'])
                if 'created_at' in df.columns:
                    df = df.drop(columns=['created_at'])
                cleaned_dfs.append(df)
        
        if not cleaned_dfs:
             raise ValueError("No feature data loaded from any database")

        # Step 3: Merge features
        # Start with first features dataframe
        merged_features = cleaned_dfs[0]

        # Merge remaining features
        for features_df in cleaned_dfs[1:]:
            merged_features = pd.merge(
                merged_features,
                features_df,
                on=['bse_code', 'date'],
                how='outer'
            )

        # Step 4: Merge with labels (inner join to get only labeled samples)
        data = pd.merge(
            merged_features,
            labels_df,
            on=['bse_code', 'date'],
            how='inner'
        )

        if data.empty:
            raise ValueError("No data after merging features with labels")
        
        # Convert all feature columns to numeric (handles 'object' dtype issues)
        feature_cols = [col for col in data.columns if col not in ['bse_code', 'date', 'label']]
        for col in feature_cols:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Fill NaN values with 0 (simple imputation)
        data[feature_cols] = data[feature_cols].fillna(0)

        logger.info(f"Loaded {len(data)} samples with {len(merged_features.columns)-2} total features")

        # Step 5: Filter to selected features only
        missing_features = [f for f in self.selected_features if f not in data.columns]
        if missing_features:
            raise ValueError(f"Missing features in database: {missing_features}")

        # Return dataframe with selected features + label
        result_df = data[self.selected_features + ['label']].copy()

        logger.info(f"Final dataset: {len(result_df)} samples, {len(self.selected_features)} features")

        return result_df

    def _load_labels(self) -> pd.DataFrame:
        """Load labels from upper_circuit_labels.db"""
        conn = sqlite3.connect(self.labels_db_path)
        query = """
            SELECT bse_code, earnings_date, label
            FROM upper_circuit_labels
        """
        labels_df = pd.read_sql_query(query, conn)
        conn.close()

        # Rename earnings_date to date for consistency
        labels_df = labels_df.rename(columns={'earnings_date': 'date'})

        logger.info(f"Loaded {len(labels_df)} labels")
        return labels_df

    def _load_features_from_db(self, db_path: str, table_name: str) -> pd.DataFrame:
        """Load features from a specific database"""
        conn = sqlite3.connect(db_path)

        # Check if table exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            logger.warning(f"Table {table_name} not found in {db_path}")
            conn.close()
            return pd.DataFrame()

        # Load all columns
        query = f"SELECT * FROM {table_name}"
        features_df = pd.read_sql_query(query, conn)
        conn.close()

        logger.info(f"Loaded {len(features_df)} rows from {table_name}")
        return features_df

    def split_data(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split data into 80/20 stratified train/test sets

        Args:
            df: DataFrame with features + label column
            test_size: Fraction for test set (default: 0.2 = 20%)

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        logger.info(f"Splitting data: {int((1-test_size)*100)}% train, {int(test_size*100)}% test")

        X = df[self.selected_features]
        y = df['label']

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=self.random_state,
            stratify=y  # Stratified split to preserve class distribution
        )

        logger.info(
            f"Split complete: train={len(self.X_train)}, test={len(self.X_test)}, "
            f"train_positive={self.y_train.sum()}/{len(self.y_train)} "
            f"({self.y_train.sum()/len(self.y_train)*100:.1f}%), "
            f"test_positive={self.y_test.sum()}/{len(self.y_test)} "
            f"({self.y_test.sum()/len(self.y_test)*100:.1f}%)"
        )

        return self.X_train, self.X_test, self.y_train, self.y_test

    def train_xgboost(self, X_train, y_train) -> xgb.XGBClassifier:
        """
        Train XGBoost classifier (AC3.2.3)

        Returns:
            Trained XGBClassifier model

        Hyperparameters:
            - max_depth: 6 (tree depth)
            - n_estimators: 200 (number of trees)
            - learning_rate: 0.1 (step size)
            - scale_pos_weight: auto (handles class imbalance)
            - random_state: 42 (reproducibility)
        """
        logger.info("Training XGBoost model...")

        # Calculate scale_pos_weight to handle class imbalance
        n_negative = (y_train == 0).sum()
        n_positive = (y_train == 1).sum()
        scale_pos_weight = n_negative / n_positive if n_positive > 0 else 1.0

        logger.info(f"XGBoost scale_pos_weight: {scale_pos_weight:.2f} (negative/positive ratio)")

        self.xgboost_model = xgb.XGBClassifier(
            max_depth=6,
            n_estimators=200,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            random_state=self.random_state,
            eval_metric='logloss',
            use_label_encoder=False
        )

        self.xgboost_model.fit(X_train, y_train)

        logger.info("XGBoost training complete")

        return self.xgboost_model

    def train_lightgbm(self, X_train, y_train) -> lgb.LGBMClassifier:
        """
        Train LightGBM classifier (AC3.2.4)

        Returns:
            Trained LGBMClassifier model

        Hyperparameters:
            - num_leaves: 31 (tree complexity)
            - n_estimators: 200 (number of trees)
            - learning_rate: 0.1 (step size)
            - class_weight: 'balanced' (handles class imbalance)
            - random_state: 42 (reproducibility)
        """
        logger.info("Training LightGBM model...")

        self.lightgbm_model = lgb.LGBMClassifier(
            num_leaves=31,
            n_estimators=200,
            learning_rate=0.1,
            class_weight='balanced',
            random_state=self.random_state,
            verbose=-1  # Suppress training logs
        )

        self.lightgbm_model.fit(X_train, y_train)

        logger.info("LightGBM training complete")

        return self.lightgbm_model

    def train_neural_network(self, X_train, y_train) -> MLPClassifier:
        """
        Train Neural Network classifier (AC3.2.5)

        Returns:
            Trained MLPClassifier model

        Architecture:
            - Hidden layers: (100, 50) - 2 layers with 100 and 50 neurons
            - Activation: relu
            - max_iter: 500 (training epochs)
            - early_stopping: True (prevents overfitting)
            - learning_rate_init: 0.001 (initial learning rate)
            - random_state: 42 (reproducibility)
        """
        logger.info("Training Neural Network model...")

        self.neural_network_model = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            activation='relu',
            max_iter=500,
            early_stopping=True,
            learning_rate_init=0.001,
            random_state=self.random_state,
            verbose=False
        )

        self.neural_network_model.fit(X_train, y_train)

        logger.info("Neural Network training complete")

        return self.neural_network_model

    def evaluate_model(self, model, X_test, y_test) -> Dict[str, float]:
        """
        Calculate comprehensive metrics for a model (AC3.2.6)

        Args:
            model: Trained sklearn-compatible model
            X_test: Test features
            y_test: Test labels

        Returns:
            Dict with metrics: accuracy, precision, recall, f1, roc_auc

        Metrics:
            - Accuracy: Overall correctness (TP + TN) / Total
            - Precision: Of predicted positives, how many correct? TP / (TP + FP)
            - Recall: Of actual positives, how many caught? TP / (TP + FN)
            - F1: Harmonic mean of precision and recall
            - ROC-AUC: Area under ROC curve (probability-based)
        """
        # Get predictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]  # Probability of positive class

        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, y_proba)
        }

        # Round to 4 decimal places for readability
        metrics = {k: round(v, 4) for k, v in metrics.items()}

        return metrics

    def train_all_models(self) -> Dict:
        """
        Train all 3 advanced models and return results

        Returns:
            Dict with results for all models
        """
        logger.info("Starting training for all advanced models...")

        # Load and split data
        df = self.load_data()
        X_train, X_test, y_train, y_test = self.split_data(df)

        # Train XGBoost
        logger.info("="*60)
        xgb_model = self.train_xgboost(X_train, y_train)
        self.xgboost_metrics = self.evaluate_model(xgb_model, X_test, y_test)
        logger.info(f"XGBoost metrics: {self.xgboost_metrics}")

        # Train LightGBM
        logger.info("="*60)
        lgb_model = self.train_lightgbm(X_train, y_train)
        self.lightgbm_metrics = self.evaluate_model(lgb_model, X_test, y_test)
        logger.info(f"LightGBM metrics: {self.lightgbm_metrics}")

        # Train Neural Network
        logger.info("="*60)
        nn_model = self.train_neural_network(X_train, y_train)
        self.neural_network_metrics = self.evaluate_model(nn_model, X_test, y_test)
        logger.info(f"Neural Network metrics: {self.neural_network_metrics}")

        logger.info("="*60)
        logger.info("All models trained successfully!")

        # Compile results
        results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'train_size': len(X_train),
                'test_size': len(X_test),
                'feature_count': len(self.selected_features),
                'positive_ratio': round(y_test.sum() / len(y_test), 4),
                'story': '3.2',
                'description': 'Advanced Models: XGBoost vs LightGBM vs Neural Network'
            },
            'xgboost': self.xgboost_metrics,
            'lightgbm': self.lightgbm_metrics,
            'neural_network': self.neural_network_metrics
        }

        return results

    def save_results(self, results: Dict, output_path: str):
        """
        Save model comparison results to JSON (AC3.2.7)

        Args:
            results: Dict with model results (from train_all_models)
            output_path: Path to save JSON file

        Output format:
        {
            "metadata": {
                "timestamp": "2025-11-14T10:30:00",
                "train_size": 160000,
                "test_size": 40000,
                "feature_count": 25,
                "positive_ratio": 0.10,
                "story": "3.2"
            },
            "xgboost": {
                "accuracy": 0.94,
                "precision": 0.58,
                "recall": 0.82,
                "f1": 0.68,
                "roc_auc": 0.92
            },
            "lightgbm": {
                "accuracy": 0.94,
                "precision": 0.56,
                "recall": 0.84,
                "f1": 0.67,
                "roc_auc": 0.93
            },
            "neural_network": {
                "accuracy": 0.93,
                "precision": 0.54,
                "recall": 0.81,
                "f1": 0.65,
                "roc_auc": 0.91
            }
        }
        """
        logger.info(f"Saving results to {output_path}...")

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved successfully to {output_path}")

        # Log comparison table
        logger.info("\n" + "="*80)
        logger.info("ADVANCED MODELS COMPARISON")
        logger.info("="*80)
        logger.info(f"{'Metric':<15} {'XGBoost':<15} {'LightGBM':<15} {'Neural Network':<15}")
        logger.info("-"*80)
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
            xgb_val = results['xgboost'][metric]
            lgb_val = results['lightgbm'][metric]
            nn_val = results['neural_network'][metric]
            logger.info(f"{metric:<15} {xgb_val:<15.4f} {lgb_val:<15.4f} {nn_val:<15.4f}")
        logger.info("="*80)

        # Check if F1 target met
        best_f1 = max(results['xgboost']['f1'], results['lightgbm']['f1'], results['neural_network']['f1'])
        if best_f1 >= 0.65:
            logger.info(f"✅ SUCCESS: Best F1 score {best_f1:.4f} meets target ≥ 0.65")
        else:
            logger.warning(f"⚠️  WARNING: Best F1 score {best_f1:.4f} below target 0.65")
