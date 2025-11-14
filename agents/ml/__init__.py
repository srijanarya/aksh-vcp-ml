"""
ML Agents Package for Upper Circuit Prediction System

This package contains 8 specialized ML agents:
- MLMasterOrchestrator: Coordinates all ML operations
- MLDataCollectorAgent: Historical data collection
- MLFeatureEngineerAgent: 25-30 feature extraction
- MLTrainingAgent: XGBoost/LightGBM/RF training
- MLInferenceAgent: Real-time predictions
- MLMonitoringAgent: Accuracy tracking and drift detection
- MLBacktestingAgent: Historical validation
- MLAlertAgent: Telegram alert sender

Author: VCP Financial Research Team
Version: 1.0.0
"""

from .ml_master_orchestrator import MLMasterOrchestrator
from .ml_data_collector import MLDataCollectorAgent

# Future agents (will be implemented in Stories 1.2-1.6 and Epic 2-5)
# from .ml_feature_engineer import MLFeatureEngineerAgent
# from .ml_training_agent import MLTrainingAgent
# from .ml_inference_agent import MLInferenceAgent
# from .ml_monitoring_agent import MLMonitoringAgent
# from .ml_backtesting_agent import MLBacktestingAgent
# from .ml_alert_agent import MLAlertAgent

__all__ = [
    "MLMasterOrchestrator",
    "MLDataCollectorAgent",
    # Future exports
    # "MLFeatureEngineerAgent",
    # "MLTrainingAgent",
    # "MLInferenceAgent",
    # "MLMonitoringAgent",
    # "MLBacktestingAgent",
    # "MLAlertAgent",
]

__version__ = "1.0.0"