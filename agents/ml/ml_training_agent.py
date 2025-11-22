"""
MLTrainingAgent - Orchestrates model training pipeline

This agent coordinates the training of ML models using:
- Baseline models (Logistic Regression, Random Forest)
- Advanced models (XGBoost, LightGBM, Neural Networks)
- Model Registry for versioning and management

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from .baseline_trainer import BaselineTrainer
from .advanced_trainer import AdvancedTrainer
from .model_registry import ModelRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "agent": "MLTrainingAgent", "message": "%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Configuration for model training"""
    db_base_path: str
    models_path: str
    selected_features_path: str

class MLTrainingAgent:
    """
    Orchestrates model training and management.
    
    Responsibilities:
    1. Manage training data loading
    2. Coordinate model training (baseline & advanced)
    3. Register trained models
    4. Track model performance
    """

    def __init__(self, db_base_path: str, models_path: str):
        """
        Initialize MLTrainingAgent
        
        Args:
            db_base_path: Base directory for data
            models_path: Base directory for models
        """
        self.config = TrainingConfig(
            db_base_path=db_base_path,
            models_path=models_path,
            selected_features_path=os.path.join(models_path, "selected_features.json")
        )
        
        self.paths = {
            'technical': os.path.join(db_base_path, "features", "technical_features.db"),
            'financial': os.path.join(db_base_path, "features", "financial_features.db"),
            'sentiment': os.path.join(db_base_path, "features", "sentiment_features.db"),
            'seasonality': os.path.join(db_base_path, "features", "seasonality_features.db"),
            'labels': os.path.join(db_base_path, "upper_circuit_labels.db"),
            'registry': os.path.join(models_path, "registry", "registry.db")
        }
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.config.selected_features_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.paths['registry']), exist_ok=True)
        
        # Initialize registry
        self.registry = ModelRegistry(self.paths['registry'])
        
        logger.info(f"MLTrainingAgent initialized with models path: {models_path}")

    def train_baseline_models(self) -> Dict[str, Any]:
        """
        Train baseline models (Logistic Regression, Random Forest)
        
        Returns:
            Dict with training results
        """
        logger.info("Starting baseline model training...")
        
        try:
            # Load selected features
            selected_features = self._load_selected_features()
            
            trainer = BaselineTrainer(
                feature_dbs={
                    'technical': self.paths['technical'],
                    'financial': self.paths['financial'],
                    'sentiment': self.paths['sentiment'],
                    'seasonality': self.paths['seasonality']
                },
                labels_db=self.paths['labels'],
                selected_features=selected_features
            )
            
            # Execute training pipeline
            trainer.load_data()
            trainer.split_data()
            
            lr_model = trainer.train_logistic_regression()
            rf_model = trainer.train_random_forest()
            
            # Save results
            output_path = os.path.join(self.config.models_path, "baseline_results.json")
            trainer.save_results(output_path)
            
            return {
                'logistic_regression': trainer.logistic_metrics,
                'random_forest': trainer.random_forest_metrics
            }
            
        except Exception as e:
            logger.error(f"Baseline training failed: {e}")
            raise

    def train_advanced_models(self) -> Dict[str, Any]:
        """
        Train advanced models (XGBoost, LightGBM, Neural Network)
        
        Returns:
            Dict with training results
        """
        logger.info("Starting advanced model training...")
        
        try:
            trainer = AdvancedTrainer(
                technical_db_path=self.paths['technical'],
                financial_db_path=self.paths['financial'],
                sentiment_db_path=self.paths['sentiment'],
                seasonality_db_path=self.paths['seasonality'],
                selected_features_path=self.config.selected_features_path,
                labels_db_path=self.paths['labels']
            )
            
            # Train all models
            results = trainer.train_all_models()
            
            # Save results
            output_path = os.path.join(self.config.models_path, "advanced_results.json")
            trainer.save_results(results, output_path)
            
            # Register best model
            self._register_best_model(trainer, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Advanced training failed: {e}")
            raise

    def _load_selected_features(self) -> List[str]:
        """Load selected features list"""
        if not os.path.exists(self.config.selected_features_path):
            # Create default features if not exists
            default_features = [
                "rsi_14", "macd_line", "bb_percent_b", "volume_ratio",  # Technical
                "revenue_growth_yoy", "net_profit_margin", "eps_growth_yoy",  # Financial
                "day0_reaction", "volume_spike_ratio",  # Sentiment
                "is_q1", "is_q2", "is_q3", "is_q4"  # Seasonality
            ]
            with open(self.config.selected_features_path, 'w') as f:
                json.dump(default_features, f)
            return default_features
            
        with open(self.config.selected_features_path, 'r') as f:
            return json.load(f)

    def _register_best_model(self, trainer: AdvancedTrainer, results: Dict):
        """Register the best performing model"""
        # Find best model based on F1 score
        models = {
            'xgboost': (trainer.xgboost_model, results['xgboost']),
            'lightgbm': (trainer.lightgbm_model, results['lightgbm']),
            'neural_network': (trainer.neural_network_model, results['neural_network'])
        }
        
        best_name = max(models.keys(), key=lambda k: models[k][1]['f1'])
        best_model, best_metrics = models[best_name]
        
        logger.info(f"Registering best model: {best_name} (F1: {best_metrics['f1']:.4f})")
        
        self.registry.save_model(
            model=best_model,
            model_name=f"upper_circuit_predictor_{best_name}",
            model_type=best_name,
            metrics=best_metrics,
            hyperparameters={'model_type': best_name},
            description=f"Best advanced model ({best_name}) from training run"
        )
