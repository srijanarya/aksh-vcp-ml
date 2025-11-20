"""
Story 3.1: Baseline Models Training

Trains baseline Logistic Regression and Random Forest models on 25 selected features
to predict upper circuit events. Target: Establish baseline performance metrics.

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import sqlite3
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

logger = logging.getLogger(__name__)


class BaselineTrainer:
    """
    Trains baseline models for upper circuit prediction.

    Supports:
    - Logistic Regression (interpretable, fast)
    - Random Forest (non-linear, ensemble)

    Performance:
    - Trains on 200K samples in <2 minutes
    - 80/20 stratified train/test split
    - Comprehensive metrics: accuracy, precision, recall, F1, ROC-AUC
    """

    def __init__(
        self,
        feature_dbs: Dict[str, str],
        labels_db: str,
        selected_features: List[str]
    ):
        """
        Initialize baseline trainer (AC3.1.1)

        Args:
            feature_dbs: Dict mapping database type to path
                Example: {
                    'technical': '/path/to/technical_features.db',
                    'financial': '/path/to/financial_features.db',
                    'sentiment': '/path/to/sentiment_features.db',
                    'seasonality': '/path/to/seasonality_features.db'
                }
            labels_db: Path to upper_circuit_labels.db
            selected_features: List of 25 selected feature names
                Example: ['rsi_14', 'macd_line', 'eps_growth', 'sentiment_score', 'quarter_q4']
        """
        self.feature_dbs = feature_dbs
        self.labels_db = labels_db
        self.selected_features = selected_features

        # Data storage
        self.X = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

        # Models (initialized as None before training)
        self.logistic_model = None
        self.random_forest_model = None

        # Results
        self.logistic_metrics = None
        self.random_forest_metrics = None

        logger.info(
            f"BaselineTrainer initialized: {len(selected_features)} features, "
            f"{len(feature_dbs)} databases"
        )

    def load_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load and combine features from multiple databases (AC3.1.2)

        Returns:
            Tuple of (X: features DataFrame, y: labels Series)

        Raises:
            ValueError: If no data loaded or missing features
        """
        logger.info("Loading data from feature databases...")

        # Step 1: Load labels
        labels_df = self._load_labels()

        if labels_df.empty:
            raise ValueError("No data loaded: labels database is empty")

        # Step 2: Load features from each database
        features_dfs = []

        for db_type, db_path in self.feature_dbs.items():
            logger.info(f"Loading features from {db_type} database...")
            features_df = self._load_features_from_db(db_path, db_type)

            if not features_df.empty:
                features_dfs.append(features_df)

        # Step 3: Merge all features
        if not features_dfs:
            raise ValueError("No features loaded from any database")

        # Drop metadata columns that would cause duplicates during merge
        metadata_cols = ['feature_id', 'created_at', 'sample_id', 'financial_id', 'sentiment_id']
        
        cleaned_dfs = []
        for df in features_dfs:
            # Keep only bse_code, date, and actual feature columns
            cols_to_drop = [col for col in metadata_cols if col in df.columns]
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
            cleaned_dfs.append(df)

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

        logger.info(f"Loaded {len(data)} samples with {len(merged_features.columns)-2} total features")

        # Step 5: Filter to selected features only
        missing_features = [f for f in self.selected_features if f not in data.columns]
        if missing_features:
            raise ValueError(f"Missing features in database: {missing_features}")

        X = data[self.selected_features]
        y = data['label']

        # Step 6: Check for class balance
        unique_classes = y.unique()
        if len(unique_classes) == 1:
            logger.warning(
                f"WARNING: Only single class found in labels: {unique_classes[0]}. "
                f"Model training may fail."
            )

        positive_ratio = y.sum() / len(y) * 100
        logger.info(f"Class distribution: {positive_ratio:.2f}% positive, {100-positive_ratio:.2f}% negative")

        # Store for later use
        self.X = X
        self.y = y

        return X, y

    def _load_labels(self) -> pd.DataFrame:
        """Load labels from upper_circuit_labels.db"""
        conn = sqlite3.connect(self.labels_db)
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

    def _load_features_from_db(self, db_path: str, db_type: str) -> pd.DataFrame:
        """Load features from a specific database"""
        conn = sqlite3.connect(db_path)

        # Determine table name based on db_type
        table_mapping = {
            'technical': 'technical_features',
            'financial': 'financial_features',
            'sentiment': 'sentiment_features',
            'seasonality': 'seasonality_features'
        }

        table_name = table_mapping.get(db_type, f'{db_type}_features')

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

    def split_data(self, test_size: float = 0.2, random_state: int = 42):
        """
        Split data into 80/20 stratified train/test sets (AC3.1.3)

        Args:
            test_size: Fraction for test set (default: 0.2 = 20%)
            random_state: Random seed for reproducibility (default: 42)
        """
        if self.X is None or self.y is None:
            raise ValueError("Must call load_data() before split_data()")

        logger.info(f"Splitting data: {int((1-test_size)*100)}% train, {int(test_size*100)}% test")

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X,
            self.y,
            test_size=test_size,
            random_state=random_state,
            stratify=self.y  # Stratified split to preserve class distribution
        )
        
        # Handle NaN values by filling with 0 (simple imputation)
        self.X_train = self.X_train.fillna(0)
        self.X_test = self.X_test.fillna(0)

        logger.info(
            f"Split complete: train={len(self.X_train)}, test={len(self.X_test)}, "
            f"train_positive={self.y_train.sum()}/{len(self.y_train)} "
            f"({self.y_train.sum()/len(self.y_train)*100:.1f}%), "
            f"test_positive={self.y_test.sum()}/{len(self.y_test)} "
            f"({self.y_test.sum()/len(self.y_test)*100:.1f}%)"
        )

    def train_logistic_regression(self) -> LogisticRegression:
        """
        Train Logistic Regression baseline model (AC3.1.4)

        Returns:
            Trained LogisticRegression model

        Hyperparameters:
            - max_iter: 1000 (sufficient for convergence)
            - class_weight: 'balanced' (handles class imbalance)
            - random_state: 42 (reproducibility)
        """
        if self.X_train is None or self.y_train is None:
            raise ValueError("Must call split_data() before training")

        logger.info("Training Logistic Regression model...")

        self.logistic_model = LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42
        )

        self.logistic_model.fit(self.X_train, self.y_train)

        logger.info("Logistic Regression training complete")

        # Evaluate on test set
        self.logistic_metrics = self.evaluate_model(
            self.logistic_model,
            self.X_test,
            self.y_test
        )

        logger.info(f"Logistic Regression metrics: {self.logistic_metrics}")

        return self.logistic_model

    def train_random_forest(self) -> RandomForestClassifier:
        """
        Train Random Forest baseline model (AC3.1.5)

        Returns:
            Trained RandomForestClassifier model

        Hyperparameters:
            - n_estimators: 100 (100 trees)
            - class_weight: 'balanced' (handles class imbalance)
            - random_state: 42 (reproducibility)
        """
        if self.X_train is None or self.y_train is None:
            raise ValueError("Must call split_data() before training")

        logger.info("Training Random Forest model...")

        self.random_forest_model = RandomForestClassifier(
            n_estimators=100,
            class_weight='balanced',
            random_state=42
        )

        self.random_forest_model.fit(self.X_train, self.y_train)

        logger.info("Random Forest training complete")

        # Evaluate on test set
        self.random_forest_metrics = self.evaluate_model(
            self.random_forest_model,
            self.X_test,
            self.y_test
        )

        logger.info(f"Random Forest metrics: {self.random_forest_metrics}")

        return self.random_forest_model

    def evaluate_model(self, model, X_test, y_test) -> Dict[str, float]:
        """
        Calculate comprehensive metrics for a model (AC3.1.6)

        Args:
            model: Trained sklearn model
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

    def save_results(self, output_path: str):
        """
        Save model comparison results to JSON (AC3.1.7)

        Args:
            output_path: Path to save JSON file

        Output format:
        {
            "metadata": {
                "timestamp": "2025-11-14T10:30:00",
                "train_size": 160000,
                "test_size": 40000,
                "selected_features": [...],
                "positive_ratio": 0.10
            },
            "logistic_regression": {
                "accuracy": 0.92,
                "precision": 0.45,
                "recall": 0.78,
                "f1": 0.57,
                "roc_auc": 0.88
            },
            "random_forest": {
                "accuracy": 0.94,
                "precision": 0.52,
                "recall": 0.81,
                "f1": 0.63,
                "roc_auc": 0.91
            }
        }
        """
        logger.info(f"Saving results to {output_path}...")

        if self.logistic_metrics is None or self.random_forest_metrics is None:
            raise ValueError("Must train both models before saving results")

        results = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "train_size": len(self.X_train),
                "test_size": len(self.X_test),
                "selected_features": self.selected_features,
                "positive_ratio": round(self.y_test.sum() / len(self.y_test), 4),
                "story": "3.1",
                "description": "Baseline Models: Logistic Regression vs Random Forest"
            },
            "logistic_regression": self.logistic_metrics,
            "random_forest": self.random_forest_metrics
        }

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved successfully to {output_path}")

        # Log comparison
        logger.info("\n" + "="*60)
        logger.info("MODEL COMPARISON")
        logger.info("="*60)
        logger.info(f"{'Metric':<15} {'Logistic Reg':<15} {'Random Forest':<15}")
        logger.info("-"*60)
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
            lr_val = self.logistic_metrics[metric]
            rf_val = self.random_forest_metrics[metric]
            logger.info(f"{metric:<15} {lr_val:<15.4f} {rf_val:<15.4f}")
        logger.info("="*60)
