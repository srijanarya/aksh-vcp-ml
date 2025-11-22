"""
Evaluate Models Script

Comprehensive evaluation of all trained models.
Shows detailed metrics, feature importances, and prediction analysis.

Usage:
    python scripts/evaluate_models.py

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ml.model_registry import ModelRegistry
from tools.model_analyzer import extract_feature_importance, calculate_class_metrics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_results(results_path):
    """Load training results from JSON file"""
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def print_model_metrics(model_name, metrics):
    """Print metrics in a formatted way"""
    print(f"\n{model_name}:")
    print(f"  Accuracy:  {metrics.get('accuracy', 0):.3f}")
    print(f"  Precision: {metrics.get('precision', 0):.3f}")
    print(f"  Recall:    {metrics.get('recall', 0):.3f}")
    print(f"  F1 Score:  {metrics.get('f1', 0):.3f}")
    print(f"  ROC-AUC:   {metrics.get('roc_auc', 0):.3f}")


def main():
    print("=" * 70)
    print("MODEL EVALUATION REPORT")
    print("=" * 70)
    print()
    
    models_path = "/Users/srijan/Desktop/aksh/models"
    
    # Load baseline results
    print("📊 BASELINE MODELS")
    print("-" * 70)
    baseline_results = load_results(os.path.join(models_path, "baseline_results.json"))
    
    if baseline_results:
        metadata = baseline_results.get('metadata', {})
        print(f"Training Date: {metadata.get('timestamp', 'Unknown')}")
        print(f"Train Size: {metadata.get('train_size', 0)}")
        print(f"Test Size: {metadata.get('test_size', 0)}")
        print(f"Positive Ratio: {metadata.get('positive_ratio', 0)*100:.1f}%")
        print(f"Features: {len(metadata.get('selected_features', []))}")
        
        # Logistic Regression
        if 'logistic_regression' in baseline_results:
            print_model_metrics("Logistic Regression", baseline_results['logistic_regression'])
        
        # Random Forest
        if 'random_forest' in baseline_results:
            print_model_metrics("Random Forest", baseline_results['random_forest'])
    else:
        print("❌ No baseline results found")
    
    print()
    
    # Load advanced results
    print("📊 ADVANCED MODELS")
    print("-" * 70)
    advanced_results = load_results(os.path.join(models_path, "advanced_results.json"))
    
    if advanced_results:
        metadata = advanced_results.get('metadata', {})
        print(f"Training Date: {metadata.get('timestamp', 'Unknown')}")
        print(f"Train Size: {metadata.get('train_size', 0)}")
        print(f"Test Size: {metadata.get('test_size', 0)}")
        print(f"Positive Ratio: {metadata.get('positive_ratio', 0)*100:.1f}%")
        
        # XGBoost
        if 'xgboost' in advanced_results:
            print_model_metrics("XGBoost", advanced_results['xgboost'])
        
        # LightGBM
        if 'lightgbm' in advanced_results:
            print_model_metrics("LightGBM", advanced_results['lightgbm'])
        
        # Neural Network
        if 'neural_network' in advanced_results:
            print_model_metrics("Neural Network", advanced_results['neural_network'])
    else:
        print("❌ No advanced results found")
    
    print()
    
    # Find best model
    print("🏆 BEST MODEL")
    print("-" * 70)
    
    all_models = {}
    if baseline_results:
        if 'logistic_regression' in baseline_results:
            all_models['Logistic Regression'] = baseline_results['logistic_regression']
        if 'random_forest' in baseline_results:
            all_models['Random Forest'] = baseline_results['random_forest']
    
    if advanced_results:
        if 'xgboost' in advanced_results:
            all_models['XGBoost'] = advanced_results['xgboost']
        if 'lightgbm' in advanced_results:
            all_models['LightGBM'] = advanced_results['lightgbm']
        if 'neural_network' in advanced_results:
            all_models['Neural Network'] = advanced_results['neural_network']
    
    if all_models:
        # Find best by F1
        best_model_name = max(all_models.keys(), key=lambda k: all_models[k].get('f1', 0))
        best_metrics = all_models[best_model_name]
        
        print(f"Best Model (by F1): {best_model_name}")
        print(f"  F1 Score: {best_metrics.get('f1', 0):.3f}")
        print(f"  ROC-AUC:  {best_metrics.get('roc_auc', 0):.3f}")
        
        # Find best by ROC-AUC
        best_roc_name = max(all_models.keys(), key=lambda k: all_models[k].get('roc_auc', 0))
        if best_roc_name != best_model_name:
            print(f"\nBest Model (by ROC-AUC): {best_roc_name}")
            print(f"  ROC-AUC: {all_models[best_roc_name].get('roc_auc', 0):.3f}")
    
    print()
    
    # Analysis
    print("📈 ANALYSIS")
    print("-" * 70)
    
    if all_models:
        # Check if any model has F1 > 0
        has_predictions = any(m.get('f1', 0) > 0 for m in all_models.values())
        
        if not has_predictions:
            print("⚠️  All models have F1 = 0 (predicting only negative class)")
            print("\nLikely causes:")
            print("  1. Severe class imbalance (too few positive samples)")
            print("  2. Insufficient training data")
            print("  3. Labels may not represent real circuits")
            print("\n💡 Recommendations:")
            print("  1. Run: python scripts/relabel_circuits.py")
            print("  2. Collect more historical data (2-3 years)")
            print("  3. Add more companies (50-100 stocks)")
        else:
            best_f1 = max(m.get('f1', 0) for m in all_models.values())
            if best_f1 < 0.3:
                print("⚠️  Models are performing poorly (F1 < 0.3)")
                print("\n💡 Recommendations:")
                print("  1. Collect more data")
                print("  2. Tune hyperparameters")
                print("  3. Add more features")
            elif best_f1 < 0.5:
                print("✅ Models are performing adequately (F1 = 0.3-0.5)")
                print("\n💡 Next steps:")
                print("  1. Test real-time inference")
                print("  2. Paper trading validation")
            else:
                print("🎉 Models are performing well (F1 > 0.5)")
                print("\n💡 Next steps:")
                print("  1. Deploy to production")
                print("  2. Set up monitoring")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
