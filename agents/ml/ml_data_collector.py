"""
MLDataCollectorAgent - Orchestrates historical data collection

This agent coordinates all data collection tasks for Epic 1:
1. Label upper circuits (200K+ samples)
2. Improve BSE-NSE mapping (33.9% → 80%)
3. Extract historical financials from PDFs
4. Collect price movements from BhavCopy

Follows TDD with ≥90% test coverage.

Story: Epic 1 Story 1.1
Acceptance Criteria: 7 (see tests/unit/test_ml_data_collector.py)

Author: VCP Financial Research Team
Created: 2025-11-13
"""

import os
import sqlite3
import logging
import json
import time
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import pandas as pd

# Import tools and skills
from tools.db_utils import get_db_connection, execute_query, create_table_if_not_exists
from tools.validation_utils import validate_date_range
from skills.circuit_detector import find_circuit_hits_in_dataset

# Configure logging (AC1.1.6: Structured JSON logging)
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "agent": "MLDataCollectorAgent", "message": "%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class CollectionConfig:
    """Configuration for data collection"""
    db_base_path: str = "/Users/srijan/Desktop/aksh/data"
    start_date: str = "2022-01-01"
    end_date: str = "2025-11-13"
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    batch_size: int = 100


@dataclass
class CollectionReport:
    """Summary report for data collection (AC1.1.7)"""
    total_samples: int
    circuits_labeled: int
    bse_nse_mapping_pct: float
    financials_extracted: int
    price_days_collected: int
    success_rate: float
    duration_seconds: float
    tasks_completed: int
    tasks_total: int
    errors: List[str]


@dataclass
class TaskReport:
    """Report for individual sub-task"""
    task_name: str
    success: bool
    result: Dict
    error: Optional[str] = None
    duration_seconds: float = 0.0


