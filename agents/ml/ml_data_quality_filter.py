"""
ML Pipeline Data Quality Filter
Ensures only high-quality, validated data is used for model training
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sqlite3
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from data_sources.data_accuracy_validator import DataAccuracyValidator
from data_sources.validation_database import ValidationDatabase
from utils.fiscal_year_utils import IndianFiscalYear, DataTimestamp


class MLDataQualityFilter:
    """
    Filters and preprocesses data for ML pipeline based on validation confidence
    """

    def __init__(self, min_confidence: float = 60.0, db_path: str = None):
        """
        Initialize the ML data quality filter

        Args:
            min_confidence: Minimum confidence score for data inclusion
            db_path: Path to validation database
        """
        self.min_confidence = min_confidence
        self.validator = DataAccuracyValidator()
        self.validation_db = ValidationDatabase(db_path or "ml_validation.db")
        self.quality_metrics = {
            'total_samples': 0,
            'filtered_samples': 0,
            'low_confidence_removed': 0,
            'outliers_removed': 0,
            'missing_imputed': 0
        }

    def filter_training_data(self, df: pd.DataFrame,
                            feature_columns: List[str],
                            target_column: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Filter training data based on quality and confidence scores

        Args:
            df: Input DataFrame with training data
            feature_columns: List of feature column names
            target_column: Target variable column name

        Returns:
            Tuple of (filtered_df, quality_report)
        """
        self.quality_metrics['total_samples'] = len(df)
        quality_report = {
            'timestamp': DataTimestamp.create_timestamp(),
            'initial_samples': len(df),
            'feature_columns': feature_columns,
            'target_column': target_column
        }

        # Step 1: Add confidence scores for financial metrics
        df = self._add_confidence_scores(df)

        # Step 2: Filter by minimum confidence
        df_filtered = self._filter_by_confidence(df)
        quality_report['after_confidence_filter'] = len(df_filtered)

        # Step 3: Detect and handle outliers
        df_filtered = self._handle_outliers(df_filtered, feature_columns)
        quality_report['after_outlier_handling'] = len(df_filtered)

        # Step 4: Handle missing values with confidence-weighted imputation
        df_filtered = self._handle_missing_values(df_filtered, feature_columns)
        quality_report['after_missing_handling'] = len(df_filtered)

        # Step 5: Validate target variable
        df_filtered = self._validate_target(df_filtered, target_column)
        quality_report['final_samples'] = len(df_filtered)

        # Step 6: Add data quality features
        df_filtered = self._add_quality_features(df_filtered)

        # Update metrics
        self.quality_metrics['filtered_samples'] = len(df_filtered)
        quality_report['quality_metrics'] = self.quality_metrics.copy()
        quality_report['removal_rate'] = 1 - (len(df_filtered) / len(df))

        # Save quality report
        self._save_quality_report(quality_report)

        return df_filtered, quality_report

    def _add_confidence_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add confidence scores for each row based on data validation

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with confidence scores added
        """
        confidence_scores = []

        for idx, row in df.iterrows():
            confidence = 100.0  # Start with full confidence

            # Check if we have validation data for this company
            if 'Symbol' in row or 'symbol' in row:
                symbol = row.get('Symbol', row.get('symbol'))

                # Get latest validation from database
                validation = self.validation_db.get_latest_validation(symbol)

                if validation:
                    # Use stored confidence
                    confidence = validation.get('confidence_score', 50.0)
                else:
                    # Calculate confidence based on data characteristics
                    confidence = self._calculate_row_confidence(row)

            confidence_scores.append(confidence)

        df['data_confidence'] = confidence_scores
        return df

    def _calculate_row_confidence(self, row: pd.Series) -> float:
        """
        Calculate confidence score for a data row

        Args:
            row: Data row

        Returns:
            Confidence score (0-100)
        """
        confidence = 60.0  # Base confidence

        # Check for suspicious values
        suspicious_fields = {
            'revenue_yoy': (-90, 500),  # Reasonable range
            'profit_yoy': (-100, 1000),
            'eps': (-100, 1000),
            'pe_ratio': (0, 100),
            'pb_ratio': (0, 50)
        }

        for field, (min_val, max_val) in suspicious_fields.items():
            if field in row and pd.notna(row[field]):
                value = row[field]
                if value < min_val or value > max_val:
                    confidence -= 10  # Reduce confidence for out-of-range values

        # Check for missing critical fields
        critical_fields = ['revenue_yoy', 'profit_yoy', 'eps']
        missing_critical = sum(1 for f in critical_fields if f in row and pd.isna(row[f]))
        confidence -= missing_critical * 15

        # Check data age if timestamp available
        if 'fetch_timestamp' in row and pd.notna(row['fetch_timestamp']):
            try:
                fetch_time = pd.to_datetime(row['fetch_timestamp'])
                age_days = (datetime.now() - fetch_time).days
                if age_days > 30:
                    confidence -= min(20, age_days - 30)  # Reduce for old data
            except:
                pass

        return max(0, min(100, confidence))

    def _filter_by_confidence(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter rows by minimum confidence threshold

        Args:
            df: DataFrame with confidence scores

        Returns:
            Filtered DataFrame
        """
        initial_count = len(df)

        if 'data_confidence' in df.columns:
            df_filtered = df[df['data_confidence'] >= self.min_confidence].copy()
            removed = initial_count - len(df_filtered)
            self.quality_metrics['low_confidence_removed'] = removed

            if removed > 0:
                print(f"Removed {removed} samples with confidence < {self.min_confidence}%")
        else:
            df_filtered = df.copy()

        return df_filtered

    def _handle_outliers(self, df: pd.DataFrame, feature_columns: List[str]) -> pd.DataFrame:
        """
        Detect and handle outliers using IQR method with confidence weighting

        Args:
            df: Input DataFrame
            feature_columns: List of feature columns to check

        Returns:
            DataFrame with outliers handled
        """
        df_clean = df.copy()
        outliers_removed = 0

        for col in feature_columns:
            if col in df_clean.columns and pd.api.types.is_numeric_dtype(df_clean[col]):
                # Calculate IQR
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1

                # Define outlier bounds (more lenient for financial data)
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR

                # Identify outliers
                outliers = (df_clean[col] < lower_bound) | (df_clean[col] > upper_bound)

                # For outliers with low confidence, remove
                if 'data_confidence' in df_clean.columns:
                    low_conf_outliers = outliers & (df_clean['data_confidence'] < 70)
                    outliers_removed += low_conf_outliers.sum()
                    df_clean = df_clean[~low_conf_outliers]

                # For outliers with high confidence, cap values
                df_clean.loc[df_clean[col] < lower_bound, col] = lower_bound
                df_clean.loc[df_clean[col] > upper_bound, col] = upper_bound

        self.quality_metrics['outliers_removed'] = outliers_removed
        if outliers_removed > 0:
            print(f"Removed {outliers_removed} outlier samples")

        return df_clean

    def _handle_missing_values(self, df: pd.DataFrame, feature_columns: List[str]) -> pd.DataFrame:
        """
        Handle missing values with confidence-weighted imputation

        Args:
            df: Input DataFrame
            feature_columns: List of feature columns

        Returns:
            DataFrame with missing values handled
        """
        df_imputed = df.copy()
        missing_count = 0

        for col in feature_columns:
            if col in df_imputed.columns:
                missing_mask = df_imputed[col].isna()
                missing_count += missing_mask.sum()

                if missing_mask.any():
                    # Use different strategies based on data type and confidence
                    if 'data_confidence' in df_imputed.columns:
                        # For high confidence rows, use median
                        high_conf_mask = df_imputed['data_confidence'] >= 80
                        if high_conf_mask.any():
                            median_val = df_imputed.loc[high_conf_mask, col].median()
                            df_imputed.loc[missing_mask & high_conf_mask, col] = median_val

                        # For low confidence rows, use more conservative imputation
                        low_conf_mask = df_imputed['data_confidence'] < 80
                        if low_conf_mask.any():
                            # Use 25th percentile for conservative estimate
                            conservative_val = df_imputed[col].quantile(0.25)
                            df_imputed.loc[missing_mask & low_conf_mask, col] = conservative_val
                    else:
                        # Simple median imputation
                        df_imputed[col].fillna(df_imputed[col].median(), inplace=True)

        self.quality_metrics['missing_imputed'] = missing_count
        if missing_count > 0:
            print(f"Imputed {missing_count} missing values")

        return df_imputed

    def _validate_target(self, df: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """
        Validate target variable for ML training

        Args:
            df: Input DataFrame
            target_column: Name of target column

        Returns:
            DataFrame with validated target
        """
        if target_column not in df.columns:
            raise ValueError(f"Target column {target_column} not found")

        df_valid = df.copy()

        # Remove rows with missing target
        initial_count = len(df_valid)
        df_valid = df_valid.dropna(subset=[target_column])
        removed = initial_count - len(df_valid)

        if removed > 0:
            print(f"Removed {removed} samples with missing target values")

        # For classification, ensure valid classes
        if df_valid[target_column].dtype == 'object' or df_valid[target_column].nunique() < 10:
            # Likely classification
            value_counts = df_valid[target_column].value_counts()

            # Remove classes with too few samples
            min_samples_per_class = 5
            valid_classes = value_counts[value_counts >= min_samples_per_class].index
            df_valid = df_valid[df_valid[target_column].isin(valid_classes)]

            if len(df_valid) < initial_count:
                print(f"Removed classes with < {min_samples_per_class} samples")

        return df_valid

    def _add_quality_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add data quality features that may help ML model

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with quality features added
        """
        df_enhanced = df.copy()

        # Add confidence buckets as categorical feature
        if 'data_confidence' in df_enhanced.columns:
            df_enhanced['confidence_bucket'] = pd.cut(
                df_enhanced['data_confidence'],
                bins=[0, 60, 80, 100],
                labels=['low', 'medium', 'high']
            )

        # Add data freshness indicator
        if 'fetch_timestamp' in df_enhanced.columns:
            df_enhanced['data_age_days'] = df_enhanced['fetch_timestamp'].apply(
                lambda x: (datetime.now() - pd.to_datetime(x)).days if pd.notna(x) else 999
            )

            df_enhanced['data_freshness'] = pd.cut(
                df_enhanced['data_age_days'],
                bins=[0, 7, 30, 90, 999],
                labels=['very_fresh', 'fresh', 'moderate', 'stale']
            )

        # Add validation flag
        df_enhanced['is_validated'] = df_enhanced.get('data_confidence', 0) >= self.min_confidence

        return df_enhanced

    def _save_quality_report(self, report: Dict):
        """Save quality report to database"""
        try:
            cursor = self.validation_db.conn.cursor()
            cursor.execute("""
                INSERT INTO data_quality_metrics
                (company_code, date, sources_available, metrics_validated,
                 avg_confidence, high_confidence_count, medium_confidence_count,
                 low_confidence_count, failed_validations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                'ML_PIPELINE',
                datetime.now().date().isoformat(),
                report.get('initial_samples', 0),
                report.get('final_samples', 0),
                report.get('quality_metrics', {}).get('avg_confidence', 0),
                0, 0, 0, 0  # Placeholder values
            ))
            self.validation_db.conn.commit()
        except Exception as e:
            print(f"Error saving quality report: {e}")

    def prepare_features_with_validation(self, df: pd.DataFrame,
                                        feature_columns: List[str]) -> Tuple[np.ndarray, List[str], Dict]:
        """
        Prepare features for ML with validation and quality checks

        Args:
            df: Input DataFrame
            feature_columns: List of feature columns

        Returns:
            Tuple of (feature_matrix, feature_names, validation_report)
        """
        # Filter data
        df_filtered, quality_report = self.filter_training_data(
            df, feature_columns, feature_columns[0]  # Dummy target
        )

        # Select features
        available_features = [col for col in feature_columns if col in df_filtered.columns]
        X = df_filtered[available_features].values

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        validation_report = {
            'features_used': available_features,
            'samples': len(X_scaled),
            'quality_report': quality_report,
            'scaling_params': {
                'mean': scaler.mean_.tolist(),
                'std': scaler.scale_.tolist()
            }
        }

        return X_scaled, available_features, validation_report

    def validate_prediction_data(self, df: pd.DataFrame,
                                required_features: List[str]) -> Tuple[pd.DataFrame, Dict]:
        """
        Validate data before making predictions

        Args:
            df: Input DataFrame for prediction
            required_features: List of required feature columns

        Returns:
            Tuple of (validated_df, validation_report)
        """
        validation_report = {
            'timestamp': DataTimestamp.create_timestamp(),
            'input_samples': len(df),
            'missing_features': [],
            'validation_issues': []
        }

        # Check for missing features
        missing = [f for f in required_features if f not in df.columns]
        if missing:
            validation_report['missing_features'] = missing
            validation_report['validation_issues'].append(f"Missing features: {missing}")

        # Add confidence scores
        df_validated = self._add_confidence_scores(df)

        # Flag low confidence predictions
        if 'data_confidence' in df_validated.columns:
            low_conf_mask = df_validated['data_confidence'] < self.min_confidence
            if low_conf_mask.any():
                validation_report['validation_issues'].append(
                    f"{low_conf_mask.sum()} samples have confidence < {self.min_confidence}%"
                )
                df_validated['prediction_reliability'] = df_validated['data_confidence'].apply(
                    lambda x: 'high' if x >= 80 else 'medium' if x >= 60 else 'low'
                )

        validation_report['output_samples'] = len(df_validated)
        validation_report['avg_confidence'] = df_validated.get('data_confidence', pd.Series([50])).mean()

        return df_validated, validation_report

    def get_feature_quality_scores(self, df: pd.DataFrame,
                                  feature_columns: List[str]) -> Dict[str, float]:
        """
        Calculate quality scores for each feature

        Args:
            df: Input DataFrame
            feature_columns: List of feature columns

        Returns:
            Dictionary of feature quality scores
        """
        feature_scores = {}

        for feature in feature_columns:
            if feature not in df.columns:
                feature_scores[feature] = 0.0
                continue

            score = 100.0

            # Penalize for missing values
            missing_pct = df[feature].isna().mean() * 100
            score -= min(30, missing_pct)  # Max 30 point penalty

            # Penalize for low variance (uninformative)
            if pd.api.types.is_numeric_dtype(df[feature]):
                if df[feature].std() < 0.01:
                    score -= 20

            # Check correlation with confidence if available
            if 'data_confidence' in df.columns:
                try:
                    corr = df[feature].corr(df['data_confidence'])
                    if abs(corr) < 0.1:  # Low correlation with confidence
                        score -= 10
                except:
                    pass

            feature_scores[feature] = max(0, score)

        return feature_scores

    def close(self):
        """Clean up resources"""
        self.validation_db.close()


