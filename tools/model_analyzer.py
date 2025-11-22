"""
Model Analyzer Tool

Deep analysis and diagnostics for trained ML models.
Extracts feature importances, analyzes predictions, and calculates detailed metrics.

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_feature_importance(
    model: Any,
    feature_names: List[str],
    model_type: str = "xgboost"
) -> pd.DataFrame:
    """
    Extract feature importances from a trained model.
    
    Args:
        model: Trained model object
        feature_names: List of feature names
        model_type: Type of model ("xgboost", "lightgbm", "random_forest")
        
    Returns:
        DataFrame with features and importances, sorted by importance
    """
    try:
        if model_type.lower() in ["xgboost", "xgbclassifier"]:
            # XGBoost uses get_score() or feature_importances_
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'get_score'):
                importance_dict = model.get_score(importance_type='weight')
                importances = [importance_dict.get(f"f{i}", 0) for i in range(len(feature_names))]
            else:
                logger.warning("Could not extract importances from XGBoost model")
                return pd.DataFrame()
                
        elif model_type.lower() in ["lightgbm", "lgbmclassifier"]:
            importances = model.feature_importances_
            
        elif model_type.lower() in ["randomforest", "random_forest"]:
            importances = model.feature_importances_
            
        else:
            logger.warning(f"Feature importance not supported for {model_type}")
            return pd.DataFrame()
        
        # Create DataFrame
        df = pd.DataFrame({
            'feature': feature_names,
            'importance': importances
        })
        
        # Sort by importance
        df = df.sort_values('importance', ascending=False).reset_index(drop=True)
        
        # Add percentage
        df['importance_pct'] = (df['importance'] / df['importance'].sum() * 100)
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting feature importance: {e}")
        return pd.DataFrame()


def analyze_prediction_distribution(
    predictions: np.ndarray,
    probabilities: Optional[np.ndarray] = None
) -> Dict:
    """
    Analyze the distribution of model predictions.
    
    Args:
        predictions: Array of predicted classes (0 or 1)
        probabilities: Array of prediction probabilities (optional)
        
    Returns:
        Dictionary with distribution statistics
    """
    unique, counts = np.unique(predictions, return_counts=True)
    total = len(predictions)
    
    distribution = {
        "total_predictions": total,
        "class_distribution": dict(zip(unique.tolist(), counts.tolist())),
        "class_percentages": {
            int(k): (v / total * 100) for k, v in zip(unique, counts)
        }
    }
    
    if probabilities is not None:
        # Analyze probability distribution
        distribution["prob_stats"] = {
            "mean": float(probabilities.mean()),
            "std": float(probabilities.std()),
            "min": float(probabilities.min()),
            "max": float(probabilities.max()),
            "median": float(np.median(probabilities))
        }
        
        # Count high-confidence predictions
        high_conf_positive = np.sum(probabilities > 0.7)
        high_conf_negative = np.sum(probabilities < 0.3)
        
        distribution["confidence_stats"] = {
            "high_conf_positive": int(high_conf_positive),
            "high_conf_negative": int(high_conf_negative),
            "uncertain": int(total - high_conf_positive - high_conf_negative)
        }
    
    return distribution


def calculate_class_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None
) -> Dict:
    """
    Calculate detailed per-class metrics.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_prob: Prediction probabilities (optional)
        
    Returns:
        Dictionary with per-class metrics
    """
    from sklearn.metrics import (
        confusion_matrix, classification_report,
        precision_recall_fscore_support, roc_auc_score
    )
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Per-class metrics
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, zero_division=0
    )
    
    metrics = {
        "confusion_matrix": cm.tolist(),
        "class_0": {
            "precision": float(precision[0]) if len(precision) > 0 else 0.0,
            "recall": float(recall[0]) if len(recall) > 0 else 0.0,
            "f1": float(f1[0]) if len(f1) > 0 else 0.0,
            "support": int(support[0]) if len(support) > 0 else 0
        },
        "class_1": {
            "precision": float(precision[1]) if len(precision) > 1 else 0.0,
            "recall": float(recall[1]) if len(recall) > 1 else 0.0,
            "f1": float(f1[1]) if len(f1) > 1 else 0.0,
            "support": int(support[1]) if len(support) > 1 else 0
        }
    }
    
    # ROC-AUC if probabilities provided
    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except:
            metrics["roc_auc"] = None
    
    # Classification report
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    metrics["classification_report"] = report
    
    return metrics


def analyze_misclassifications(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
    sample_ids: Optional[List] = None
) -> Dict:
    """
    Analyze misclassified samples.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_prob: Prediction probabilities (optional)
        sample_ids: Sample identifiers (optional)
        
    Returns:
        Dictionary with misclassification analysis
    """
    # Find misclassified indices
    misclassified = y_true != y_pred
    n_misclassified = np.sum(misclassified)
    
    # False positives and false negatives
    false_positives = (y_true == 0) & (y_pred == 1)
    false_negatives = (y_true == 1) & (y_pred == 0)
    
    analysis = {
        "total_misclassified": int(n_misclassified),
        "misclassification_rate": float(n_misclassified / len(y_true)),
        "false_positives": int(np.sum(false_positives)),
        "false_negatives": int(np.sum(false_negatives))
    }
    
    if y_prob is not None:
        # Analyze confidence of misclassifications
        misclass_probs = y_prob[misclassified]
        if len(misclass_probs) > 0:
            analysis["misclass_confidence"] = {
                "mean": float(misclass_probs.mean()),
                "std": float(misclass_probs.std()),
                "min": float(misclass_probs.min()),
                "max": float(misclass_probs.max())
            }
    
    if sample_ids is not None:
        # List misclassified sample IDs
        misclass_ids = [sample_ids[i] for i in range(len(sample_ids)) if misclassified[i]]
        analysis["misclassified_samples"] = misclass_ids[:20]  # Limit to 20
    
    return analysis


if __name__ == "__main__":
    # Demo usage
    print("=== Model Analyzer Demo ===\n")
    
    # Simulate some predictions
    y_true = np.array([0, 0, 1, 0, 1, 0, 0, 1, 0, 0])
    y_pred = np.array([0, 0, 0, 0, 1, 0, 0, 0, 0, 0])
    y_prob = np.array([0.1, 0.2, 0.4, 0.15, 0.8, 0.05, 0.3, 0.45, 0.1, 0.2])
    
    # Analyze predictions
    dist = analyze_prediction_distribution(y_pred, y_prob)
    print("Prediction Distribution:")
    print(f"  Class 0: {dist['class_percentages'].get(0, 0):.1f}%")
    print(f"  Class 1: {dist['class_percentages'].get(1, 0):.1f}%")
    
    # Calculate metrics
    metrics = calculate_class_metrics(y_true, y_pred, y_prob)
    print(f"\nClass 1 Metrics:")
    print(f"  Precision: {metrics['class_1']['precision']:.2f}")
    print(f"  Recall: {metrics['class_1']['recall']:.2f}")
    print(f"  F1: {metrics['class_1']['f1']:.2f}")
    
    # Analyze misclassifications
    misclass = analyze_misclassifications(y_true, y_pred, y_prob)
    print(f"\nMisclassifications:")
    print(f"  Total: {misclass['total_misclassified']}")
    print(f"  False Positives: {misclass['false_positives']}")
    print(f"  False Negatives: {misclass['false_negatives']}")
