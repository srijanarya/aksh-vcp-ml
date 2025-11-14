"""
Story 1.4: Financial Data Extractor

This module will be integrated into ml_data_collector.py

Extracts historical financial data from quarterly PDFs
Target: ≥80% extraction success rate
"""

import os
import sqlite3
import logging
import time
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FinancialData:
    """Extracted financial data from quarterly PDF (AC1.4.1)"""
    revenue_cr: float
    pat_cr: float
    eps: float
    opm: float
    npm: float
    extraction_confidence: float


@dataclass
class ValidationResult:
    """Data validation result (AC1.4.7)"""
    is_valid: bool
    failed_checks: List[str]
    adjusted_confidence: float


@dataclass
class ExtractionReport:
    """Summary report for financial data extraction (AC1.4.5)"""
    total_attempted: int
    total_successful: int
    total_failed: int
    success_rate: float
    duration_seconds: float
    failures_by_type: Dict[str, int]


@dataclass
class FailureAnalysisReport:
    """Failure analysis report (AC1.4.6)"""
    total_failures: int
    by_error_type: Dict[str, int]
    companies_high_failure_rate: List[Dict]


class FinancialExtractor:
    """
    Extracts historical financial data from quarterly PDFs (Story 1.4).

    Workflow:
    1. Query earnings announcements from earnings_calendar.db
    2. Download PDFs with caching
    3. Extract financial data using indian_pdf_extractor
    4. Validate extracted data
    5. Store in historical_financials.db
    6. Log failures for investigation

    Target: ≥80% extraction success rate
    """

    def __init__(self, db_path: str, cache_dir: str = "/tmp/earnings_pdfs_cache"):
        self.db_path = db_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.earnings_db_path = "/Users/srijan/vcp/data/earnings_calendar.db"
        self.failure_log_path = "/Users/srijan/Desktop/aksh/data/extraction_failures.csv"

        self._initialize_database()
        logger.info(f"FinancialExtractor initialized: {db_path}")

    def _initialize_database(self):
        """AC1.4.4: Create historical_financials table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_financials (
                financial_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bse_code TEXT NOT NULL,
                quarter TEXT NOT NULL CHECK(quarter IN ('Q1', 'Q2', 'Q3', 'Q4')),
                year INTEGER NOT NULL CHECK(year BETWEEN 2019 AND 2030),
                revenue_cr REAL CHECK(revenue_cr >= 0),
                pat_cr REAL,
                eps REAL,
                opm REAL CHECK(opm BETWEEN -100 AND 100),
                npm REAL CHECK(npm BETWEEN -100 AND 100),
                extraction_date DATE DEFAULT (date('now')),
                extraction_confidence REAL CHECK(extraction_confidence BETWEEN 0 AND 1),
                pdf_url TEXT,
                UNIQUE(bse_code, quarter, year)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bse_quarter_year ON historical_financials(bse_code, quarter, year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_year_quarter ON historical_financials(year, quarter)")

        conn.commit()
        conn.close()

    def query_earnings_announcements(self, start_date: str, end_date: str) -> List[Dict]:
        """AC1.4.2: Query earnings announcements from earnings_calendar.db"""
        if not os.path.exists(self.earnings_db_path):
            logger.warning(f"Earnings calendar database not found: {self.earnings_db_path}")
            return []

        conn = sqlite3.connect(self.earnings_db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT bse_code, announcement_date, pdf_url
                FROM earnings
                WHERE announcement_date BETWEEN ? AND ?
            """, (start_date, end_date))

            rows = cursor.fetchall()
            conn.close()

            announcements = []
            for bse_code, announcement_date_str, pdf_url in rows:
                announcement_date = datetime.strptime(announcement_date_str, "%Y-%m-%d").date()
                quarter = self.identify_quarter(announcement_date)
                year = announcement_date.year

                announcements.append({
                    "bse_code": bse_code,
                    "quarter": quarter,
                    "year": year,
                    "pdf_url": pdf_url,
                    "announcement_date": announcement_date_str
                })

            logger.info(f"Found {len(announcements)} earnings announcements")
            return announcements

        except Exception as e:
            logger.error(f"Error querying earnings: {e}")
            conn.close()
            return []

    def identify_quarter(self, announcement_date: date) -> str:
        """AC1.4.2: Identify fiscal quarter from announcement date"""
        month = announcement_date.month

        if month in [7, 8]:
            return 'Q1'
        elif month in [10, 11]:
            return 'Q2'
        elif month in [1, 2]:
            return 'Q3'
        elif month in [4, 5, 6]:
            return 'Q4'
        else:
            if month == 9:
                return 'Q2'
            elif month == 12:
                return 'Q3'
            elif month == 3:
                return 'Q4'
            else:
                return 'Q1'

    def should_extract(self, bse_code: str, quarter: str, year: int) -> bool:
        """AC1.4.3: Check if extraction is needed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT extraction_confidence
            FROM historical_financials
            WHERE bse_code=? AND quarter=? AND year=?
        """, (bse_code, quarter, year))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return True

        confidence = row[0]
        return confidence < 0.7

    def download_pdf(self, pdf_url: str, bse_code: str, quarter: str, year: int) -> Optional[str]:
        """AC1.4.3: Download PDF with caching"""
        cached_filename = f"{bse_code}_{quarter}_{year}.pdf"
        cached_path = self.cache_dir / cached_filename

        if cached_path.exists() and cached_path.stat().st_size > 0:
            return str(cached_path)

        try:
            import requests
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            cached_path.write_bytes(response.content)
            return str(cached_path)
        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            self.log_extraction_failure(bse_code, "", quarter, year, pdf_url, "PDF_DOWNLOAD_FAILED", str(e))
            return None

    def extract_from_pdf(self, pdf_path: str, bse_code: str, quarter: str, year: int) -> Optional[FinancialData]:
        """AC1.4.1, AC1.4.3: Extract financial data from PDF"""
        try:
            from agents.indian_pdf_extractor import extract_financial_data
            data = extract_financial_data(pdf_path, bse_code, quarter, year)
            return data
        except ImportError:
            logger.warning("indian_pdf_extractor not found")
            return None
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            self.log_extraction_failure(bse_code, "", quarter, year, "", "EXTRACTION_ERROR", str(e))
            return None

    def validate_financial_data(self, data: FinancialData) -> ValidationResult:
        """AC1.4.7: Validate extracted financial data"""
        failed_checks = []

        if data.revenue_cr <= 0:
            failed_checks.append("revenue_positive")

        if not (-100 <= data.opm <= 100):
            failed_checks.append("opm_bounds")

        if not (-100 <= data.npm <= 100):
            failed_checks.append("npm_bounds")

        adjusted_confidence = 0.5 if failed_checks else data.extraction_confidence

        return ValidationResult(
            is_valid=len(failed_checks) == 0,
            failed_checks=failed_checks,
            adjusted_confidence=adjusted_confidence
        )

    def store_financial_data(self, data: FinancialData, bse_code: str, quarter: str, year: int, pdf_url: str) -> bool:
        """AC1.4.4: Store extracted data in database"""
        validation = self.validate_financial_data(data)
        confidence = validation.adjusted_confidence

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO historical_financials
                (bse_code, quarter, year, revenue_cr, pat_cr, eps, opm, npm, extraction_confidence, pdf_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (bse_code, quarter, year, data.revenue_cr, data.pat_cr, data.eps, data.opm, data.npm, confidence, pdf_url))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            return False

    def log_extraction_failure(self, bse_code: str, company_name: str, quarter: str, year: int, pdf_url: str, error_type: str, error_message: str):
        """AC1.4.6: Log extraction failure to CSV"""
        import csv

        os.makedirs(os.path.dirname(self.failure_log_path), exist_ok=True)
        file_exists = os.path.exists(self.failure_log_path)

        with open(self.failure_log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['bse_code', 'company_name', 'quarter', 'year', 'pdf_url', 'error_type', 'error_message', 'attempted_at'])

            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'bse_code': bse_code,
                'company_name': company_name,
                'quarter': quarter,
                'year': year,
                'pdf_url': pdf_url,
                'error_type': error_type,
                'error_message': error_message,
                'attempted_at': datetime.now().isoformat()
            })

    def calculate_success_rate(self) -> float:
        """AC1.4.5: Calculate extraction success rate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM historical_financials")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM historical_financials WHERE extraction_confidence >= 0.7")
        successful = cursor.fetchone()[0]

        conn.close()

        return (successful / total * 100) if total > 0 else 0.0

    def meets_success_target(self) -> bool:
        """AC1.4.5: Check if success rate meets ≥80% target"""
        return self.calculate_success_rate() >= 80.0

    def analyze_failures(self) -> FailureAnalysisReport:
        """AC1.4.6: Analyze extraction failures"""
        import csv

        if not os.path.exists(self.failure_log_path):
            return FailureAnalysisReport(0, {}, [])

        by_error_type = {}
        company_failures = {}

        with open(self.failure_log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                error_type = row['error_type']
                bse_code = row['bse_code']
                by_error_type[error_type] = by_error_type.get(error_type, 0) + 1
                company_failures[bse_code] = company_failures.get(bse_code, 0) + 1

        companies_high_failure = [{"bse_code": bse, "failure_count": cnt} for bse, cnt in company_failures.items() if cnt > 5]

        return FailureAnalysisReport(sum(by_error_type.values()), by_error_type, companies_high_failure)

    def extract_all_financials(self, start_date: str, end_date: str) -> ExtractionReport:
        """AC1.4.3: Extract financial data for all earnings in date range"""
        start_time = time.time()

        announcements = self.query_earnings_announcements(start_date, end_date)

        total_attempted = 0
        total_successful = 0
        total_failed = 0

        for announcement in announcements:
            bse_code = announcement['bse_code']
            quarter = announcement['quarter']
            year = announcement['year']
            pdf_url = announcement['pdf_url']

            if not self.should_extract(bse_code, quarter, year):
                continue

            total_attempted += 1

            pdf_path = self.download_pdf(pdf_url, bse_code, quarter, year)
            if pdf_path is None:
                total_failed += 1
                continue

            data = self.extract_from_pdf(pdf_path, bse_code, quarter, year)
            if data is None:
                total_failed += 1
                continue

            success = self.store_financial_data(data, bse_code, quarter, year, pdf_url)
            if success:
                total_successful += 1
            else:
                total_failed += 1

        duration_seconds = time.time() - start_time
        success_rate = (total_successful / total_attempted * 100) if total_attempted > 0 else 0.0

        failure_report = self.analyze_failures()

        return ExtractionReport(total_attempted, total_successful, total_failed, success_rate, duration_seconds, failure_report.by_error_type)


def extract_financial_data(pdf_path: str, bse_code: str, quarter: str, year: int) -> Optional[FinancialData]:
    """AC1.4.1: Wrapper function for indian_pdf_extractor compatibility"""
    logger.warning("extract_financial_data is a placeholder")
    return None
