"""
Run Training Pipeline

This script executes the full model training pipeline using the MLMasterOrchestrator.
It orchestrates:
1. Feature Engineering
2. Baseline Model Training
3. Advanced Model Training (XGBoost, LightGBM, etc.)
4. Model Selection

Usage:
    python run_training_pipeline.py
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.ml.ml_master_orchestrator import MLMasterOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing ML Master Orchestrator...")
    orchestrator = MLMasterOrchestrator()
    
    logger.info("Starting training pipeline...")
    
    try:
        report = orchestrator.orchestrate_training_pipeline(algorithm="auto")
        
        print("\n" + "="*50)
        print("TRAINING PIPELINE REPORT")
        print("="*50)
        print(f"Run ID: {report.run_id}")
        print(f"Success Rate: {report.success_rate:.1%}")
        print(f"Tasks Completed: {report.tasks_completed}")
        print(f"Duration: {report.total_duration_seconds:.1f}s")
        print("-" * 50)
        
        for task in report.task_results:
            status_icon = "✅" if task.status == "SUCCESS" else "❌"
            print(f"{status_icon} {task.task_name}: {task.status}")
            if task.output:
                # Print key metrics if available
                if "metrics" in task.output:
                    print(f"   Metrics: {task.output['metrics']}")
                elif "best_model" in task.output:
                    print(f"   Best Model: {task.output['best_model']}")
                    
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