# Test the ML data quality filter
if __name__ == "__main__":
    # Create sample data
    sample_data = pd.DataFrame({
        'Symbol': ['TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'ICICIBANK'],
        'revenue_yoy': [15.5, 22.3, 18.7, -790.0, 12.4],  # Note the outlier
        'profit_yoy': [22.3, 18.5, 25.6, 15.2, None],  # Missing value
        'eps': [45.2, 78.3, 38.5, 52.1, 41.7],
        'pe_ratio': [28.5, 24.3, 22.1, 19.8, 26.4],
        'volume_ratio': [1.2, 1.5, 0.9, 1.8, 1.1],
        'target': [1, 1, 1, 0, 1]  # Binary classification target
    })

    print("Testing ML Data Quality Filter")
    print("=" * 60)

    filter = MLDataQualityFilter(min_confidence=60.0)

    # Test filtering
    print("\nOriginal data shape:", sample_data.shape)
    print("\nOriginal data:")
    print(sample_data)

    feature_cols = ['revenue_yoy', 'profit_yoy', 'eps', 'pe_ratio', 'volume_ratio']
    filtered_data, report = filter.filter_training_data(
        sample_data,
        feature_cols,
        'target'
    )

    print("\n\nFiltered data shape:", filtered_data.shape)
    print("\nQuality Report:")
    print(f"  Initial samples: {report['initial_samples']}")
    print(f"  Final samples: {report['final_samples']}")
    print(f"  Removal rate: {report['removal_rate']:.1%}")

    # Test feature quality scores
    print("\n\nFeature Quality Scores:")
    feature_scores = filter.get_feature_quality_scores(filtered_data, feature_cols)
    for feature, score in feature_scores.items():
        print(f"  {feature}: {score:.1f}/100")

    # Test feature preparation
    print("\n\nPreparing features for ML...")
    X, feature_names, val_report = filter.prepare_features_with_validation(
        sample_data, feature_cols
    )
    print(f"Feature matrix shape: {X.shape}")
    print(f"Features used: {feature_names}")

    filter.close()
    print("\n✅ ML Data Quality Filter test complete!")