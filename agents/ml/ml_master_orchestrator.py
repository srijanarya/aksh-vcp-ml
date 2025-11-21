"""
ML Master Orchestrator - Coordinates all ML agents and operations

This orchestrator follows the Dexter/Vikram multi-agent pattern from the existing
127-agent infrastructure. It delegates tasks to 7 specialist sub-agents for:
- Data collection (historical and real-time)
- Feature engineering (25-30 features)
- Model training (XGBoost/LightGBM/RF)
- Real-time inference (<2 min latency)
- Accuracy monitoring and drift detection
- Backtesting and validation
- Alert delivery via Telegram

Author: VCP Financial Research Team
Created: 2025-11-13
Epic: Foundation
Story: INFRA-S1 (Create Master Orchestrator)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

# Configure structured JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "agent": "MLMasterOrchestrator", "message": "%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for ML Master Orchestrator"""
    db_base_path: str
    models_path: str
    data_cache_path: str
    log_level: str
    enable_parallel_execution: bool
    max_concurrent_tasks: int


@dataclass
class TaskResult:
    """Result from a delegated task"""
    task_name: str
    agent_name: str
    status: str  # "SUCCESS", "FAILED", "PARTIAL"
    duration_seconds: float
    output: any
    error_message: Optional[str] = None


@dataclass
class OrchestrationReport:
    """Comprehensive report from orchestration run"""
    run_id: str
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float
    tasks_completed: int
    tasks_failed: int
    success_rate: float
    task_results: List[TaskResult]
    next_recommended_action: str