class MLDataCollectorAgent:
    """
    Orchestrates historical data collection for ML training.

    This agent coordinates 4 sub-collection tasks:
    1. label_upper_circuits() - Label 200K+ training samples
    2. improve_bse_nse_mapping() - Improve BSE-NSE mapping to 80%+
    3. extract_historical_financials() - Extract financials from PDFs
    4. collect_price_movements() - Collect daily OHLCV from BhavCopy

    Follows BMAD Method with TDD, structured logging, and error handling.
    """

    def __init__(self, config: Optional[CollectionConfig] = None, status_db_path: Optional[str] = None):
        """
        Initialize MLDataCollectorAgent.

        Args:
            config: Collection configuration (default: load from .env)
            status_db_path: Path to status tracking database (default: data/ml_collection_status.db)
        """
        # AC1.1.3: Load configuration from .env
        load_dotenv()

        if config is None:
            config = CollectionConfig(
                db_base_path=os.getenv("DB_BASE_PATH", "/Users/srijan/Desktop/aksh/data"),
                start_date=os.getenv("START_DATE", "2022-01-01"),
                end_date=os.getenv("END_DATE", "2025-11-13"),
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                retry_backoff_factor=float(os.getenv("RETRY_BACKOFF_FACTOR", "2.0")),
                batch_size=int(os.getenv("BATCH_SIZE", "100"))
            )

        self.config = config

        # AC1.1.4: Initialize status tracking database
        if status_db_path is None:
            status_db_path = os.path.join(self.config.db_base_path, "ml_collection_status.db")

        self.status_db_path = status_db_path
        self._initialize_status_database()

        logger.info(f"MLDataCollectorAgent initialized with config: {asdict(self.config)}")

    def _initialize_status_database(self):
        """AC1.1.4: Create status tracking database and tables"""
        # Ensure directory exists
        Path(self.status_db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create tables
        collection_tasks_schema = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "task_name": "TEXT NOT NULL",
            "status": "TEXT NOT NULL",  # PENDING, IN_PROGRESS, SUCCESS, FAILED
            "started_at": "TEXT",
            "completed_at": "TEXT",
            "result": "TEXT",  # JSON
            "error": "TEXT"
        }

        collection_progress_schema = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "run_id": "TEXT NOT NULL",
            "timestamp": "TEXT NOT NULL",
            "task_name": "TEXT NOT NULL",
            "progress_pct": "REAL",
            "message": "TEXT"
        }

        create_table_if_not_exists(
            self.status_db_path,
            "collection_tasks",
            collection_tasks_schema,
            indexes=["task_name", "status"]
        )

        create_table_if_not_exists(
            self.status_db_path,
            "collection_progress",
            collection_progress_schema,
            indexes=["run_id", "task_name"]
        )

        logger.info(f"Status database initialized: {self.status_db_path}")

    def collect_all_data(
        self,
        bse_codes: List[str],
        start_date: str,
        end_date: str
    ) -> CollectionReport:
        """
        AC1.1.2: Orchestrate all data collection tasks in sequence.

        Args:
            bse_codes: List of BSE company codes (e.g., ["500570", "500209"])
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            CollectionReport with summary statistics

        Raises:
            ValueError: If date range is invalid
        """
        start_time = datetime.now()
        run_id = start_time.strftime("%Y%m%d_%H%M%S")

        logger.info(f"Starting data collection run {run_id}: {len(bse_codes)} companies, {start_date} to {end_date}")

        # Validate date range
        is_valid, errors = validate_date_range(start_date, end_date)
        if not is_valid:
            raise ValueError(f"Invalid date range: {errors}")

        # Handle empty BSE codes
        if not bse_codes:
            logger.warning("Empty BSE codes list - nothing to collect")
            return CollectionReport(
                total_samples=0,
                circuits_labeled=0,
                bse_nse_mapping_pct=0.0,
                financials_extracted=0,
                price_days_collected=0,
                success_rate=1.0,
                duration_seconds=0.0,
                tasks_completed=0,
                tasks_total=4,
                errors=[]
            )

        # AC1.1.2: Execute 4 sub-tasks in sequence
        task_reports: List[TaskReport] = []
        all_errors = []

        # Task 1: Label upper circuits
        task1_report = self._execute_with_retry(
            task_name="label_upper_circuits",
            task_func=lambda: self.label_upper_circuits(bse_codes, start_date, end_date),
            run_id=run_id
        )
        task_reports.append(task1_report)
        if not task1_report.success:
            all_errors.append(f"label_upper_circuits: {task1_report.error}")

        # Task 2: Improve BSE-NSE mapping (can run even if Task 1 fails partially)
        task2_report = self._execute_with_retry(
            task_name="improve_bse_nse_mapping",
            task_func=lambda: self.improve_bse_nse_mapping(bse_codes),
            run_id=run_id
        )
        task_reports.append(task2_report)
        if not task2_report.success:
            all_errors.append(f"improve_bse_nse_mapping: {task2_report.error}")

        # Task 3: Extract historical financials
        task3_report = self._execute_with_retry(
            task_name="extract_historical_financials",
            task_func=lambda: self.extract_historical_financials(bse_codes, start_date, end_date),
            run_id=run_id
        )
        task_reports.append(task3_report)
        if not task3_report.success:
            all_errors.append(f"extract_historical_financials: {task3_report.error}")

        # Task 4: Collect price movements
        task4_report = self._execute_with_retry(
            task_name="collect_price_movements",
            task_func=lambda: self.collect_price_movements(bse_codes, start_date, end_date),
            run_id=run_id
        )
        task_reports.append(task4_report)
        if not task4_report.success:
            all_errors.append(f"collect_price_movements: {task4_report.error}")

        # Calculate summary statistics
        duration = (datetime.now() - start_time).total_seconds()
        tasks_completed = sum(1 for r in task_reports if r.success)
        success_rate = tasks_completed / len(task_reports)

        report = CollectionReport(
            total_samples=task1_report.result.get("circuits_labeled", 0) if task1_report.success else 0,
            circuits_labeled=task1_report.result.get("circuits_labeled", 0) if task1_report.success else 0,
            bse_nse_mapping_pct=task2_report.result.get("mapping_pct", 0.0) if task2_report.success else 0.0,
            financials_extracted=task3_report.result.get("pdfs_extracted", 0) if task3_report.success else 0,
            price_days_collected=task4_report.result.get("days_collected", 0) if task4_report.success else 0,
            success_rate=success_rate,
            duration_seconds=duration,
            tasks_completed=tasks_completed,
            tasks_total=len(task_reports),
            errors=all_errors
        )

        logger.info(f"Data collection run {run_id} complete: {report.tasks_completed}/{report.tasks_total} tasks succeeded in {duration:.1f}s")

        return report

    def _execute_with_retry(
        self,
        task_name: str,
        task_func: callable,
        run_id: str
    ) -> TaskReport:
        """
        AC1.1.5: Execute task with retry logic (max 3 attempts, exponential backoff).

        Args:
            task_name: Name of task for logging
            task_func: Function to execute
            run_id: Current run ID for tracking

        Returns:
            TaskReport with success/failure status
        """
        start_time = datetime.now()

        # Record task start in database
        self._record_task_start(task_name, start_time)

        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Executing {task_name} (attempt {attempt + 1}/{self.config.max_retries})")

                # Execute task
                result = task_func()

                # Check if result indicates success
                if isinstance(result, dict) and result.get("success", True):
                    duration = (datetime.now() - start_time).total_seconds()

                    # Record success in database
                    self._record_task_complete(task_name, "SUCCESS", result, None, start_time, datetime.now())

                    logger.info(f"✓ {task_name} succeeded in {duration:.1f}s")

                    return TaskReport(
                        task_name=task_name,
                        success=True,
                        result=result,
                        error=None,
                        duration_seconds=duration
                    )
                else:
                    # Task returned failure status
                    error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else "Task returned failure"
                    logger.warning(f"✗ {task_name} failed (attempt {attempt + 1}): {error_msg}")

                    # Retry with exponential backoff
                    if attempt < self.config.max_retries - 1:
                        sleep_time = self.config.retry_backoff_factor ** attempt
                        logger.info(f"Retrying {task_name} in {sleep_time:.1f}s...")
                        time.sleep(sleep_time)
                        continue
                    else:
                        # Max retries exceeded
                        duration = (datetime.now() - start_time).total_seconds()
                        self._record_task_complete(task_name, "FAILED", {}, error_msg, start_time, datetime.now())

                        return TaskReport(
                            task_name=task_name,
                            success=False,
                            result={},
                            error=error_msg,
                            duration_seconds=duration
                        )

            except Exception as e:
                error_msg = str(e)
                logger.error(f"✗ {task_name} exception (attempt {attempt + 1}): {error_msg}")

                # Retry with exponential backoff
                if attempt < self.config.max_retries - 1:
                    sleep_time = self.config.retry_backoff_factor ** attempt
                    logger.info(f"Retrying {task_name} in {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    # Max retries exceeded
                    duration = (datetime.now() - start_time).total_seconds()
                    self._record_task_complete(task_name, "FAILED", {}, error_msg, start_time, datetime.now())

                    return TaskReport(
                        task_name=task_name,
                        success=False,
                        result={},
                        error=error_msg,
                        duration_seconds=duration
                    )

    def _record_task_start(self, task_name: str, start_time: datetime):
        """AC1.1.4: Record task start in status database"""
        execute_query(
            self.status_db_path,
            "INSERT INTO collection_tasks (task_name, status, started_at) VALUES (?, ?, ?)",
            params=(task_name, "IN_PROGRESS", start_time.isoformat()),
            commit=True
        )

    def _record_task_complete(
        self,
        task_name: str,
        status: str,
        result: Dict,
        error: Optional[str],
        start_time: datetime,
        end_time: datetime
    ):
        """AC1.1.4: Record task completion in status database"""
        execute_query(
            self.status_db_path,
            """
            UPDATE collection_tasks
            SET status = ?, completed_at = ?, result = ?, error = ?
            WHERE task_name = ? AND started_at = ?
            """,
            params=(status, end_time.isoformat(), json.dumps(result), error, task_name, start_time.isoformat()),
            commit=True
        )

    # ====================================================================================
    # Sub-task methods (AC1.1.2) - Will be implemented in Stories 1.2-1.5
    # ====================================================================================

    def label_upper_circuits(
        self,
        bse_codes: List[str],
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Label upper circuit hits for training data (Story 1.2).

        Args:
            bse_codes: List of BSE company codes
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dict with success status and circuits_labeled count
        """
        logger.info(f"Labeling upper circuits for {len(bse_codes)} companies from {start_date} to {end_date}")

        # TODO: Implement in Story 1.2
        # For now, return simulated success for testing
        return {
            "success": True,
            "circuits_labeled": len(bse_codes) * 10,  # Placeholder
            "date_range": f"{start_date} to {end_date}"
        }

    def improve_bse_nse_mapping(self, bse_codes: List[str]) -> Dict:
        """
        Improve BSE-NSE mapping from 33.9% to 80%+ (Story 1.3).

        Args:
            bse_codes: List of BSE company codes

        Returns:
            Dict with success status and mapping_pct
        """
        logger.info(f"Improving BSE-NSE mapping for {len(bse_codes)} companies")

        # TODO: Implement in Story 1.3
        # For now, return simulated success for testing
        return {
            "success": True,
            "mapping_pct": 82.5,  # Placeholder (target: 80%+)
            "companies_mapped": len(bse_codes)
        }

    def extract_historical_financials(
        self,
        bse_codes: List[str],
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Extract historical financials from PDFs (Story 1.4).

        Args:
            bse_codes: List of BSE company codes
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dict with success status and pdfs_extracted count
        """
        logger.info(f"Extracting financials for {len(bse_codes)} companies from {start_date} to {end_date}")

        # TODO: Implement in Story 1.4
        # For now, return simulated success for testing
        return {
            "success": True,
            "pdfs_extracted": len(bse_codes) * 12,  # ~12 quarters per company
            "companies_processed": len(bse_codes)
        }

    def collect_price_movements(
        self,
        bse_codes: List[str],
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Collect daily price movements from BhavCopy (Story 1.5).

        Args:
            bse_codes: List of BSE company codes
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dict with success status and days_collected count
        """
        logger.info(f"Collecting prices for {len(bse_codes)} companies from {start_date} to {end_date}")

        # TODO: Implement in Story 1.5
        # For now, return simulated success for testing

        # Calculate trading days (approx)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        total_days = (end_dt - start_dt).days
        trading_days = int(total_days * 0.7)  # ~70% are trading days

        return {
            "success": True,
            "days_collected": trading_days,
            "companies_processed": len(bse_codes)
        }


if __name__ == "__main__":
    # Demo: Run data collection for small sample
    print("=== MLDataCollectorAgent Demo ===\n")

    agent = MLDataCollectorAgent()

    # Collect data for 2 companies over 1 month
    report = agent.collect_all_data(
        bse_codes=["500570", "500209"],  # TCS, Infosys
        start_date="2024-10-01",
        end_date="2024-10-31"
    )

    print(f"\n📊 Collection Report:")
    print(f"  Total samples: {report.total_samples}")
    print(f"  Circuits labeled: {report.circuits_labeled}")
    print(f"  BSE-NSE mapping: {report.bse_nse_mapping_pct:.1f}%")
    print(f"  Financials extracted: {report.financials_extracted}")
    print(f"  Price days collected: {report.price_days_collected}")
    print(f"  Success rate: {report.success_rate:.1%}")
    print(f"  Duration: {report.duration_seconds:.1f}s")
    print(f"  Tasks: {report.tasks_completed}/{report.tasks_total} completed")

    if report.errors:
        print(f"\n❌ Errors:")
        for error in report.errors:
            print(f"  - {error}")


# ====================================================================================
# Story 1.2: UpperCircuitLabeler - Label training samples
# ====================================================================================

@dataclass
class UpperCircuitLabel:
    """Label for a single earnings announcement and next-day circuit (AC1.2.1)"""
    bse_code: str
    nse_symbol: Optional[str]
    earnings_date: date
    next_day_date: date
    price_change_pct: float
    hit_circuit: bool
    label: int  # 1 = upper circuit, 0 = no circuit


@dataclass
class BhavCopyRecord:
    """Parsed record from BhavCopy CSV (AC1.2.2)"""
    bse_code: str
    company_name: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    circuit_indicator: str
    prev_close: Optional[float] = None


@dataclass
class ClassDistributionReport:
    """Report on class distribution (AC1.2.6)"""
    total_samples: int
    positive_samples: int
    negative_samples: int
    positive_ratio: float
    status: str  # PASS, WARNING
    message: str


class UpperCircuitLabeler:
    """
    Labels earnings announcements with upper circuit occurrences (Story 1.2).

    This class:
    1. Fetches next-day price data from BhavCopy CSVs
    2. Labels samples as upper circuit (1) or not (0) based on dual criteria
    3. Stores labels in historical_upper_circuits.db
    4. Validates class distribution

    Follows TDD with ≥90% test coverage.
    """

    def __init__(self, db_path: str, cache_dir: str = "/tmp/bhav_copy_cache"):
        """
        Initialize UpperCircuitLabeler.

        Args:
            db_path: Path to historical_upper_circuits.db
            cache_dir: Directory to cache downloaded BhavCopy files
        """
        self.db_path = db_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # AC1.2.4: Create database table
        self._initialize_database()

        logger.info(f"UpperCircuitLabeler initialized: {db_path}")

    def _initialize_database(self):
        """AC1.2.4: Create upper_circuit_labels table"""
        schema = {
            "sample_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "bse_code": "TEXT NOT NULL",
            "nse_symbol": "TEXT",
            "earnings_date": "DATE NOT NULL",
            "next_day_date": "DATE NOT NULL",
            "price_change_pct": "REAL",
            "hit_circuit": "BOOLEAN",
            "label": "INTEGER NOT NULL CHECK(label IN (0, 1))",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }

        create_table_if_not_exists(
            self.db_path,
            "upper_circuit_labels",
            schema,
            indexes=["bse_code", "earnings_date", "label"]
        )

        # Create UNIQUE constraint manually (not supported in create_table_if_not_exists)
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_bse_earnings
                ON upper_circuit_labels(bse_code, earnings_date)
            """)
            conn.commit()

    def label_upper_circuits(
        self,
        bse_code: str,
        date_range: Tuple[str, str]
    ) -> List[UpperCircuitLabel]:
        """
        AC1.2.1: Label upper circuits for a company over a date range.

        Args:
            bse_code: BSE company code (e.g., "500570")
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format

        Returns:
            List of UpperCircuitLabel objects

        Example:
            labels = labeler.label_upper_circuits("500570", ("2024-01-01", "2024-12-31"))
            print(f"Labeled {len(labels)} earnings announcements")
        """
        start_date_str, end_date_str = date_range
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        logger.info(f"Labeling upper circuits for {bse_code} from {start_date} to {end_date}")

        # TODO: Query earnings_calendar.db for earnings dates in range
        # For now, return empty list for testing
        # This will be implemented when earnings_calendar.db is populated

        labels = []

        # Placeholder: Simulate one earnings date for testing
        earnings_date = start_date

        # AC1.2.2: Fetch next trading day
        next_day_str = self.fetch_next_trading_day(earnings_date.isoformat())

        if next_day_str is None:
            logger.warning(f"No trading day found after {earnings_date} for {bse_code}")
            return labels

        next_day = datetime.strptime(next_day_str, "%Y-%m-%d").date()

        # AC1.2.2: Download BhavCopy
        csv_path = self.download_bhav_copy(next_day_str)

        if csv_path is None:
            logger.warning(f"BhavCopy unavailable for {next_day} - skipping {bse_code}")
            return labels

        # AC1.2.2: Parse BhavCopy
        record = self.parse_bhav_copy(csv_path, bse_code)

        if record is None:
            logger.warning(f"No data for {bse_code} in BhavCopy {next_day}")
            return labels

        # AC1.2.3: Calculate price change
        if record.prev_close is None:
            # AC1.2.7: Fallback to yfinance
            record.prev_close = self.get_prev_close(bse_code, earnings_date.isoformat())

        if record.prev_close is None:
            logger.warning(f"Cannot determine prev_close for {bse_code} on {earnings_date}")
            return labels

        price_change_pct = self.calculate_price_change(record.close, record.prev_close)

        # AC1.2.3: Check circuit hit
        hit_circuit = self.check_circuit_hit(record)

        # AC1.2.3: Determine label (1 if BOTH criteria met)
        label = 1 if (price_change_pct >= 5.0 and hit_circuit) else 0

        upper_circuit_label = UpperCircuitLabel(
            bse_code=bse_code,
            nse_symbol=None,  # TODO: Get from BSE-NSE mapping
            earnings_date=earnings_date,
            next_day_date=next_day,
            price_change_pct=price_change_pct,
            hit_circuit=hit_circuit,
            label=label
        )

        labels.append(upper_circuit_label)

        logger.info(
            f"Labeled {bse_code} on {earnings_date}: "
            f"price_change={price_change_pct:.2f}%, circuit={hit_circuit}, label={label}"
        )

        return labels

    def fetch_next_trading_day(self, date_str: str, max_days: int = 5) -> Optional[str]:
        """
        AC1.2.2, AC1.2.7: Find next trading day (skip weekends/holidays).

        Args:
            date_str: Date in YYYY-MM-DD format
            max_days: Maximum days to search ahead (default: 5)

        Returns:
            Next trading day in YYYY-MM-DD format, or None if not found
        """
        current_date = datetime.strptime(date_str, "%Y-%m-%d")

        for i in range(1, max_days + 1):
            next_date = current_date + timedelta(days=i)

            # Skip weekends (Saturday=5, Sunday=6)
            if next_date.weekday() >= 5:
                continue

            # TODO: Check market holiday calendar
            # For now, assume it's a trading day if not weekend

            return next_date.strftime("%Y-%m-%d")

        logger.warning(f"No trading day found within {max_days} days of {date_str}")
        return None

    def download_bhav_copy(self, date_str: str) -> Optional[str]:
        """
        AC1.2.2: Download BhavCopy CSV for a date (with caching).

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Path to extracted CSV file, or None if download failed
        """
        # Use tools/bhav_copy_downloader.py
        from tools.bhav_copy_downloader import download_bse_bhav_copy

        try:
            csv_path = download_bse_bhav_copy(date_str, cache_dir=str(self.cache_dir))
            return str(csv_path) if csv_path else None
        except Exception as e:
            logger.error(f"Failed to download BhavCopy for {date_str}: {e}")
            return None

    def parse_bhav_copy(self, csv_path: str, bse_code: str) -> Optional[BhavCopyRecord]:
        """
        AC1.2.2: Parse BhavCopy CSV and extract data for specific BSE code.

        Args:
            csv_path: Path to BhavCopy CSV file
            bse_code: BSE code to extract (e.g., "500570")

        Returns:
            BhavCopyRecord or None if code not found
        """
        try:
            with open(csv_path, 'r') as f:
                lines = f.readlines()

            # Parse CSV (simple parsing - can use pandas for production)
            header = lines[0].strip().split(',')
            for line in lines[1:]:
                fields = line.strip().split(',')
                if len(fields) < 8:
                    continue

                row_dict = dict(zip(header, fields))

                if row_dict.get('SC_CODE', '').strip() == bse_code:
                    return BhavCopyRecord(
                        bse_code=bse_code,
                        company_name=row_dict.get('SC_NAME', ''),
                        open=float(row_dict.get('OPEN', 0)),
                        high=float(row_dict.get('HIGH', 0)),
                        low=float(row_dict.get('LOW', 0)),
                        close=float(row_dict.get('CLOSE', 0)),
                        volume=int(row_dict.get('NO_OF_SHRS', 0)),
                        circuit_indicator=row_dict.get('TDCLOINDI', '').strip(),
                        prev_close=None
                    )

            logger.warning(f"BSE code {bse_code} not found in {csv_path}")
            return None

        except Exception as e:
            logger.error(f"Error parsing BhavCopy {csv_path}: {e}")
            return None

    def calculate_price_change(self, close: float, prev_close: float) -> float:
        """
        AC1.2.3: Calculate percentage price change.

        Args:
            close: Closing price
            prev_close: Previous closing price

        Returns:
            Percentage change
        """
        if prev_close == 0:
            return 0.0

        return ((close - prev_close) / prev_close) * 100

    def check_circuit_hit(self, record: BhavCopyRecord) -> bool:
        """
        AC1.2.3: Check if circuit was hit.

        Args:
            record: BhavCopyRecord with circuit indicator

        Returns:
            True if circuit hit, False otherwise
        """
        # Check circuit indicator flag
        if record.circuit_indicator == 'C':
            return True

        # TODO: Check if close >= circuit_limit * 0.99
        # Need to know circuit limits (5%, 10%, 20% based on stock category)

        return False

    def get_prev_close(self, bse_code: str, date_str: str) -> Optional[float]:
        """
        AC1.2.7: Get previous closing price (fallback to yfinance).

        Args:
            bse_code: BSE code
            date_str: Date in YYYY-MM-DD format

        Returns:
            Previous closing price or None
        """
        # TODO: First try to get from price_movements.db
        # If not found, fallback to yfinance

        try:
            import yfinance as yf

            # Convert BSE code to yfinance ticker (BSE uses .BO suffix)
            ticker_symbol = f"{bse_code}.BO"
            ticker = yf.Ticker(ticker_symbol)

            # Fetch historical data
            hist = ticker.history(start=date_str, end=date_str)

            if not hist.empty and 'Close' in hist.columns:
                return float(hist['Close'].iloc[0])

            logger.warning(f"No yfinance data for {ticker_symbol} on {date_str}")
            return None

        except Exception as e:
            logger.error(f"yfinance fallback failed for {bse_code}: {e}")
            return None

    def store_labels(self, labels: List[UpperCircuitLabel]) -> int:
        """
        AC1.2.4: Store labels in database (bulk insert with INSERT OR REPLACE).

        Args:
            labels: List of UpperCircuitLabel objects

        Returns:
            Number of records inserted
        """
        if not labels:
            return 0

        # Prepare data for bulk insert
        data = [
            (
                label.bse_code,
                label.nse_symbol,
                label.earnings_date.isoformat(),
                label.next_day_date.isoformat(),
                label.price_change_pct,
                1 if label.hit_circuit else 0,
                label.label
            )
            for label in labels
        ]

        # Use INSERT OR REPLACE for idempotency
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT OR REPLACE INTO upper_circuit_labels
                (bse_code, nse_symbol, earnings_date, next_day_date, price_change_pct, hit_circuit, label)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()
            rows_inserted = cursor.rowcount

        logger.info(f"Stored {rows_inserted} labels in database")
        return rows_inserted

    def validate_class_distribution(self) -> ClassDistributionReport:
        """
        AC1.2.6: Validate class distribution is in 5-15% range.

        Returns:
            ClassDistributionReport with statistics
        """
        # Query database for counts
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels WHERE label = 1")
            positive = cursor.fetchone()[0]

            negative = total - positive

        if total == 0:
            return ClassDistributionReport(
                total_samples=0,
                positive_samples=0,
                negative_samples=0,
                positive_ratio=0.0,
                status="UNKNOWN",
                message="No samples in database"
            )

        positive_ratio = (positive / total) * 100

        # AC1.2.6: Check if in expected range
        if positive_ratio < 5.0:
            status = "WARNING"
            message = (
                f"Class imbalance severe: {positive_ratio:.1f}%. "
                f"Upper circuits may be under-represented. "
                f"Consider relaxing criteria (e.g., ≥3% price change)."
            )
            logger.warning(message)

        elif positive_ratio > 15.0:
            status = "WARNING"
            message = (
                f"Class imbalance low: {positive_ratio:.1f}%. "
                f"Upper circuit criteria may be too lenient. "
                f"Consider stricter criteria (e.g., ≥7% price change)."
            )
            logger.warning(message)

        else:
            status = "PASS"
            message = f"Class distribution within expected range: {positive_ratio:.1f}%"
            logger.info(message)

        return ClassDistributionReport(
            total_samples=total,
            positive_samples=positive,
            negative_samples=negative,
            positive_ratio=positive_ratio,
            status=status,
            message=message
        )


# ============================================================================
# Story 1.3: BSE-NSE Mapping Improvement
# ============================================================================

@dataclass
class MappingCandidate:
    """
    A candidate BSE→NSE mapping (AC1.3.1).

    Attributes:
        nse_symbol: NSE ticker symbol
        company_name: Company name
        isin: ISIN code
        match_method: How mapping was determined
        confidence: Confidence score 0.0-1.0
        updated_at: Timestamp of mapping
        requires_manual_review: Whether manual review needed
        status: Status (active/delisted)
        volume: Trading volume (for disambiguation)
    """
    nse_symbol: str
    company_name: Optional[str] = None
    isin: Optional[str] = None
    match_method: str = "unknown"
    confidence: float = 0.0
    updated_at: Optional[str] = None
    requires_manual_review: bool = False
    status: str = "active"
    volume: Optional[int] = None
    use_for_yfinance: bool = True


@dataclass
class MappingReport:
    """
    Summary report for BSE-NSE mapping (AC1.3.7).

    Attributes:
        total_bse_companies: Total BSE companies processed
        total_mapped: Total mappings created
        coverage_percent: Coverage percentage
        isin_matches: Count from ISIN matching
        fuzzy_matches: Count from fuzzy matching
        baseline_preserved: Count from existing baseline
        requires_manual_review: Count needing review
        conflicts_logged: Count of ISIN conflicts
        anomalies_logged: Count of name mismatches
        unmapped_count: Count of unmapped companies
    """
    total_bse_companies: int
    total_mapped: int
    coverage_percent: float
    isin_matches: int = 0
    fuzzy_matches: int = 0
    baseline_preserved: int = 0
    requires_manual_review: int = 0
    conflicts_logged: int = 0
    anomalies_logged: int = 0
    unmapped_count: int = 0


class BSENSEMapper:
    """
    BSE-NSE symbol mapper (Story 1.3).

    Improves BSE→NSE mapping from 33.9% to ≥80% using:
    1. Existing baseline (392 mappings)
    2. ISIN-based matching (~60-70% coverage)
    3. Fuzzy company name matching (~15-20% additional)

    Usage:
        mapper = BSENSEMapper(existing_mapping_path="bse_nse_mapping_current.json")
        report = mapper.run_full_mapping(output_dir="/path/to/output")
        print(f"Coverage: {report.coverage_percent:.1f}%")
    """

    def __init__(self, existing_mapping_path: Optional[str] = None):
        """
        Initialize BSENSEMapper.

        Args:
            existing_mapping_path: Path to existing baseline mapping JSON
        """
        self.existing_mapping_path = existing_mapping_path
        self._mappings: Dict[str, Dict] = {}
        self._total_bse_companies = 0
        self._conflicts: List[Dict] = []
        self._anomalies: List[Dict] = []

        # Load existing baseline if provided (AC1.3.1)
        if existing_mapping_path and os.path.exists(existing_mapping_path):
            self._load_baseline_mapping()

        logger.info(f"BSENSEMapper initialized with {len(self._mappings)} baseline mappings")

    def _load_baseline_mapping(self):
        """
        AC1.3.1: Load existing baseline mapping and convert to new format.

        Old format: {bse_code: nse_symbol}
        New format: {bse_code: {nse_symbol, company_name, isin, match_method, confidence}}
        """
        try:
            with open(self.existing_mapping_path, 'r') as f:
                baseline = json.load(f)

            # Convert to new format
            for bse_code, nse_symbol in baseline.items():
                if isinstance(nse_symbol, str):
                    # Old format - simple string
                    self._mappings[bse_code] = {
                        "nse_symbol": nse_symbol,
                        "company_name": None,
                        "isin": None,
                        "match_method": "existing_baseline",
                        "confidence": 1.0,
                        "updated_at": datetime.now().isoformat(),
                        "requires_manual_review": False,
                        "status": "active",
                        "use_for_yfinance": True
                    }
                else:
                    # Already in new format
                    self._mappings[bse_code] = nse_symbol

            logger.info(f"Loaded {len(self._mappings)} baseline mappings from {self.existing_mapping_path}")

        except Exception as e:
            logger.error(f"Error loading baseline mapping: {e}")
            self._mappings = {}

    def get_current_mappings(self) -> Dict[str, Dict]:
        """Get current mappings in new format."""
        return self._mappings

    def download_bhav_copies(self) -> Tuple[str, str]:
        """
        AC1.3.2: Download latest BSE and NSE BhavCopy files.

        Returns:
            Tuple of (bse_csv_path, nse_csv_path)
        """
        from tools.bhav_copy_downloader import download_bse_bhav_copy, download_nse_bhav_copy
        from datetime import datetime, timedelta

        # Try today, fallback to yesterday (for after-hours)
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        try:
            # Try today first
            bse_path = download_bse_bhav_copy(today.strftime("%Y-%m-%d"))
            nse_path = download_nse_bhav_copy(today.strftime("%Y-%m-%d"))

            logger.info(f"Downloaded BhavCopy files: BSE={bse_path}, NSE={nse_path}")
            return (bse_path, nse_path)

        except Exception as e:
            logger.warning(f"Failed to download today's BhavCopy: {e}, trying yesterday")

            try:
                bse_path = download_bse_bhav_copy(yesterday.strftime("%Y-%m-%d"))
                nse_path = download_nse_bhav_copy(yesterday.strftime("%Y-%m-%d"))

                logger.info(f"Downloaded yesterday's BhavCopy: BSE={bse_path}, NSE={nse_path}")
                return (bse_path, nse_path)

            except Exception as e2:
                logger.error(f"Failed to download BhavCopy files: {e2}")
                raise

    def parse_bse_bhav_copy(self, csv_path: str) -> Dict[str, Dict]:
        """
        AC1.3.2: Parse BSE BhavCopy CSV for SC_CODE, SC_NAME, ISIN_CODE.

        Args:
            csv_path: Path to BSE BhavCopy CSV

        Returns:
            Dict mapping bse_code → {company_name, isin}
        """
        import csv

        bse_data = {}

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    bse_code = row.get('SC_CODE', '').strip()
                    company_name = row.get('SC_NAME', '').strip()
                    isin = row.get('ISIN_CODE', '').strip() or row.get('SC_ISIN', '').strip()

                    if bse_code:
                        bse_data[bse_code] = {
                            "company_name": company_name,
                            "isin": isin if isin else None
                        }

            logger.info(f"Parsed {len(bse_data)} BSE companies from {csv_path}")
            self._total_bse_companies = len(bse_data)
            return bse_data

        except Exception as e:
            logger.error(f"Error parsing BSE BhavCopy {csv_path}: {e}")
            return {}

    def parse_nse_bhav_copy(self, csv_path: str) -> Dict[str, Dict]:
        """
        AC1.3.2: Parse NSE BhavCopy CSV for SYMBOL, ISIN, SERIES.
        Only include SERIES='EQ' (equity).

        Args:
            csv_path: Path to NSE BhavCopy CSV

        Returns:
            Dict mapping nse_symbol → {isin, volume, series, company_name}
        """
        import csv

        nse_data = {}

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    series = row.get('SERIES', '').strip()

                    # Only include EQ (equity) series
                    if series != 'EQ':
                        continue

                    symbol = row.get('SYMBOL', '').strip()
                    isin = row.get('ISIN', '').strip()
                    volume = int(row.get('TOTTRDQTY', 0) or 0)
                    company_name = row.get('NAME', '').strip() if 'NAME' in row else None

                    if symbol and isin:
                        nse_data[symbol] = {
                            "isin": isin,
                            "volume": volume,
                            "series": series,
                            "company_name": company_name
                        }

            logger.info(f"Parsed {len(nse_data)} NSE EQ symbols from {csv_path}")
            return nse_data

        except Exception as e:
            logger.error(f"Error parsing NSE BhavCopy {csv_path}: {e}")
            return {}

    def extract_isin_mappings(self, bse_data: Dict[str, Dict], nse_data: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        AC1.3.3: ISIN-based matching strategy.

        For each BSE code with ISIN:
        - Search NSE for matching ISIN
        - If exact match: confidence 1.0
        - If multiple NSE symbols: choose highest volume, confidence 0.95

        Args:
            bse_data: BSE company data with ISINs
            nse_data: NSE symbol data with ISINs

        Returns:
            Dict mapping bse_code → mapping candidate
        """
        # Build reverse ISIN index: isin → list of (nse_symbol, volume)
        isin_to_nse: Dict[str, List[Tuple[str, int]]] = {}

        for nse_symbol, data in nse_data.items():
            isin = data.get('isin')
            volume = data.get('volume', 0)

            if isin:
                if isin not in isin_to_nse:
                    isin_to_nse[isin] = []
                isin_to_nse[isin].append((nse_symbol, volume))

        # Match BSE codes
        isin_mappings = {}

        for bse_code, bse_info in bse_data.items():
            isin = bse_info.get('isin')

            if not isin or isin not in isin_to_nse:
                continue

            nse_candidates = isin_to_nse[isin]

            if len(nse_candidates) == 1:
                # Exact match - confidence 1.0
                nse_symbol, volume = nse_candidates[0]
                confidence = 1.0

            else:
                # Multiple NSE symbols for same ISIN - choose highest volume
                nse_candidates.sort(key=lambda x: x[1], reverse=True)
                nse_symbol, volume = nse_candidates[0]
                confidence = 0.95  # Slightly lower for ambiguity

                # Log conflict
                self._conflicts.append({
                    "bse_code": bse_code,
                    "isin": isin,
                    "nse_candidates": [(sym, vol) for sym, vol in nse_candidates],
                    "chosen": nse_symbol
                })

            # Check for name mismatch anomalies
            bse_name = bse_info.get('company_name', '')
            nse_name = nse_data[nse_symbol].get('company_name', '')

            if bse_name and nse_name:
                # Simple check: if cleaned names are very different, log anomaly
                bse_clean = self.clean_company_name(bse_name)
                nse_clean = self.clean_company_name(nse_name)

                # If first 3 chars don't match at all, might be anomaly
                if bse_clean[:3].upper() != nse_clean[:3].upper():
                    self._anomalies.append({
                        "bse_code": bse_code,
                        "isin": isin,
                        "bse_name": bse_name,
                        "nse_symbol": nse_symbol,
                        "nse_name": nse_name,
                        "reason": "name_mismatch_despite_isin"
                    })

            isin_mappings[bse_code] = {
                "nse_symbol": nse_symbol,
                "company_name": bse_info.get('company_name'),
                "isin": isin,
                "match_method": "isin_exact" if confidence == 1.0 else "isin_ambiguous",
                "confidence": confidence,
                "updated_at": datetime.now().isoformat(),
                "requires_manual_review": confidence < 1.0,
                "status": "active",
                "use_for_yfinance": True
            }

        logger.info(f"ISIN matching: {len(isin_mappings)} mappings created, {len(self._conflicts)} conflicts, {len(self._anomalies)} anomalies")
        return isin_mappings

    def clean_company_name(self, name: str) -> str:
        """
        AC1.3.4: Clean company name for fuzzy matching.

        Removes: LIMITED, LTD, PVT, punctuation
        Converts to uppercase

        Args:
            name: Raw company name

        Returns:
            Cleaned name
        """
        import re

        # Convert to uppercase
        cleaned = name.upper()

        # Remove common suffixes
        suffixes = ['LIMITED', 'LTD', 'PVT', 'PRIVATE', 'LTD.', 'PVT.', 'LIMITED.']
        for suffix in suffixes:
            cleaned = cleaned.replace(suffix, '')

        # Remove punctuation
        cleaned = re.sub(r'[^\w\s]', '', cleaned)

        # Remove extra whitespace
        cleaned = ' '.join(cleaned.split())

        return cleaned.strip()

    def fuzzy_match_names(self, unmapped_bse: Dict[str, Dict], nse_symbols: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        AC1.3.4: Fuzzy company name matching for remaining unmapped.

        Uses fuzzywuzzy token_sort_ratio:
        - Ratio ≥90: High confidence, accept
        - Ratio 80-89: Medium confidence, requires manual review
        - Ratio <80: Reject

        Args:
            unmapped_bse: BSE codes without ISIN match
            nse_symbols: All NSE symbols with company names

        Returns:
            Dict mapping bse_code → mapping candidate
        """
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            logger.warning("fuzzywuzzy not installed, skipping fuzzy matching")
            return {}

        fuzzy_mappings = {}

        for bse_code, bse_info in unmapped_bse.items():
            bse_name = bse_info.get('company_name', '')

            if not bse_name:
                continue

            bse_clean = self.clean_company_name(bse_name)

            best_match = None
            best_ratio = 0

            # Try all NSE symbols
            for nse_symbol, nse_info in nse_symbols.items():
                nse_name = nse_info.get('company_name', '')

                if not nse_name:
                    continue

                nse_clean = self.clean_company_name(nse_name)
                ratio = fuzz.token_sort_ratio(bse_clean, nse_clean)

                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = (nse_symbol, nse_info)

            # Accept if ratio ≥80
            if best_ratio >= 80 and best_match:
                nse_symbol, nse_info = best_match
                confidence = best_ratio / 100.0

                if best_ratio >= 90:
                    match_method = "fuzzy_name_90"
                    requires_review = False
                else:
                    match_method = "fuzzy_name_80-89"
                    requires_review = True

                fuzzy_mappings[bse_code] = {
                    "nse_symbol": nse_symbol,
                    "company_name": bse_info.get('company_name'),
                    "isin": nse_info.get('isin'),
                    "match_method": match_method,
                    "confidence": confidence,
                    "updated_at": datetime.now().isoformat(),
                    "requires_manual_review": requires_review,
                    "status": "active",
                    "use_for_yfinance": True
                }

        logger.info(f"Fuzzy matching: {len(fuzzy_mappings)} mappings created")
        return fuzzy_mappings

    def get_top_companies_by_market_cap(self, top_n: int = 1000) -> List[Dict]:
        """
        Get top N companies by market cap from master stock list.

        Args:
            top_n: Number of top companies to return

        Returns:
            List of {bse_code, company_name, market_cap_cr}
        """
        # TODO: Implement actual query to master_stock_list.db
        # For now, return mock data for testing
        logger.warning("get_top_companies_by_market_cap not fully implemented, returning mapped companies")

        result = []
        for bse_code, mapping in list(self._mappings.items())[:top_n]:
            result.append({
                "bse_code": bse_code,
                "company_name": mapping.get('company_name', 'Unknown'),
                "market_cap_cr": 0  # Would be fetched from master list
            })

        return result

    def generate_manual_validation_csv(self, top_n: int = 1000) -> str:
        """
        AC1.3.5: Generate manual validation CSV for top N companies.

        Columns: bse_code, bse_name, proposed_nse_symbol, nse_name,
                 match_method, confidence, market_cap_cr, requires_manual_review

        Args:
            top_n: Number of top companies to include

        Returns:
            Path to generated CSV
        """
        import csv

        output_path = "/Users/srijan/Desktop/aksh/data/mapping_validation_top1000.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        top_companies = self.get_top_companies_by_market_cap(top_n)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'bse_code', 'bse_name', 'proposed_nse_symbol', 'nse_name',
                'match_method', 'confidence', 'market_cap_cr', 'requires_manual_review',
                'approved'  # User fills this
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for company in top_companies:
                bse_code = company['bse_code']
                mapping = self._mappings.get(bse_code, {})

                requires_review = mapping.get('confidence', 0) < 0.90 or \
                                 mapping.get('match_method', '') == 'fuzzy_name_80-89'

                writer.writerow({
                    'bse_code': bse_code,
                    'bse_name': company.get('company_name', ''),
                    'proposed_nse_symbol': mapping.get('nse_symbol', ''),
                    'nse_name': '',  # Would fetch from NSE data
                    'match_method': mapping.get('match_method', ''),
                    'confidence': f"{mapping.get('confidence', 0):.2f}",
                    'market_cap_cr': company.get('market_cap_cr', 0),
                    'requires_manual_review': 'TRUE' if requires_review else 'FALSE',
                    'approved': ''  # User fills
                })

        logger.info(f"Generated manual validation CSV: {output_path}")
        return output_path

    def apply_manual_corrections(self, validation_csv: str) -> int:
        """
        AC1.3.5: Apply manual corrections from validation CSV.

        Args:
            validation_csv: Path to user-corrected validation CSV

        Returns:
            Count of corrections applied
        """
        import csv

        corrections = 0

        try:
            with open(validation_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    approved = row.get('approved', '').upper()

                    if approved == 'YES':
                        bse_code = row['bse_code']
                        nse_symbol = row['proposed_nse_symbol']

                        # Update or add mapping
                        self._mappings[bse_code] = {
                            "nse_symbol": nse_symbol,
                            "company_name": row['bse_name'],
                            "isin": None,
                            "match_method": "manual_correction",
                            "confidence": 1.0,
                            "updated_at": datetime.now().isoformat(),
                            "requires_manual_review": False,
                            "status": "active",
                            "use_for_yfinance": True
                        }
                        corrections += 1

            logger.info(f"Applied {corrections} manual corrections from {validation_csv}")
            return corrections

        except Exception as e:
            logger.error(f"Error applying manual corrections: {e}")
            return 0

    def save_final_mapping(self, output_path: str) -> MappingReport:
        """
        AC1.3.6: Save final mapping to JSON.

        Args:
            output_path: Path to output JSON file

        Returns:
            MappingReport with statistics
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self._mappings, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self._mappings)} mappings to {output_path}")

            # Calculate statistics
            isin_matches = sum(1 for m in self._mappings.values() if m.get('match_method', '').startswith('isin'))
            fuzzy_matches = sum(1 for m in self._mappings.values() if m.get('match_method', '').startswith('fuzzy'))
            baseline = sum(1 for m in self._mappings.values() if m.get('match_method') == 'existing_baseline')
            manual_review = sum(1 for m in self._mappings.values() if m.get('requires_manual_review', False))

            coverage = self.calculate_coverage()

            return MappingReport(
                total_bse_companies=self._total_bse_companies,
                total_mapped=len(self._mappings),
                coverage_percent=coverage,
                isin_matches=isin_matches,
                fuzzy_matches=fuzzy_matches,
                baseline_preserved=baseline,
                requires_manual_review=manual_review,
                conflicts_logged=len(self._conflicts),
                anomalies_logged=len(self._anomalies),
                unmapped_count=self._total_bse_companies - len(self._mappings)
            )

        except Exception as e:
            logger.error(f"Error saving final mapping: {e}")
            raise

    def save_to_database(self, db_path: str):
        """
        AC1.3.6: Save mapping to SQLite database.

        Args:
            db_path: Path to SQLite database
        """
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mappings (
                bse_code TEXT PRIMARY KEY,
                nse_symbol TEXT NOT NULL,
                company_name TEXT,
                isin TEXT,
                match_method TEXT,
                confidence REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                requires_manual_review INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active'
            )
        """)

        # Insert mappings
        for bse_code, mapping in self._mappings.items():
            cursor.execute("""
                INSERT OR REPLACE INTO mappings
                (bse_code, nse_symbol, company_name, isin, match_method, confidence, updated_at, requires_manual_review, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bse_code,
                mapping['nse_symbol'],
                mapping.get('company_name'),
                mapping.get('isin'),
                mapping.get('match_method'),
                mapping.get('confidence'),
                mapping.get('updated_at'),
                1 if mapping.get('requires_manual_review', False) else 0,
                mapping.get('status', 'active')
            ))

        conn.commit()
        conn.close()

        logger.info(f"Saved {len(self._mappings)} mappings to database {db_path}")

    def calculate_coverage(self) -> float:
        """
        AC1.3.7: Calculate coverage percentage.

        Returns:
            Coverage percentage (0-100)
        """
        if self._total_bse_companies == 0:
            return 0.0

        coverage = (len(self._mappings) / self._total_bse_companies) * 100
        return round(coverage, 2)

    def generate_unmapped_report(self) -> str:
        """
        AC1.3.7: Generate unmapped companies report if coverage < 80%.

        Returns:
            Path to unmapped_companies.csv
        """
        import csv

        output_path = "/Users/srijan/Desktop/aksh/data/unmapped_companies.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # TODO: Would query master stock list for full details
        # For now, create placeholder report

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['bse_code', 'company_name', 'market_cap_cr', 'listing_date', 'reason_unmapped']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Would write unmapped companies here
            writer.writerow({
                'bse_code': 'example',
                'company_name': 'Example Company',
                'market_cap_cr': 0,
                'listing_date': '',
                'reason_unmapped': 'no_isin_no_fuzzy_match'
            })

        logger.info(f"Generated unmapped companies report: {output_path}")
        return output_path

    def is_nse_symbol_delisted(self, nse_symbol: str) -> bool:
        """
        AC1.3.8: Check if NSE symbol is delisted.

        Args:
            nse_symbol: NSE ticker symbol

        Returns:
            True if delisted
        """
        # TODO: Implement actual delisting check (query NSE API or master list)
        # For now, return False
        return False

    def validate_nse_symbol(self, bse_code: str, nse_symbol: str) -> Dict:
        """
        AC1.3.8: Validate NSE symbol (check if delisted).

        Args:
            bse_code: BSE code
            nse_symbol: Proposed NSE symbol

        Returns:
            Validation result with status
        """
        is_delisted = self.is_nse_symbol_delisted(nse_symbol)

        return {
            "bse_code": bse_code,
            "nse_symbol": nse_symbol,
            "status": "delisted" if is_delisted else "active",
            "use_for_yfinance": not is_delisted
        }

    def run_full_mapping(self, output_dir: str = "/Users/srijan/Desktop/aksh/data") -> MappingReport:
        """
        Run full BSE-NSE mapping workflow.

        Steps:
        1. Load baseline
        2. Download BhavCopy files
        3. ISIN matching
        4. Fuzzy name matching
        5. Generate validation CSV
        6. Save final mapping

        Args:
            output_dir: Directory for output files

        Returns:
            MappingReport with statistics
        """
        os.makedirs(output_dir, exist_ok=True)

        # Step 1: Download BhavCopy files
        logger.info("Step 1: Downloading BhavCopy files...")
        bse_csv, nse_csv = self.download_bhav_copies()

        # Step 2: Parse BhavCopy files
        logger.info("Step 2: Parsing BhavCopy files...")
        bse_data = self.parse_bse_bhav_copy(bse_csv)
        nse_data = self.parse_nse_bhav_copy(nse_csv)

        # Step 3: ISIN matching
        logger.info("Step 3: ISIN-based matching...")
        isin_mappings = self.extract_isin_mappings(bse_data, nse_data)
        self._mappings.update(isin_mappings)

        # Step 4: Fuzzy name matching for unmapped
        logger.info("Step 4: Fuzzy name matching...")
        unmapped_bse = {code: data for code, data in bse_data.items() if code not in self._mappings}
        fuzzy_mappings = self.fuzzy_match_names(unmapped_bse, nse_data)
        self._mappings.update(fuzzy_mappings)

        # Step 5: Generate validation CSV
        logger.info("Step 5: Generating manual validation CSV...")
        validation_csv = self.generate_manual_validation_csv(top_n=1000)

        # Step 6: Save final mapping
        logger.info("Step 6: Saving final mapping...")
        mapping_json = os.path.join(output_dir, "bse_nse_mapping.json")
        mapping_db = os.path.join(output_dir, "bse_nse_mapping.db")

        report = self.save_final_mapping(mapping_json)
        self.save_to_database(mapping_db)

        # Step 7: Check coverage and generate unmapped report if needed
        logger.info("Step 7: Checking coverage...")
        if report.coverage_percent < 80:
            logger.warning(f"Coverage {report.coverage_percent:.1f}% below 80% target")
            self.generate_unmapped_report()

        logger.info(f"""
BSE-NSE Mapping Complete!
=========================
Total BSE Companies: {report.total_bse_companies}
Total Mapped: {report.total_mapped}
Coverage: {report.coverage_percent:.1f}%

Breakdown:
- Baseline Preserved: {report.baseline_preserved}
- ISIN Matches: {report.isin_matches}
- Fuzzy Matches: {report.fuzzy_matches}
- Requires Manual Review: {report.requires_manual_review}
- Conflicts Logged: {report.conflicts_logged}
- Anomalies Logged: {report.anomalies_logged}
- Unmapped: {report.unmapped_count}

Output Files:
- {mapping_json}
- {mapping_db}
- {validation_csv}
        """)

        return report


# Demo for Story 1.2
if __name__ == "__main__":
    # Previous demo code for MLDataCollectorAgent...
    pass

# Story 1.4 imports
from agents.ml.financial_extractor_story_1_4 import (
    FinancialExtractor,
    FinancialData,
    ValidationResult,
    ExtractionReport,
    FailureAnalysisReport,
    extract_financial_data
)


# ============================================================================
# Story 1.5: PriceCollector - Historical Price & Volume Data Collection
# ============================================================================

@dataclass
class PriceCollectionReport:
    """Summary report for price data collection (AC1.5.5)"""
    total_files_downloaded: int
    total_records_stored: int
    total_companies: int
    average_completeness: float
    companies_above_95_pct: int
    gaps_filled_by_yfinance: int
    validation_failures: int
    duration_seconds: float


@dataclass
class OHLCValidationReport:
    """OHLC data quality validation report (AC1.5.6)"""
    total_records: int
    invalid_records: int
    anomalies: Dict[str, str]  # {bse_code_date: error_type}


class PriceCollector:
    """
    Collects historical price and volume data from BhavCopy files (Story 1.5).

    Workflow:
    1. Download BSE/NSE BhavCopy CSV files for date range (AC1.5.1, AC1.5.2)
    2. Parse CSV files and store in price_movements.db (AC1.5.3)
    3. Fill gaps using yfinance fallback (AC1.5.4)
    4. Calculate data completeness per company (AC1.5.5)
    5. Validate OHLC data quality (AC1.5.6)

    Target: ≥95% data completeness for ≥90% of companies
    """

    def __init__(self, db_path: str, cache_dir: str = "/Users/srijan/Desktop/aksh/data/bhav_copy_cache"):
        self.db_path = db_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for BSE and NSE
        (self.cache_dir / "bse").mkdir(exist_ok=True)
        (self.cache_dir / "nse").mkdir(exist_ok=True)

        self.incomplete_data_log = "/Users/srijan/Desktop/aksh/data/incomplete_price_data.csv"
        self.anomaly_log = "/Users/srijan/Desktop/aksh/data/price_data_anomalies.csv"

        # Load BSE-NSE mapping for yfinance fallback
        self.bse_nse_mapping = self._load_bse_nse_mapping()

        self._initialize_database()
        logger.info(f"PriceCollector initialized: {db_path}")

    def _load_bse_nse_mapping(self) -> Dict[str, str]:
        """Load BSE→NSE mapping for yfinance fallback"""
        mapping_path = "/Users/srijan/Desktop/aksh/data/bse_nse_mapping.json"
        if not os.path.exists(mapping_path):
            logger.warning(f"BSE-NSE mapping not found: {mapping_path}")
            return {}

        try:
            with open(mapping_path, 'r') as f:
                data = json.load(f)
                return {bse: info['nse_symbol'] for bse, info in data.items() if 'nse_symbol' in info}
        except Exception as e:
            logger.error(f"Error loading BSE-NSE mapping: {e}")
            return {}

    def _initialize_database(self):
        """AC1.5.3: Create price_movements table with indexes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_movements (
                price_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bse_code TEXT,
                nse_symbol TEXT,
                date DATE NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume INTEGER NOT NULL,
                prev_close REAL,
                circuit_limit REAL,
                hit_upper_circuit BOOLEAN,
                hit_lower_circuit BOOLEAN,
                source TEXT CHECK(source IN ('bse_bhav_copy', 'nse_bhav_copy', 'yfinance_fallback')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bse_code, date) ON CONFLICT REPLACE
            )
        """)

        # AC1.5.7: Create indexes for fast querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bse_date ON price_movements(bse_code, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nse_date ON price_movements(nse_symbol, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON price_movements(date)")

        conn.commit()
        conn.close()

    def download_bse_bhav_copies(self, start_date: str, end_date: str) -> List[str]:
        """AC1.5.1: Download BSE BhavCopy CSV files for all trading days"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        downloaded_files = []
        current_date = start

        while current_date <= end:
            # Skip weekends
            if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date += timedelta(days=1)
                continue

            # Format: EQ131124.csv for 13/11/2024
            date_str = current_date.strftime("%d%m%y")
            filename = f"EQ{date_str}.csv"
            cached_file = self.cache_dir / "bse" / filename

            # AC1.5.1: Skip if file already cached
            if cached_file.exists() and cached_file.stat().st_size > 0:
                downloaded_files.append(str(cached_file))
                current_date += timedelta(days=1)
                continue

            # Download
            url = f"https://www.bseindia.com/download/BhavCopy/Equity/EQ{date_str}_CSV.ZIP"

            for attempt in range(3):  # AC1.5.1: Retry 3x on failure
                try:
                    import requests
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()

                    # Extract ZIP
                    import zipfile
                    import io
                    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                        csv_filename = z.namelist()[0]
                        csv_content = z.read(csv_filename)
                        cached_file.write_bytes(csv_content)

                    downloaded_files.append(str(cached_file))
                    logger.info(f"Downloaded BSE BhavCopy: {filename}")

                    # AC1.5.1: 0.5s delay between requests
                    time.sleep(0.5)
                    break

                except Exception as e:
                    if attempt == 2:
                        logger.error(f"Failed to download {url} after 3 attempts: {e}")
                    else:
                        time.sleep(1)

            current_date += timedelta(days=1)

        return downloaded_files

    def download_nse_bhav_copies(self, start_date: str, end_date: str) -> List[str]:
        """AC1.5.2: Download NSE BhavCopy CSV files for all trading days"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        downloaded_files = []
        current_date = start

        # AC1.5.2: NSE requires specific headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        while current_date <= end:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            # Format: cm13NOV2024bhav.csv
            date_str = current_date.strftime("%d%b%Y").upper()
            filename = f"cm{date_str}bhav.csv"
            cached_file = self.cache_dir / "nse" / filename

            # Skip if cached
            if cached_file.exists() and cached_file.stat().st_size > 0:
                downloaded_files.append(str(cached_file))
                current_date += timedelta(days=1)
                continue

            # URL format: https://archives.nseindia.com/content/historical/EQUITIES/2024/NOV/cm13NOV2024bhav.csv.zip
            year = current_date.strftime("%Y")
            month = current_date.strftime("%b").upper()
            url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year}/{month}/cm{date_str}bhav.csv.zip"

            try:
                import requests
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()

                # Extract ZIP
                import zipfile
                import io
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    csv_filename = z.namelist()[0]
                    csv_content = z.read(csv_filename)
                    cached_file.write_bytes(csv_content)

                downloaded_files.append(str(cached_file))
                logger.info(f"Downloaded NSE BhavCopy: {filename}")
                time.sleep(0.5)

            except Exception as e:
                # AC1.5.2: Handle 404 for weekends/holidays gracefully
                if "404" in str(e):
                    logger.debug(f"Non-trading day: {current_date.strftime('%Y-%m-%d')}")
                else:
                    logger.error(f"Failed to download NSE BhavCopy: {e}")

            current_date += timedelta(days=1)

        return downloaded_files

    def parse_bhav_copy(self, csv_path: str, source: str, date: str) -> pd.DataFrame:
        """AC1.5.3: Parse CSV files and return DataFrame"""
        try:
            import pandas as pd

            if source == 'bse_bhav_copy':
                # BSE columns: SC_CODE, SC_NAME, OPEN, HIGH, LOW, CLOSE, NO_OF_SHRS, NET_TURNOV, TDCLOINDI
                df = pd.read_csv(csv_path)

                # Rename columns
                df = df.rename(columns={
                    'SC_CODE': 'bse_code',
                    'OPEN': 'open',
                    'HIGH': 'high',
                    'LOW': 'low',
                    'CLOSE': 'close',
                    'NO_OF_SHRS': 'volume',
                    'TDCLOINDI': 'circuit_indicator'
                })

                # Add metadata
                df['bse_code'] = df['bse_code'].astype(str)
                df['date'] = date
                df['source'] = source
                df['hit_upper_circuit'] = df['circuit_indicator'] == 'C'
                df['nse_symbol'] = None

                # Select relevant columns
                df = df[['bse_code', 'nse_symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'hit_upper_circuit', 'source']]

            elif source == 'nse_bhav_copy':
                # NSE columns: SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, TOTTRDQTY, TOTTRDVAL, PREV_CLOSE
                df = pd.read_csv(csv_path)

                # Filter to EQ series only
                df = df[df['SERIES'] == 'EQ']

                # Rename columns
                df = df.rename(columns={
                    'SYMBOL': 'nse_symbol',
                    'OPEN': 'open',
                    'HIGH': 'high',
                    'LOW': 'low',
                    'CLOSE': 'close',
                    'TOTTRDQTY': 'volume',
                    'PREV_CLOSE': 'prev_close'
                })

                # Add metadata
                df['date'] = date
                df['source'] = source
                df['bse_code'] = None

                # Select relevant columns
                df = df[['bse_code', 'nse_symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'prev_close', 'source']]

            else:
                raise ValueError(f"Unknown source: {source}")

            return df

        except Exception as e:
            logger.error(f"Error parsing {csv_path}: {e}")
            return pd.DataFrame()

    def store_price_data(self, df: pd.DataFrame) -> int:
        """AC1.5.3: Store parsed data in price_movements.db"""
        if df.empty:
            return 0

        conn = sqlite3.connect(self.db_path)

        # Use pandas to_sql with if_exists='append'
        # But we have UNIQUE constraint, so it will replace on conflict
        rows_inserted = 0

        for _, row in df.iterrows():
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO price_movements
                    (bse_code, nse_symbol, date, open, high, low, close, volume, prev_close, hit_upper_circuit, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('bse_code'),
                    row.get('nse_symbol'),
                    row['date'],
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume'],
                    row.get('prev_close'),
                    row.get('hit_upper_circuit'),
                    row['source']
                ))
                rows_inserted += 1
            except Exception as e:
                logger.error(f"Error inserting row: {e}")

        conn.commit()
        conn.close()

        return rows_inserted

    def identify_gaps(self, bse_codes: List[str], start_date: str, end_date: str, expected_days: int = None) -> Dict[str, List[str]]:
        """AC1.5.4: Identify companies with <95% date coverage"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        # Calculate expected trading days (~250 per year)
        if expected_days is None:
            total_days = (end - start).days
            expected_days = int(total_days * 250 / 365)  # Rough estimate

        gaps = {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for bse_code in bse_codes:
            cursor.execute("""
                SELECT COUNT(*) FROM price_movements
                WHERE bse_code=? AND date BETWEEN ? AND ?
            """, (bse_code, start_date, end_date))

            actual_days = cursor.fetchone()[0]
            completeness = (actual_days / expected_days * 100) if expected_days > 0 else 0

            if completeness < 95.0:
                # Identify missing dates
                cursor.execute("""
                    SELECT date FROM price_movements
                    WHERE bse_code=? AND date BETWEEN ? AND ?
                    ORDER BY date
                """, (bse_code, start_date, end_date))

                existing_dates = set(row[0] for row in cursor.fetchall())

                # Generate all expected dates
                all_dates = []
                current = start
                while current <= end:
                    if current.weekday() < 5:  # Exclude weekends
                        all_dates.append(current.strftime("%Y-%m-%d"))
                    current += timedelta(days=1)

                missing_dates = [d for d in all_dates if d not in existing_dates]
                gaps[bse_code] = missing_dates

        conn.close()
        return gaps

    def fill_gaps_with_yfinance(self, bse_code: str, missing_dates: List[str]) -> int:
        """AC1.5.4: Fill missing dates using yfinance"""
        if not missing_dates:
            return 0

        # Get NSE symbol for yfinance
        nse_symbol = self.bse_nse_mapping.get(bse_code)
        if not nse_symbol:
            logger.warning(f"No NSE mapping for BSE code: {bse_code}")
            return 0

        try:
            import yfinance as yf

            # Download data for missing dates
            start_date = min(missing_dates)
            end_date = max(missing_dates)

            ticker = f"{nse_symbol}.NS"
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if df.empty:
                return 0

            # Convert to price_movements format
            gaps_filled = 0

            for date_idx, row in df.iterrows():
                date_str = date_idx.strftime("%Y-%m-%d")

                if date_str in missing_dates:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT OR REPLACE INTO price_movements
                        (bse_code, nse_symbol, date, open, high, low, close, volume, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'yfinance_fallback')
                    """, (
                        bse_code,
                        nse_symbol,
                        date_str,
                        row['Open'],
                        row['High'],
                        row['Low'],
                        row['Close'],
                        int(row['Volume'])
                    ))

                    conn.commit()
                    conn.close()
                    gaps_filled += 1

            # AC1.5.4: Rate limit - 1 second between yfinance calls
            time.sleep(1)

            return gaps_filled

        except Exception as e:
            logger.error(f"Error filling gaps with yfinance for {bse_code}: {e}")
            return 0

    def calculate_completeness(self, bse_codes: List[str], expected_days: int = 975) -> Dict[str, float]:
        """AC1.5.5: Calculate completeness per company"""
        completeness = {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for bse_code in bse_codes:
            cursor.execute("SELECT COUNT(*) FROM price_movements WHERE bse_code=?", (bse_code,))
            actual_days = cursor.fetchone()[0]

            completeness_pct = (actual_days / expected_days * 100) if expected_days > 0 else 0
            completeness[bse_code] = completeness_pct

        conn.close()
        return completeness

    def log_incomplete_companies(self, completeness: Dict[str, float], threshold: float = 95.0):
        """AC1.5.5: Log companies with <95% completeness to CSV"""
        import csv

        incomplete = {bse: pct for bse, pct in completeness.items() if pct < threshold}

        if not incomplete:
            return

        os.makedirs(os.path.dirname(self.incomplete_data_log), exist_ok=True)

        with open(self.incomplete_data_log, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['bse_code', 'completeness_pct', 'missing_days'])
            writer.writeheader()

            for bse_code, pct in incomplete.items():
                missing = int(975 * (1 - pct / 100))
                writer.writerow({
                    'bse_code': bse_code,
                    'completeness_pct': f"{pct:.1f}",
                    'missing_days': missing
                })

    def validate_ohlc_data(self) -> OHLCValidationReport:
        """AC1.5.6: Validate OHLC data quality"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM price_movements")
        total_records = cursor.fetchone()[0]

        anomalies = {}

        # AC1.5.6 Check 1: OHLC relationships
        cursor.execute("""
            SELECT bse_code, date, open, high, low, close
            FROM price_movements
            WHERE low > high OR open < low OR open > high OR close < low OR close > high
        """)

        for row in cursor.fetchall():
            bse_code, date, open_price, high, low, close = row
            key = f"{bse_code}_{date}"
            anomalies[key] = "OHLC_RELATIONSHIP_VIOLATION"

        # AC1.5.6 Check 3: No future dates
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT bse_code, date FROM price_movements WHERE date > ?", (today,))

        for row in cursor.fetchall():
            bse_code, date = row
            key = f"{bse_code}_{date}"
            anomalies[key] = "FUTURE_DATE"

        # AC1.5.6 Check 4: Price continuity
        cursor.execute("""
            SELECT bse_code, date, close, prev_close
            FROM price_movements
            WHERE prev_close IS NOT NULL AND prev_close > 0
        """)

        for row in cursor.fetchall():
            bse_code, date, close, prev_close = row
            if prev_close and prev_close > 0:
                pct_change = abs((close - prev_close) / prev_close)
                if pct_change > 0.5:  # 50% jump
                    key = f"{bse_code}_{date}"
                    anomalies[key] = f"PRICE_JUMP_{pct_change:.1%}"

        conn.close()

        return OHLCValidationReport(
            total_records=total_records,
            invalid_records=len(anomalies),
            anomalies=anomalies
        )

    def log_anomalies(self, report: OHLCValidationReport):
        """AC1.5.6: Log validation failures to CSV"""
        if not report.anomalies:
            return

        import csv

        os.makedirs(os.path.dirname(self.anomaly_log), exist_ok=True)

        with open(self.anomaly_log, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['bse_code', 'date', 'error_type'])
            writer.writeheader()

            for key, error_type in report.anomalies.items():
                bse_code, date = key.split('_', 1)
                writer.writerow({
                    'bse_code': bse_code,
                    'date': date,
                    'error_type': error_type
                })

    def collect_all_price_data(self, bse_codes: List[str], start_date: str, end_date: str) -> PriceCollectionReport:
        """AC1.5.1-AC1.5.7: Collect all price data for specified companies and date range"""
        start_time = time.time()

        logger.info(f"Starting price data collection for {len(bse_codes)} companies")

        # Step 1: Download BhavCopy files
        bse_files = self.download_bse_bhav_copies(start_date, end_date)
        nse_files = self.download_nse_bhav_copies(start_date, end_date)

        total_files = len(bse_files) + len(nse_files)
        logger.info(f"Downloaded {total_files} BhavCopy files")

        # Step 2: Parse and store BSE data
        total_records = 0
        for csv_path in bse_files:
            date_str = Path(csv_path).stem.replace("EQ", "")
            # Convert DDMMYY to YYYY-MM-DD
            try:
                date_obj = datetime.strptime(date_str, "%d%m%y")
                date_formatted = date_obj.strftime("%Y-%m-%d")
            except:
                continue

            df = self.parse_bhav_copy(csv_path, source='bse_bhav_copy', date=date_formatted)
            records = self.store_price_data(df)
            total_records += records

        # Step 3: Parse and store NSE data
        for csv_path in nse_files:
            # Extract date from filename like cm13NOV2024bhav.csv
            filename = Path(csv_path).stem
            try:
                date_part = filename.replace("cm", "").replace("bhav", "")
                date_obj = datetime.strptime(date_part, "%d%b%Y")
                date_formatted = date_obj.strftime("%Y-%m-%d")
            except:
                continue

            df = self.parse_bhav_copy(csv_path, source='nse_bhav_copy', date=date_formatted)
            records = self.store_price_data(df)
            total_records += records

        # Step 4: Fill gaps with yfinance
        gaps = self.identify_gaps(bse_codes, start_date, end_date)
        gaps_filled = 0

        for bse_code, missing_dates in gaps.items():
            filled = self.fill_gaps_with_yfinance(bse_code, missing_dates)
            gaps_filled += filled

        # Step 5: Calculate completeness
        completeness = self.calculate_completeness(bse_codes)
        avg_completeness = sum(completeness.values()) / len(completeness) if completeness else 0
        companies_above_95 = sum(1 for pct in completeness.values() if pct >= 95.0)

        self.log_incomplete_companies(completeness)

        # Step 6: Validate OHLC data
        validation_report = self.validate_ohlc_data()
        self.log_anomalies(validation_report)

        duration = time.time() - start_time

        return PriceCollectionReport(
            total_files_downloaded=total_files,
            total_records_stored=total_records,
            total_companies=len(bse_codes),
            average_completeness=avg_completeness,
            companies_above_95_pct=companies_above_95,
            gaps_filled_by_yfinance=gaps_filled,
            validation_failures=validation_report.invalid_records,
            duration_seconds=duration
        )


# ============================================================================
# Story 1.6: DataQualityValidator - Validate Data Quality Before Training
# ============================================================================

@dataclass
class CheckResult:
    """Individual validation check result (AC1.6.1)"""
    check_name: str
    status: str  # "PASS" or "FAIL"
    metric_value: float
    threshold: float
    passed: bool
    details: str


@dataclass
class ValidationReport:
    """Comprehensive validation report (AC1.6.1)"""
    timestamp: datetime
    checks_passed: int
    checks_failed: int
    total_samples: int
    usable_companies: int
    estimated_model_f1: float
    checks: List[CheckResult]
    remediation_steps: List[str]


class DataQualityValidator:
    """
    Validates data quality before ML training (Story 1.6).

    Performs 5 critical checks:
    1. ≥200,000 labeled samples
    2. Class distribution 5-15%
    3. ≥80% companies with complete financials
    4. ≥95% price data completeness
    5. ≥80% BSE-NSE mapping coverage

    Target: ≥4 of 5 checks passing, estimated F1 ≥ 0.70
    """

    def __init__(self, db_paths: Dict[str, str]):
        self.db_paths = db_paths
        logger.info("DataQualityValidator initialized")

    def check_labeled_samples_count(self) -> CheckResult:
        """AC1.6.2: Check 1 - Verify ≥200,000 labeled samples"""
        threshold = 200000.0

        try:
            conn = sqlite3.connect(self.db_paths['upper_circuits'])
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels")
            count = cursor.fetchone()[0]

            conn.close()

            passed = count >= threshold
            status = "PASS" if passed else "FAIL"

            if passed:
                details = "Sufficient samples for training"
            else:
                shortfall = int(threshold - count)
                details = f"{shortfall:,} samples below threshold"

            return CheckResult(
                check_name="Labeled Samples Count",
                status=status,
                metric_value=float(count),
                threshold=threshold,
                passed=passed,
                details=details
            )

        except Exception as e:
            logger.error(f"Error checking labeled samples: {e}")
            return CheckResult(
                check_name="Labeled Samples Count",
                status="ERROR",
                metric_value=0.0,
                threshold=threshold,
                passed=False,
                details=f"Error: {str(e)}"
            )

    def check_class_distribution(self) -> CheckResult:
        """AC1.6.3: Check 2 - Verify class distribution 5-15%"""
        min_threshold = 5.0
        max_threshold = 15.0

        try:
            conn = sqlite3.connect(self.db_paths['upper_circuits'])
            cursor = conn.cursor()

            cursor.execute("""
                SELECT (SUM(CASE WHEN label=1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS positive_ratio
                FROM upper_circuit_labels
            """)

            positive_ratio = cursor.fetchone()[0]
            conn.close()

            passed = min_threshold <= positive_ratio <= max_threshold
            status = "PASS" if passed else "FAIL"

            if passed:
                details = f"Balanced distribution: {positive_ratio:.1f}% positive"
            elif positive_ratio < min_threshold:
                details = f"Class imbalance severe at {positive_ratio:.1f}%. SMOTE may struggle."
            else:
                details = f"Class imbalance low at {positive_ratio:.1f}%. Labels may be too lenient."

            return CheckResult(
                check_name="Class Distribution",
                status=status,
                metric_value=positive_ratio,
                threshold=min_threshold,  # Report lower bound
                passed=passed,
                details=details
            )

        except Exception as e:
            logger.error(f"Error checking class distribution: {e}")
            return CheckResult(
                check_name="Class Distribution",
                status="ERROR",
                metric_value=0.0,
                threshold=min_threshold,
                passed=False,
                details=f"Error: {str(e)}"
            )

    def check_financial_data_coverage(self) -> CheckResult:
        """AC1.6.4: Check 3 - Verify ≥80% companies have complete financials"""
        threshold = 80.0

        try:
            financials_conn = sqlite3.connect(self.db_paths['financials'])
            master_conn = sqlite3.connect(self.db_paths['master_stock_list'])

            # Count companies with ≥12 quarters
            financials_cursor = financials_conn.cursor()
            financials_cursor.execute("""
                SELECT COUNT(DISTINCT bse_code) FROM (
                    SELECT bse_code, COUNT(DISTINCT quarter || year) as quarter_count
                    FROM historical_financials
                    GROUP BY bse_code
                    HAVING quarter_count >= 12
                )
            """)
            companies_with_complete_data = financials_cursor.fetchone()[0]

            # Total companies
            master_cursor = master_conn.cursor()
            master_cursor.execute("SELECT COUNT(*) FROM master_stock_list")
            total_companies = master_cursor.fetchone()[0]

            financials_conn.close()
            master_conn.close()

            coverage = (companies_with_complete_data / total_companies * 100) if total_companies > 0 else 0

            passed = coverage >= threshold
            status = "PASS" if passed else "FAIL"

            if passed:
                details = f"{companies_with_complete_data:,} companies with complete financial data"
            else:
                missing = total_companies - companies_with_complete_data
                details = f"Missing data for {missing:,} companies ({coverage:.1f}% coverage)"

            return CheckResult(
                check_name="Financial Data Coverage",
                status=status,
                metric_value=coverage,
                threshold=threshold,
                passed=passed,
                details=details
            )

        except Exception as e:
            logger.error(f"Error checking financial coverage: {e}")
            return CheckResult(
                check_name="Financial Data Coverage",
                status="ERROR",
                metric_value=0.0,
                threshold=threshold,
                passed=False,
                details=f"Error: {str(e)}"
            )

    def check_price_data_completeness(self) -> CheckResult:
        """AC1.6.5: Check 4 - Verify ≥95% price data completeness"""
        threshold = 95.0
        expected_days = 975

        try:
            conn = sqlite3.connect(self.db_paths['price_movements'])
            cursor = conn.cursor()

            cursor.execute("""
                SELECT AVG(completeness) AS avg_completeness FROM (
                    SELECT bse_code, (COUNT(DISTINCT date) * 100.0 / ?) AS completeness
                    FROM price_movements
                    WHERE date BETWEEN '2022-01-01' AND '2025-11-13'
                    GROUP BY bse_code
                )
            """, (expected_days,))

            result = cursor.fetchone()
            avg_completeness = result[0] if result and result[0] else 0.0

            conn.close()

            passed = avg_completeness >= threshold
            status = "PASS" if passed else "FAIL"

            if passed:
                details = f"Average {avg_completeness:.1f}% data completeness across companies"
            else:
                shortfall = threshold - avg_completeness
                details = f"Average completeness {avg_completeness:.1f}% is {shortfall:.1f}% below threshold"

            return CheckResult(
                check_name="Price Data Completeness",
                status=status,
                metric_value=avg_completeness,
                threshold=threshold,
                passed=passed,
                details=details
            )

        except Exception as e:
            logger.error(f"Error checking price completeness: {e}")
            return CheckResult(
                check_name="Price Data Completeness",
                status="ERROR",
                metric_value=0.0,
                threshold=threshold,
                passed=False,
                details=f"Error: {str(e)}"
            )

    def check_bse_nse_mapping_coverage(self) -> CheckResult:
        """AC1.6.6: Check 5 - Verify ≥80% BSE-NSE mapping coverage"""
        threshold = 80.0

        try:
            mapping_conn = sqlite3.connect(self.db_paths['bse_nse_mapping'])
            master_conn = sqlite3.connect(self.db_paths['master_stock_list'])

            # Count mapped companies
            mapping_cursor = mapping_conn.cursor()
            mapping_cursor.execute("SELECT COUNT(*) FROM mappings")
            mapped_count = mapping_cursor.fetchone()[0]

            # Total companies
            master_cursor = master_conn.cursor()
            master_cursor.execute("SELECT COUNT(*) FROM master_stock_list")
            total_count = master_cursor.fetchone()[0]

            mapping_conn.close()
            master_conn.close()

            coverage = (mapped_count / total_count * 100) if total_count > 0 else 0

            passed = coverage >= threshold
            status = "PASS" if passed else "FAIL"

            if passed:
                details = f"{mapped_count:,} of {total_count:,} companies mapped ({coverage:.1f}%)"
            else:
                unmapped = total_count - mapped_count
                details = f"{unmapped:,} companies unmapped ({coverage:.1f}% coverage)"

            return CheckResult(
                check_name="BSE-NSE Mapping Coverage",
                status=status,
                metric_value=coverage,
                threshold=threshold,
                passed=passed,
                details=details
            )

        except Exception as e:
            logger.error(f"Error checking mapping coverage: {e}")
            return CheckResult(
                check_name="BSE-NSE Mapping Coverage",
                status="ERROR",
                metric_value=0.0,
                threshold=threshold,
                passed=False,
                details=f"Error: {str(e)}"
            )

    def estimate_model_performance(self, checks: List[CheckResult]) -> float:
        """AC1.6.7: Estimate model F1 score based on data quality heuristics"""
        # Start with baseline F1 of 0.65
        estimated_f1 = 0.65

        for check in checks:
            if not check.passed:
                # Deduct based on check importance
                if "Labeled Samples" in check.check_name:
                    estimated_f1 -= 0.15  # Critical
                elif "Financial Data" in check.check_name:
                    estimated_f1 -= 0.08  # High impact
                elif "Price Data" in check.check_name:
                    estimated_f1 -= 0.05  # Medium impact
                elif "Class Distribution" in check.check_name:
                    estimated_f1 -= 0.03  # Low-medium impact
                elif "Mapping" in check.check_name:
                    estimated_f1 -= 0.02  # Low impact

        # Bonus if all checks pass
        if all(check.passed for check in checks):
            estimated_f1 += 0.10

        return max(0.0, min(1.0, estimated_f1))

    def generate_remediation_steps(self, failed_checks: List[CheckResult]) -> List[str]:
        """AC1.6.8: Generate actionable remediation steps for failed checks"""
        remediation_steps = []

        # Priority 1: Critical failures (block training)
        critical_checks = [c for c in failed_checks if "Labeled Samples" in c.check_name and c.metric_value < 100000]
        if critical_checks:
            remediation_steps.append("🔴 PRIORITY 1 (CRITICAL): Insufficient labeled samples")
            remediation_steps.append("   - Option 1: Extend date range to 2021 (estimated +30K samples)")
            remediation_steps.append("   - Option 2: Relax earnings filter to include mid-cap companies")

        # Priority 2: High-impact failures
        high_impact = [c for c in failed_checks if "Financial Data" in c.check_name or "Labeled Samples" in c.check_name]
        for check in high_impact:
            if "Labeled Samples" in check.check_name and check not in critical_checks:
                remediation_steps.append("🟠 PRIORITY 2 (HIGH): Low sample count impacts model robustness")
                remediation_steps.append(f"   - Current: {int(check.metric_value):,} samples, Target: {int(check.threshold):,}")
                remediation_steps.append("   - Extend date range to 2021 or relax criteria")

            if "Financial Data" in check.check_name:
                remediation_steps.append("🟠 PRIORITY 2 (HIGH): Financial data coverage below threshold")
                remediation_steps.append(f"   - Current: {check.metric_value:.1f}%, Target: {check.threshold:.1f}%")
                remediation_steps.append("   - Option 1: Prioritize manual extraction for top 1,000 companies by market cap")
                remediation_steps.append("   - Option 2: Extend collection to Q1 2021")

        # Priority 3: Medium-impact failures
        medium_impact = [c for c in failed_checks if "Price Data" in c.check_name or "Class Distribution" in c.check_name]
        for check in medium_impact:
            if "Price Data" in check.check_name:
                remediation_steps.append("🟡 PRIORITY 3 (MEDIUM): Price data completeness suboptimal")
                remediation_steps.append(f"   - Current: {check.metric_value:.1f}%, Target: {check.threshold:.1f}%")
                remediation_steps.append("   - Run yfinance gap filling for companies with <95% completeness")

            if "Class Distribution" in check.check_name:
                if check.metric_value < 5.0:
                    remediation_steps.append("🟡 PRIORITY 3 (MEDIUM): Class imbalance too severe")
                    remediation_steps.append(f"   - Current: {check.metric_value:.1f}%, Target: 5-15%")
                    remediation_steps.append("   - Relax upper circuit criteria to ≥3% price change")
                else:
                    remediation_steps.append("🟡 PRIORITY 3 (MEDIUM): Class imbalance too low")
                    remediation_steps.append(f"   - Current: {check.metric_value:.1f}%, Target: 5-15%")
                    remediation_steps.append("   - Tighten criteria to ≥7% price change")

        # Priority 4: Low-impact failures
        low_impact = [c for c in failed_checks if "Mapping" in c.check_name]
        for check in low_impact:
            remediation_steps.append("🟢 PRIORITY 4 (LOW): BSE-NSE mapping coverage suboptimal")
            remediation_steps.append(f"   - Current: {check.metric_value:.1f}%, Target: {check.threshold:.1f}%")
            remediation_steps.append("   - Option 1: Lower fuzzy matching threshold to 85% (from 90%)")
            remediation_steps.append("   - Option 2: Manual mapping for top 500 unmapped companies")

        if not remediation_steps:
            remediation_steps.append("✅ No remediation needed - all checks passed!")

        return remediation_steps

    def validate_training_readiness(self) -> ValidationReport:
        """AC1.6.7: Run all validation checks and generate comprehensive report"""
        logger.info("Starting data quality validation...")

        # Run all 5 checks
        checks = [
            self.check_labeled_samples_count(),
            self.check_class_distribution(),
            self.check_financial_data_coverage(),
            self.check_price_data_completeness(),
            self.check_bse_nse_mapping_coverage()
        ]

        # Calculate summary statistics
        checks_passed = sum(1 for c in checks if c.passed)
        checks_failed = len(checks) - checks_passed

        # Get total samples
        try:
            conn = sqlite3.connect(self.db_paths['upper_circuits'])
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels")
            total_samples = cursor.fetchone()[0]
            conn.close()
        except:
            total_samples = 0

        # Get usable companies (with complete data)
        try:
            financials_conn = sqlite3.connect(self.db_paths['financials'])
            cursor = financials_conn.cursor()
            cursor.execute("""
                SELECT COUNT(DISTINCT bse_code) FROM (
                    SELECT bse_code, COUNT(DISTINCT quarter || year) as quarter_count
                    FROM historical_financials
                    GROUP BY bse_code
                    HAVING quarter_count >= 12
                )
            """)
            usable_companies = cursor.fetchone()[0]
            financials_conn.close()
        except:
            usable_companies = 0

        # Estimate model performance
        estimated_f1 = self.estimate_model_performance(checks)

        # Generate remediation steps
        failed_checks = [c for c in checks if not c.passed]
        remediation_steps = self.generate_remediation_steps(failed_checks)

        return ValidationReport(
            timestamp=datetime.now(),
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            total_samples=total_samples,
            usable_companies=usable_companies,
            estimated_model_f1=estimated_f1,
            checks=checks,
            remediation_steps=remediation_steps
        )

    def save_report(self, report: ValidationReport, output_path: str):
        """AC1.6.7: Save validation report to file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            f.write("========================================\n")
            f.write("DATA QUALITY VALIDATION REPORT\n")
            f.write("========================================\n")
            f.write(f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')} IST\n")
            f.write(f"Total Checks: {len(report.checks)}\n")
            f.write(f"Passed: {report.checks_passed}\n")
            f.write(f"Failed: {report.checks_failed}\n\n")

            f.write("CHECK RESULTS:\n")
            for check in report.checks:
                status_symbol = "[✓]" if check.passed else "[✗]"
                f.write(f"{status_symbol} {check.check_name}: {check.metric_value:,.1f} (threshold: ≥{check.threshold:,.1f})\n")
                f.write(f"    {check.details}\n")

            f.write(f"\nOVERALL STATUS: {'PASS' if report.checks_failed == 0 else 'FAIL'}")
            if report.checks_failed > 0:
                f.write(f" ({report.checks_failed} check(s) failed)\n")
            else:
                f.write("\n")

            f.write("\nUSABLE DATA:\n")
            f.write(f"- Total Labeled Samples: {report.total_samples:,}\n")
            f.write(f"- Companies with Complete Data: {report.usable_companies:,}\n")

            f.write("\nESTIMATED MODEL PERFORMANCE:\n")
            f.write(f"Based on data quality heuristics:\n")
            f.write(f"- Expected F1: {report.estimated_model_f1:.2f} (target: ≥0.70)\n")

            if report.checks_failed > 0:
                status = "below" if report.estimated_model_f1 < 0.70 else "meets"
                f.write(f"- Status: Model performance {status} target\n")

            if report.remediation_steps:
                f.write("\nREMEDIATION STEPS:\n")
                for i, step in enumerate(report.remediation_steps, 1):
                    f.write(f"{i}. {step}\n")

            f.write("\n========================================\n")

        logger.info(f"Validation report saved to {output_path}")


