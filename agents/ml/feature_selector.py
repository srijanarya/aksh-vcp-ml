"""
Feature Selector - Story 2.5

Reduces 42 features to 20-30 most important features using correlation analysis
and feature importance metrics.

Author: VCP Financial Research Team
Date: 2025-11-13
Story: 2.5
Epic: 2 (Feature Engineering)
"""

import sqlite3
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureSelector:
    """
    Selects optimal feature subset from all extracted features.

    Reduces 42 features to 20-30 using:
    1. Correlation analysis (remove highly correlated features)
    2. Feature importance (variance and target correlation)
    3. Domain knowledge (keep critical features)
    """

    def __init__(
        self,
        technical_db_path: str,
        financial_db_path: str,
        sentiment_db_path: str,
        seasonality_db_path: str,
        labels_db_path: str
    ):
        self.technical_db_path = technical_db_path
        self.financial_db_path = financial_db_path
        self.sentiment_db_path = sentiment_db_path
        self.seasonality_db_path = seasonality_db_path
        self.labels_db_path = labels_db_path

        logger.info("FeatureSelector initialized")

    def combine_features(self, limit: int = None) -> pd.DataFrame:
        """
        Combine all features from 4 databases into single DataFrame

        Args:
            limit: Optional limit on number of samples (for testing)

        Returns:
            DataFrame with all 42 features + upper_circuit label
        """
        logger.info("Combining features from all databases...")

        # Load labels first to get sample keys
        conn = sqlite3.connect(self.labels_db_path)
        query = "SELECT bse_code, date, upper_circuit FROM upper_circuit_labels"
        if limit:
            query += f" LIMIT {limit}"
        labels_df = pd.read_sql_query(query, conn)
        conn.close()

        logger.info(f"Loaded {len(labels_df)} labeled samples")

        # Load all feature sets
        dfs = {'labels': labels_df}

        for name, db_path, table_name in [
            ('technical', self.technical_db_path, 'technical_features'),
            ('financial', self.financial_db_path, 'financial_features'),
            ('sentiment', self.sentiment_db_path, 'sentiment_features'),
            ('seasonality', self.seasonality_db_path, 'seasonality_features')
        ]:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
            dfs[name] = df
            logger.info(f"Loaded {name} features: {len(df)} rows, {len(df.columns)} columns")

        # Merge all on (bse_code, date)
        combined = dfs['labels']
        for name in ['technical', 'financial', 'sentiment', 'seasonality']:
            combined = combined.merge(
                dfs[name],
                on=['bse_code', 'date'],
                how='left'
            )

        # Drop ID and timestamp columns
        drop_cols = [col for col in combined.columns if 'id' in col.lower() or 'created_at' in col.lower()]
        combined = combined.drop(columns=drop_cols, errors='ignore')

        logger.info(f"Combined dataset: {len(combined)} rows, {len(combined.columns)} columns")

        return combined

    def remove_correlated_features(
        self,
        df: pd.DataFrame,
        threshold: float = 0.85
    ) -> Tuple[List[str], List[Dict]]:
        """
        Remove highly correlated features

        Args:
            df: DataFrame with all features
            threshold: Correlation threshold (default 0.85)

        Returns:
            Tuple of (features_to_keep, correlation_pairs)
        """
        logger.info(f"Analyzing correlations (threshold={threshold})...")

        # Get numeric features only (exclude bse_code, date, upper_circuit)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        exclude = ['upper_circuit']
        feature_cols = [col for col in numeric_cols if col not in exclude]

        # Calculate correlation matrix
        corr_matrix = df[feature_cols].corr().abs()

        # Find highly correlated pairs
        high_corr_pairs = []
        features_to_remove = set()

        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if corr_matrix.iloc[i, j] > threshold:
                    feat1 = corr_matrix.columns[i]
                    feat2 = corr_matrix.columns[j]
                    corr_val = corr_matrix.iloc[i, j]

                    # Keep feature with higher target correlation
                    if 'upper_circuit' in df.columns:
                        target_corr1 = abs(df[[feat1, 'upper_circuit']].corr().iloc[0, 1])
                        target_corr2 = abs(df[[feat2, 'upper_circuit']].corr().iloc[0, 1])

                        if target_corr1 >= target_corr2:
                            features_to_remove.add(feat2)
                            kept = feat1
                            removed = feat2
                        else:
                            features_to_remove.add(feat1)
                            kept = feat2
                            removed = feat1
                    else:
                        # No target, keep first
                        features_to_remove.add(feat2)
                        kept = feat1
                        removed = feat2

                    high_corr_pairs.append({
                        'kept': kept,
                        'removed': removed,
                        'correlation': float(corr_val)
                    })

        features_to_keep = [f for f in feature_cols if f not in features_to_remove]

        logger.info(f"Removed {len(features_to_remove)} highly correlated features")
        logger.info(f"Remaining features: {len(features_to_keep)}")

        return features_to_keep, high_corr_pairs

    def calculate_feature_importance(
        self,
        df: pd.DataFrame,
        features: List[str]
    ) -> pd.DataFrame:
        """
        Calculate feature importance metrics

        Args:
            df: DataFrame with features and target
            features: List of feature names to analyze

        Returns:
            DataFrame with importance metrics
        """
        logger.info("Calculating feature importance...")

        importance_data = []

        for feature in features:
            if feature not in df.columns:
                continue

            # Calculate metrics
            variance = df[feature].var()
            missing_rate = df[feature].isna().mean()

            # Target correlation
            target_corr = 0.0
            if 'upper_circuit' in df.columns:
                target_corr = abs(df[[feature, 'upper_circuit']].corr().iloc[0, 1])

            importance_data.append({
                'feature': feature,
                'target_corr': target_corr,
                'variance': variance,
                'missing_rate': missing_rate
            })

        importance_df = pd.DataFrame(importance_data)
        importance_df = importance_df.sort_values('target_corr', ascending=False)
        importance_df['rank'] = range(1, len(importance_df) + 1)

        return importance_df

    def select_features(
        self,
        target_count: int = 25,
        correlation_threshold: float = 0.85
    ) -> Dict:
        """
        Select final feature set

        Args:
            target_count: Target number of features (default 25)
            correlation_threshold: Correlation threshold for removal

        Returns:
            Dict with selected features and metadata
        """
        logger.info(f"Starting feature selection (target={target_count})...")

        # Step 1: Combine all features
        combined_df = self.combine_features()

        # Get initial feature count
        initial_features = [col for col in combined_df.columns
                          if col not in ['bse_code', 'date', 'upper_circuit']]

        logger.info(f"Initial features: {len(initial_features)}")

        # Step 2: Remove correlated features
        features_after_corr, corr_pairs = self.remove_correlated_features(
            combined_df,
            threshold=correlation_threshold
        )

        # Step 3: Calculate importance
        importance_df = self.calculate_feature_importance(combined_df, features_after_corr)

        # Step 4: Select top N features
        selected_features = importance_df.nlargest(target_count, 'target_corr')['feature'].tolist()

        # Prepare selection results
        results = {
            'version': '1.0',
            'selection_date': datetime.now().isoformat(),
            'total_features_before': len(initial_features),
            'total_features_after': len(selected_features),
            'selection_method': 'correlation_and_importance',
            'correlation_threshold': correlation_threshold,
            'selected_features': selected_features,
            'removed_by_correlation': [p['removed'] for p in corr_pairs],
            'correlation_pairs': corr_pairs,
            'feature_importance': importance_df.to_dict('records')
        }

        logger.info(f"Feature selection complete: {len(selected_features)} features selected")

        return results

    def save_selected_features(self, results: Dict, output_path: str):
        """Save selection results to JSON file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved selected features to {output_path}")


if __name__ == "__main__":
    # Example usage
    selector = FeatureSelector(
        technical_db_path="data/technical_features.db",
        financial_db_path="data/financial_features.db",
        sentiment_db_path="data/sentiment_features.db",
        seasonality_db_path="data/seasonality_features.db",
        labels_db_path="data/upper_circuit_labels.db"
    )

    # Select features
    results = selector.select_features(target_count=25)

    # Save results
    selector.save_selected_features(results, "data/selected_features.json")

    print(f"\n Selected {results['total_features_after']} features:")
    for i, feat in enumerate(results['selected_features'][:10], 1):
        print(f"{i}. {feat}")