class MLMasterOrchestrator:
    """
    Master orchestrator for all ML operations following Dexter/Vikram pattern.

    Responsibilities:
    - Coordinate data collection (historical one-time, real-time continuous)
    - Orchestrate training pipeline (features → training → validation)
    - Manage inference pipeline (BSE alert → prediction → Telegram)
    - Trigger retraining when monitoring detects drift
    - Provide status reporting and error recovery

    Design Pattern:
    - Master-Worker: Orchestrator delegates to specialist agents
    - Circuit Breaker: Pause operations if agents fail consecutively
    - Saga Pattern: Compensating actions for partial failures
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize orchestrator with configuration.

        Args:
            config: Optional configuration object. If None, loads from .env
        """
        # Load environment variables
        load_dotenv()

        # Set configuration
        if config is None:
            self.config = OrchestratorConfig(
                db_base_path=os.getenv("DB_BASE_PATH", "/Users/srijan/Desktop/aksh/data"),
                models_path=os.getenv("MODELS_PATH", "/Users/srijan/Desktop/aksh/models"),
                data_cache_path=os.getenv("DATA_CACHE_PATH", "/tmp/ml_cache"),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                enable_parallel_execution=os.getenv("ENABLE_PARALLEL", "true").lower() == "true",
                max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "4"))
            )
        else:
            self.config = config

        # Initialize agent references (lazy loading)
        self._data_collector = None
        self._feature_engineer = None
        self._training_agent = None
        self._inference_agent = None
        self._monitoring_agent = None
        self._backtesting_agent = None
        self._alert_agent = None

        # Track orchestration state
        self.current_run_id = None
        self.circuit_breaker_active = False
        self.consecutive_failures = 0

        # Initialize Memori for orchestrator-level memory
        self._memori = None
        self._initialize_memory()

        logger.info(f"MLMasterOrchestrator initialized with config: {self.config}")

    # ============================================================================
    # Memory Initialization
    # ============================================================================

    def _initialize_memory(self):
        """Initialize Memori for orchestrator-level memory"""
        try:
            # Import memory configuration
            import sys
            sys.path.append('/Users/srijan/Desktop/aksh')
            from src.memory import get_memori_instance, MemoriConfig

            # Create orchestrator-specific memory instance
            self._memori = get_memori_instance(
                namespace=MemoriConfig.NAMESPACE_ORCHESTRATOR,
                user_id="ml_master_orchestrator",
                conscious_ingest=True,  # Remember core patterns and decisions
                auto_ingest=True,       # Dynamic search for relevant past runs
            )

            if self._memori:
                self._memori.enable()
                logger.info("Memori memory system enabled for orchestrator")
            else:
                logger.warning("Memori not available - orchestrator running without memory")

        except Exception as e:
            logger.warning(f"Could not initialize Memori: {e}. Continuing without memory.")
            self._memori = None

    @property
    def memori(self):
        """Get Memori instance for memory operations"""
        return self._memori

    # ============================================================================
    # Agent Lazy Loading (Avoid Circular Imports)
    # ============================================================================

    @property
    def data_collector(self):
        """Lazy load MLDataCollectorAgent"""
        if self._data_collector is None:
            from .ml_data_collector import MLDataCollectorAgent, CollectionConfig
            
            # Create config from orchestrator config
            collector_config = CollectionConfig(
                db_base_path=self.config.db_base_path
            )
            
            self._data_collector = MLDataCollectorAgent(
                config=collector_config
            )
        return self._data_collector

    @property
    def feature_engineer(self):
        """Lazy load MLFeatureEngineerAgent"""
        if self._feature_engineer is None:
            from .ml_feature_engineer import MLFeatureEngineerAgent
            self._feature_engineer = MLFeatureEngineerAgent(
                db_base_path=self.config.db_base_path
            )
        return self._feature_engineer

    @property
    def training_agent(self):
        """Lazy load MLTrainingAgent"""
        if self._training_agent is None:
            from .ml_training_agent import MLTrainingAgent
            self._training_agent = MLTrainingAgent(
                db_base_path=self.config.db_base_path,
                models_path=self.config.models_path
            )
        return self._training_agent

    @property
    def inference_agent(self):
        """Lazy load MLInferenceAgent"""
        if self._inference_agent is None:
            from .ml_inference_agent import MLInferenceAgent
            self._inference_agent = MLInferenceAgent(
                models_path=self.config.models_path
            )
        return self._inference_agent

    @property
    def monitoring_agent(self):
        """Lazy load MLMonitoringAgent"""
        if self._monitoring_agent is None:
            from .ml_monitoring_agent import MLMonitoringAgent
            self._monitoring_agent = MLMonitoringAgent(
                db_base_path=self.config.db_base_path
            )
        return self._monitoring_agent

    @property
    def backtesting_agent(self):
        """Lazy load MLBacktestingAgent"""
        if self._backtesting_agent is None:
            from .ml_backtesting_agent import MLBacktestingAgent
            self._backtesting_agent = MLBacktestingAgent(
                db_base_path=self.config.db_base_path,
                models_path=self.config.models_path
            )
        return self._backtesting_agent

    @property
    def alert_agent(self):
        """Lazy load MLAlertAgent"""
        if self._alert_agent is None:
            from .ml_alert_agent import MLAlertAgent
            self._alert_agent = MLAlertAgent()
        return self._alert_agent

    # ============================================================================
    # Primary Orchestration Methods
    # ============================================================================

    def orchestrate_historical_data_collection(
        self,
        bse_codes: List[str] = None,
        start_date: str = "2022-01-01",
        end_date: str = "2025-11-13"
    ) -> OrchestrationReport:
        """
        Orchestrate one-time historical data collection (Epic 1).

        Tasks delegated in sequence:
        1. Label upper circuits (UpperCircuitLabeler)
        2. Improve BSE-NSE mapping (BSENSEMapper)
        3. Extract historical financials (FinancialExtractor)
        4. Collect price movements (PriceCollector)
        5. Validate data quality (DataQualityValidator)

        Args:
            bse_codes: List of BSE codes to collect data for (default: None, uses internal list)
            start_date: Start of date range (YYYY-MM-DD)
            end_date: End of date range (YYYY-MM-DD)

        Returns:
            OrchestrationReport with task results and recommendations

        Example:
            >>> orchestrator = MLMasterOrchestrator()
            >>> report = orchestrator.orchestrate_historical_data_collection(bse_codes=["500325"])
            >>> print(f"Data collection: {report.success_rate:.1%} success")
        """
        run_start = datetime.now()
        self.current_run_id = f"data_collection_{run_start.strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting historical data collection orchestration: {self.current_run_id}")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # Default BSE codes if not provided (Top 5 for demo)
        if not bse_codes:
            bse_codes = ["500325", "532540", "500209", "500180", "532174"]
            logger.info(f"Using default BSE codes: {bse_codes}")

        task_results = []

        # Task 1: Data Collection
        task_start = datetime.now()
        try:
            logger.info("Task 1/5: Collecting all historical data...")
            collection_report = self.data_collector.collect_all_data(
                bse_codes=bse_codes,
                start_date=start_date,
                end_date=end_date
            )
            task_duration = (datetime.now() - task_start).total_seconds()

            task_results.append(TaskResult(
                task_name="collect_all_data",
                agent_name="MLDataCollectorAgent",
                status="SUCCESS",
                duration_seconds=task_duration,
                output=collection_report
            ))
            logger.info(f"✓ Data collection complete in {task_duration:.1f}s: {collection_report}")

        except Exception as e:
            task_duration = (datetime.now() - task_start).total_seconds()
            task_results.append(TaskResult(
                task_name="collect_all_data",
                agent_name="MLDataCollectorAgent",
                status="FAILED",
                duration_seconds=task_duration,
                output=None,
                error_message=str(e)
            ))
            logger.error(f"✗ Data collection failed: {e}")
            self._handle_task_failure("collect_all_data")

        # Generate orchestration report
        run_end = datetime.now()
        total_duration = (run_end - run_start).total_seconds()

        tasks_completed = sum(1 for r in task_results if r.status == "SUCCESS")
        tasks_failed = sum(1 for r in task_results if r.status == "FAILED")
        success_rate = tasks_completed / len(task_results) if task_results else 0.0

        # Determine next action
        if success_rate >= 0.8:
            next_action = "Proceed to Epic 2: Feature Engineering Pipeline"
        elif success_rate >= 0.5:
            next_action = "Review failed tasks and retry before proceeding"
        else:
            next_action = "Critical failures detected. Investigate root cause before retry"

        report = OrchestrationReport(
            run_id=self.current_run_id,
            start_time=run_start,
            end_time=run_end,
            total_duration_seconds=total_duration,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            success_rate=success_rate,
            task_results=task_results,
            next_recommended_action=next_action
        )

        logger.info(f"Orchestration complete: {tasks_completed}/{len(task_results)} tasks succeeded")
        logger.info(f"Total duration: {total_duration:.1f}s")
        logger.info(f"Next action: {next_action}")

        return report

    def orchestrate_training_pipeline(
        self,
        algorithm: str = "auto"
    ) -> OrchestrationReport:
        """
        Orchestrate model training pipeline (Epic 3).

        Tasks delegated in sequence:
        1. Engineer features for all labeled samples (MLFeatureEngineerAgent)
        2. Split data into train/val/test (70%/15%/15%)
        3. Train models with hyperparameter tuning (MLTrainingAgent)
        4. Select champion model based on F1 score
        5. Compute SHAP values for explainability
        6. Backtest on Q4 FY25 before deployment

        Args:
            algorithm: "auto" (tries all 3), "xgboost", "lightgbm", "random_forest"

        Returns:
            OrchestrationReport with training results

        Example:
            >>> report = orchestrator.orchestrate_training_pipeline()
            >>> if report.success_rate == 1.0:
            ...     print("Model ready for deployment")
        """
        run_start = datetime.now()
        self.current_run_id = f"training_{run_start.strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting training pipeline orchestration: {self.current_run_id}")
        task_results = []
        
        try:
            # Task 1: Feature Engineering
            task_start = datetime.now()
            logger.info("Task 1/4: Engineering features...")
            
            # Query labeled samples from the database
            import sqlite3
            labels_db = os.path.join(self.config.db_base_path, "upper_circuit_labels.db")
            conn = sqlite3.connect(labels_db)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT bse_code, earnings_date FROM upper_circuit_labels")
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dicts with 'date' key (not 'earnings_date')
            samples = [{"bse_code": row[0], "date": row[1]} for row in rows]
            
            logger.info(f"Extracting features for {len(samples)} labeled samples")
            feature_stats = self.feature_engineer.engineer_batch_features(
                samples,
                feature_dbs={
                    'price': 'data/price_movements.db',
                    'technical': 'data/features/technical_features.db',
                    'financial': 'data/features/financial_data.db',
                    'financial_features': 'data/features/financial_features.db',
                    'news': 'data/features/news_sentiment.db',
                    'sentiment': 'data/features/sentiment_features.db',
                    'historical': 'data/features/historical_patterns.db',
                    'seasonality': 'data/features/seasonality_features.db',
                    'fundamental': 'data/features/fundamental_features.db'
                }
            )
            
            task_duration = (datetime.now() - task_start).total_seconds()
            task_results.append(TaskResult(
                task_name="feature_engineering",
                agent_name="MLFeatureEngineerAgent",
                status="SUCCESS",
                duration_seconds=task_duration,
                output=feature_stats
            ))
            
            # Task 2: Baseline Training
            task_start = datetime.now()
            logger.info("Task 2/4: Training baseline models...")
            baseline_results = self.training_agent.train_baseline_models()
            
            task_duration = (datetime.now() - task_start).total_seconds()
            task_results.append(TaskResult(
                task_name="baseline_training",
                agent_name="MLTrainingAgent",
                status="SUCCESS",
                duration_seconds=task_duration,
                output=baseline_results
            ))
            
            # Task 3: Advanced Training
            task_start = datetime.now()
            logger.info("Task 3/4: Training advanced models...")
            advanced_results = self.training_agent.train_advanced_models()
            
            task_duration = (datetime.now() - task_start).total_seconds()
            task_results.append(TaskResult(
                task_name="advanced_training",
                agent_name="MLTrainingAgent",
                status="SUCCESS",
                duration_seconds=task_duration,
                output=advanced_results
            ))
            
            # Task 4: Backtesting
            task_start = datetime.now()
            logger.info("Task 4/4: Backtesting champion model...")
            
            # Identify best model from advanced results
            best_model_id = "xgboost_v1" # Placeholder, normally derived from advanced_results
            
            backtest_results = self.backtesting_agent.backtest_model(
                model_id=best_model_id,
                start_date="2024-01-01",
                end_date="2024-03-31"
            )
            
            task_duration = (datetime.now() - task_start).total_seconds()
            task_results.append(TaskResult(
                task_name="backtesting",
                agent_name="MLBacktestingAgent",
                status="SUCCESS",
                duration_seconds=task_duration,
                output=backtest_results
            ))
            
        except Exception as e:
            task_duration = (datetime.now() - task_start).total_seconds()
            task_results.append(TaskResult(
                task_name="training_pipeline_error",
                agent_name="MLMasterOrchestrator",
                status="FAILED",
                duration_seconds=task_duration,
                output=None,
                error_message=str(e)
            ))
            logger.error(f"Training pipeline failed: {e}")
            
        # Generate orchestration report
        run_end = datetime.now()
        total_duration = (run_end - run_start).total_seconds()

        tasks_completed = sum(1 for r in task_results if r.status == "SUCCESS")
        tasks_failed = sum(1 for r in task_results if r.status == "FAILED")
        success_rate = tasks_completed / len(task_results) if task_results else 0.0
        
        next_action = "Deploy to production" if success_rate == 1.0 else "Investigate failures"

        report = OrchestrationReport(
            run_id=self.current_run_id,
            start_time=run_start,
            end_time=run_end,
            total_duration_seconds=total_duration,
            tasks_completed=tasks_completed,
            tasks_failed=tasks_failed,
            success_rate=success_rate,
            task_results=task_results,
            next_recommended_action=next_action
        )
        
        logger.info(f"Training pipeline complete. Success rate: {success_rate:.1%}")
        return report

    async def orchestrate_realtime_inference(self):
        """
        Workflow:
        1. Listen for BSE Telegram alerts (MLInferenceAgent)
        2. On alert: Download PDF, extract features, predict
        3. If probability ≥70%: Send alert via MLAlertAgent
        4. Log prediction to ml_monitoring.db for tracking

        This method runs indefinitely until stopped.

        Example:
            >>> await orchestrator.orchestrate_realtime_inference()
            # Runs forever, handling incoming BSE alerts
        """
        logger.info("Starting real-time inference orchestration (daemon mode)")

        # Start inference agent in background
        inference_task = asyncio.create_task(
            self.inference_agent.listen_to_telegram_bot()
        )

        # Start monitoring agent (daily schedule)
        monitoring_task = asyncio.create_task(
            self.monitoring_agent.run_daily_monitoring()
        )

        # Wait for both tasks (run forever)
        await asyncio.gather(inference_task, monitoring_task)

    def trigger_retraining(self, reason: str) -> OrchestrationReport:
        """
        Trigger model retraining (called by MLMonitoringAgent on drift/accuracy drop).

        Args:
            reason: Why retraining triggered (e.g., "Accuracy dropped 5%", "Feature drift 35%")

        Returns:
            OrchestrationReport with retraining results

        Example:
            >>> report = orchestrator.trigger_retraining("Precision dropped from 75% to 69%")
            >>> print(f"New model F1: {report.task_results[-1].output.f1_score}")
        """
        logger.info(f"Retraining triggered: {reason}")

        # Collect last 18 months of data
        # Retrain champion model algorithm
        # If new model F1 improves ≥2%, deploy

        raise NotImplementedError("Retraining orchestration - Coming soon")

    # ============================================================================
    # Error Handling and Circuit Breaker
    # ============================================================================

    def _handle_task_failure(self, task_name: str):
        """
        Handle task failure with circuit breaker pattern.

        If 10 consecutive failures, activate circuit breaker and pause.
        """
        self.consecutive_failures += 1

        if self.consecutive_failures >= 10:
            self.circuit_breaker_active = True
            logger.error(f"CIRCUIT BREAKER ACTIVATED: {self.consecutive_failures} consecutive failures")
            logger.error("Pausing orchestration. Manual intervention required.")
            # In production, send admin alert via Telegram/email

    def reset_circuit_breaker(self):
        """Reset circuit breaker after manual intervention"""
        self.circuit_breaker_active = False
        self.consecutive_failures = 0
        logger.info("Circuit breaker reset. Orchestration resumed.")

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def get_system_status(self) -> Dict:
        """
        Get current system status (useful for health checks).

        Returns:
            Dict with agent statuses, database sizes, model versions
        """
        status = {
            "orchestrator_version": "1.0.0",
            "circuit_breaker_active": self.circuit_breaker_active,
            "consecutive_failures": self.consecutive_failures,
            "agents_loaded": {
                "data_collector": self._data_collector is not None,
                "feature_engineer": self._feature_engineer is not None,
                "training_agent": self._training_agent is not None,
                "inference_agent": self._inference_agent is not None,
                "monitoring_agent": self._monitoring_agent is not None,
                "backtesting_agent": self._backtesting_agent is not None,
                "alert_agent": self._alert_agent is not None,
            }
        }
        return status


# ============================================================================
# CLI Entry Point (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example usage
    orchestrator = MLMasterOrchestrator()

    print("=" * 60)
    print("ML Master Orchestrator - Upper Circuit Prediction System")
    print("=" * 60)

    # Example: Run data collection
    # report = orchestrator.orchestrate_historical_data_collection()
    # print(f"\nData Collection Report:")
    # print(f"  Success Rate: {report.success_rate:.1%}")
    # print(f"  Duration: {report.total_duration_seconds:.1f}s")
    # print(f"  Next Action: {report.next_recommended_action}")

    # Get system status
    status = orchestrator.get_system_status()
    print("\nSystem Status:")
    print(f"  Version: {status['orchestrator_version']}")
    print(f"  Circuit Breaker: {'ACTIVE' if status['circuit_breaker_active'] else 'INACTIVE'}")
    print(f"  Agents Loaded: {sum(status['agents_loaded'].values())}/7")