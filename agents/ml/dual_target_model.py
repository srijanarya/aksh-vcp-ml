#!/usr/bin/env python3
"""
DUAL-TARGET ML MODEL

This model predicts both:
1. Upper Circuit Events (technical/momentum driven)
2. Blockbuster Quarters (fundamental growth driven)

The model uses all 6 feature domains including the new blockbuster features.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    f1_score
)
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
import joblib
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualTargetModel:
    """
    Multi-target model for predicting both circuits and blockbusters.

    This model:
    1. Loads features from all 6 domains (including blockbuster features)
    2. Trains separate models for each target
    3. Provides unified predictions for both events
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.features_dir = self.data_dir / "features"
        self.models_dir = self.data_dir / "models"
        self.models_dir.mkdir(exist_ok=True)

        # Feature databases
        self.feature_dbs = {
            'financial': self.features_dir / "financial_features.db",
            'technical': self.features_dir / "technical_features.db",
            'sentiment': self.features_dir / "sentiment_features.db",
            'seasonality': self.features_dir / "seasonality_features.db",
            'fundamental': self.features_dir / "fundamental_features.db",
            'blockbuster': self.features_dir / "blockbuster_features.db"
        }

        # Labels database
        self.labels_db = self.data_dir / "unified_ml_labels.db"

        # Model objects
        self.circuit_model = None
        self.blockbuster_model = None
        self.scaler = StandardScaler()

    def load_features(self) -> pd.DataFrame:
        """Load and merge features from all domains"""
        feature_dfs = []

        # 1. Load financial features
        if self.feature_dbs['financial'].exists():
            conn = sqlite3.connect(self.feature_dbs['financial'])
            df = pd.read_sql("""
                SELECT bse_code as symbol, date,
                       revenue_growth, profit_growth, margin_expansion,
                       eps_consistency, roce_improvement
                FROM financial_features
            """, conn)
            conn.close()
            feature_dfs.append(df)
            logger.info(f"Loaded {len(df)} financial features")

        # 2. Load technical features
        if self.feature_dbs['technical'].exists():
            conn = sqlite3.connect(self.feature_dbs['technical'])
            df = pd.read_sql("""
                SELECT bse_code as symbol, date,
                       rsi_14, macd_signal, bb_position,
                       volume_ratio, price_momentum
                FROM technical_features
            """, conn)
            conn.close()
            feature_dfs.append(df)
            logger.info(f"Loaded {len(df)} technical features")

        # 3. Load blockbuster features (NEW!)
        if self.feature_dbs['blockbuster'].exists():
            conn = sqlite3.connect(self.feature_dbs['blockbuster'])
            df = pd.read_sql("""
                SELECT symbol, date,
                       blockbuster_score,
                       revenue_yoy_growth, pat_yoy_growth,
                       revenue_qoq_growth, pat_qoq_growth,
                       momentum_score, percentile_rank,
                       consecutive_growth_quarters
                FROM blockbuster_features
            """, conn)
            conn.close()
            feature_dfs.append(df)
            logger.info(f"Loaded {len(df)} blockbuster features")

        if not feature_dfs:
            logger.error("No features found!")
            return pd.DataFrame()

        # Merge all features
        merged = feature_dfs[0]
        for df in feature_dfs[1:]:
            merged = pd.merge(
                merged, df,
                on=['symbol', 'date'],
                how='outer'
            )

        # Fill missing values
        merged = merged.fillna(0)

        logger.info(f"Total features merged: {len(merged)} records, {len(merged.columns)-2} features")
        return merged

    def load_labels(self) -> pd.DataFrame:
        """Load unified labels"""
        if not self.labels_db.exists():
            logger.error("Labels database not found!")
            return pd.DataFrame()

        conn = sqlite3.connect(self.labels_db)

        df = pd.read_sql("""
            SELECT
                symbol, date,
                hit_upper_circuit,
                is_blockbuster,
                high_impact_event,
                event_type
            FROM unified_ml_labels
        """, conn)

        conn.close()

        logger.info(f"Loaded {len(df)} labels")
        logger.info(f"Circuits: {df['hit_upper_circuit'].sum()}, Blockbusters: {df['is_blockbuster'].sum()}")

        return df

    def prepare_data(self) -> Tuple:
        """Prepare data for training"""
        # Load features and labels
        features_df = self.load_features()
        labels_df = self.load_labels()

        if features_df.empty or labels_df.empty:
            logger.error("Cannot prepare data - missing features or labels")
            return None, None, None, None

        # Merge features with labels
        data = pd.merge(
            features_df,
            labels_df,
            on=['symbol', 'date'],
            how='inner'
        )

        logger.info(f"Merged dataset: {len(data)} samples")

        # Separate features and targets
        feature_cols = [col for col in data.columns if col not in [
            'symbol', 'date', 'hit_upper_circuit', 'is_blockbuster',
            'high_impact_event', 'event_type'
        ]]

        X = data[feature_cols]
        y_circuit = data['hit_upper_circuit']
        y_blockbuster = data['is_blockbuster']

        # Handle infinite values
        X = X.replace([np.inf, -np.inf], 0)

        # Split data
        X_train, X_test, y_circuit_train, y_circuit_test, y_blockbuster_train, y_blockbuster_test = \
            train_test_split(X, y_circuit, y_blockbuster, test_size=0.2, random_state=42, stratify=y_circuit)

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        logger.info(f"Train set: {len(X_train)}, Test set: {len(X_test)}")
        logger.info(f"Feature dimensions: {X_train.shape[1]}")

        return (X_train_scaled, X_test_scaled,
                y_circuit_train, y_circuit_test,
                y_blockbuster_train, y_blockbuster_test,
                feature_cols)

    def train_circuit_model(self, X_train, y_train, X_test, y_test):
        """Train model for upper circuit prediction"""
        logger.info("Training circuit prediction model...")

        # XGBoost for circuit prediction
        self.circuit_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            objective='binary:logistic',
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42
        )

        self.circuit_model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.circuit_model.predict(X_test)
        y_prob = self.circuit_model.predict_proba(X_test)[:, 1]

        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob) if y_test.sum() > 0 else 0

        logger.info(f"Circuit Model - F1: {f1:.3f}, AUC: {auc:.3f}")
        logger.info("\nCircuit Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['No Circuit', 'Circuit']))

        return f1, auc

    def train_blockbuster_model(self, X_train, y_train, X_test, y_test):
        """Train model for blockbuster prediction"""
        logger.info("Training blockbuster prediction model...")

        # Random Forest for blockbuster prediction
        self.blockbuster_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            class_weight='balanced'  # Handle imbalanced classes
        )

        self.blockbuster_model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.blockbuster_model.predict(X_test)
        y_prob = self.blockbuster_model.predict_proba(X_test)[:, 1]

        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob) if y_test.sum() > 0 else 0

        logger.info(f"Blockbuster Model - F1: {f1:.3f}, AUC: {auc:.3f}")
        logger.info("\nBlockbuster Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Normal', 'Blockbuster']))

        return f1, auc

    def get_feature_importance(self, feature_cols):
        """Get feature importance from both models"""
        importance_data = []

        if self.circuit_model is not None:
            circuit_importance = self.circuit_model.feature_importances_
            for i, col in enumerate(feature_cols):
                importance_data.append({
                    'feature': col,
                    'model': 'circuit',
                    'importance': circuit_importance[i]
                })

        if self.blockbuster_model is not None:
            blockbuster_importance = self.blockbuster_model.feature_importances_
            for i, col in enumerate(feature_cols):
                importance_data.append({
                    'feature': col,
                    'model': 'blockbuster',
                    'importance': blockbuster_importance[i]
                })

        importance_df = pd.DataFrame(importance_data)

        # Show top features for each model
        for model in ['circuit', 'blockbuster']:
            print(f"\nTop 10 Features for {model.upper()} Model:")
            print("="*60)
            model_df = importance_df[importance_df['model'] == model].nlargest(10, 'importance')
            for _, row in model_df.iterrows():
                print(f"{row['feature']}: {row['importance']:.4f}")

        return importance_df

    def train(self):
        """Train both models"""
        # Prepare data
        data_tuple = self.prepare_data()
        if data_tuple is None:
            return

        (X_train, X_test,
         y_circuit_train, y_circuit_test,
         y_blockbuster_train, y_blockbuster_test,
         feature_cols) = data_tuple

        print("\n" + "="*80)
        print("TRAINING DUAL-TARGET MODELS")
        print("="*80)

        # Train circuit model
        circuit_f1, circuit_auc = self.train_circuit_model(
            X_train, y_circuit_train,
            X_test, y_circuit_test
        )

        # Train blockbuster model
        blockbuster_f1, blockbuster_auc = self.train_blockbuster_model(
            X_train, y_blockbuster_train,
            X_test, y_blockbuster_test
        )

        # Feature importance analysis
        self.get_feature_importance(feature_cols)

        # Save models
        self.save_models()

        # Summary
        print("\n" + "="*80)
        print("DUAL-TARGET MODEL TRAINING COMPLETE")
        print("="*80)
        print(f"Circuit Model Performance:")
        print(f"  F1 Score: {circuit_f1:.3f}")
        print(f"  AUC: {circuit_auc:.3f}")
        print(f"\nBlockbuster Model Performance:")
        print(f"  F1 Score: {blockbuster_f1:.3f}")
        print(f"  AUC: {blockbuster_auc:.3f}")
        print("\nModels saved to:", self.models_dir)
        print("="*80)

    def save_models(self):
        """Save trained models and scaler"""
        if self.circuit_model:
            joblib.dump(self.circuit_model, self.models_dir / "circuit_model.pkl")
            logger.info("Circuit model saved")

        if self.blockbuster_model:
            joblib.dump(self.blockbuster_model, self.models_dir / "blockbuster_model.pkl")
            logger.info("Blockbuster model saved")

        joblib.dump(self.scaler, self.models_dir / "feature_scaler.pkl")
        logger.info("Feature scaler saved")

    def load_models(self):
        """Load saved models"""
        circuit_path = self.models_dir / "circuit_model.pkl"
        blockbuster_path = self.models_dir / "blockbuster_model.pkl"
        scaler_path = self.models_dir / "feature_scaler.pkl"

        if circuit_path.exists():
            self.circuit_model = joblib.load(circuit_path)
            logger.info("Circuit model loaded")

        if blockbuster_path.exists():
            self.blockbuster_model = joblib.load(blockbuster_path)
            logger.info("Blockbuster model loaded")

        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)
            logger.info("Feature scaler loaded")

    def predict(self, features: pd.DataFrame) -> Dict:
        """Make predictions for both targets"""
        if self.circuit_model is None or self.blockbuster_model is None:
            self.load_models()

        # Scale features
        features_scaled = self.scaler.transform(features)

        # Get predictions
        circuit_prob = self.circuit_model.predict_proba(features_scaled)[:, 1]
        blockbuster_prob = self.blockbuster_model.predict_proba(features_scaled)[:, 1]

        # Combined score (weighted average)
        combined_score = (circuit_prob * 0.4 + blockbuster_prob * 0.6)

        return {
            'circuit_probability': circuit_prob,
            'blockbuster_probability': blockbuster_prob,
            'combined_score': combined_score,
            'high_impact': (circuit_prob > 0.5) | (blockbuster_prob > 0.5)
        }


def main():
    """Main execution"""
    model = DualTargetModel()

    # Train models
    model.train()

    # Example: Make predictions (would need actual feature data)
    logger.info("\nDual-target model training complete!")
    logger.info("The ML system can now predict both:")
    logger.info("1. Upper circuit events (technical/momentum)")
    logger.info("2. Blockbuster quarters (fundamental growth)")
    logger.info("\nThis unified approach captures both market dynamics!")


if __name__ == "__main__":
    main()