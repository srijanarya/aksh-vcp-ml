"""
Data Validation Database Schema and Manager
Persists validation results, confidence scores, and discrepancy logs
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.fiscal_year_utils import DataTimestamp


class ValidationDatabase:
    """
    Manages persistent storage of data validation results
    """

    def __init__(self, db_path: str = "data_validation.db"):
        self.db_path = db_path
        self.conn = None
        self.initialize_database()

    def initialize_database(self):
        """Create database tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Source tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT NOT NULL,
                source_name TEXT NOT NULL,
                fetch_timestamp TIMESTAMP NOT NULL,
                data_json TEXT,
                status TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_code, source_name, fetch_timestamp)
            )
        """)

        # Validation results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                validation_timestamp TIMESTAMP NOT NULL,
                sources_data TEXT,  -- JSON with source values
                discrepancy_pct REAL,
                confidence_score REAL,
                recommended_value REAL,
                reason TEXT,
                fiscal_quarter TEXT,
                fiscal_year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Confidence scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidence_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT NOT NULL,
                overall_confidence REAL,
                data_quality TEXT,
                timestamp TIMESTAMP NOT NULL,
                validation_summary TEXT,  -- JSON with detailed scores
                recommendations TEXT,  -- JSON array of recommendations
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Discrepancy logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discrepancy_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                source_1 TEXT,
                value_1 REAL,
                source_2 TEXT,
                value_2 REAL,
                discrepancy_pct REAL,
                timestamp TIMESTAMP NOT NULL,
                resolution TEXT,  -- How it was resolved
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Data quality metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT NOT NULL,
                date DATE NOT NULL,
                sources_available INTEGER,
                metrics_validated INTEGER,
                avg_confidence REAL,
                high_confidence_count INTEGER,
                medium_confidence_count INTEGER,
                low_confidence_count INTEGER,
                failed_validations INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_code, date)
            )
        """)

        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_company_timestamp
            ON source_tracking(company_code, fetch_timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_validation_company_timestamp
            ON validation_results(company_code, validation_timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_confidence_company
            ON confidence_scores(company_code, timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_discrepancy_company
            ON discrepancy_logs(company_code, timestamp DESC)
        """)

        self.conn.commit()

    def save_source_data(self, company_code: str, source_name: str, data: Dict) -> int:
        """
        Save data from a specific source

        Returns:
            ID of the saved record
        """
        cursor = self.conn.cursor()

        timestamp = data.get('fetch_timestamp', {}).get('timestamp', datetime.now().isoformat())
        status = data.get('status', 'unknown')
        error_message = data.get('error', None)

        # Convert data to JSON
        data_json = json.dumps(data)

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO source_tracking
                (company_code, source_name, fetch_timestamp, data_json, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (company_code, source_name, timestamp, data_json, status, error_message))

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            print(f"Error saving source data: {e}")
            self.conn.rollback()
            return -1

    def save_validation_result(self, validation_result: Dict) -> int:
        """
        Save a validation result

        Returns:
            ID of the saved record
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO validation_results
                (company_code, metric_name, validation_timestamp, sources_data,
                 discrepancy_pct, confidence_score, recommended_value, reason,
                 fiscal_quarter, fiscal_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                validation_result.get('company_code'),
                validation_result.get('metric'),
                validation_result.get('timestamp', {}).get('timestamp', datetime.now().isoformat()),
                json.dumps(validation_result.get('sources', {})),
                validation_result.get('discrepancy_pct'),
                validation_result.get('confidence_score'),
                validation_result.get('recommended_value'),
                validation_result.get('reason'),
                validation_result.get('timestamp', {}).get('fiscal_quarter'),
                validation_result.get('timestamp', {}).get('fiscal_year')
            ))

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            print(f"Error saving validation result: {e}")
            self.conn.rollback()
            return -1

    def save_confidence_score(self, company_code: str, confidence_data: Dict) -> int:
        """
        Save overall confidence score for a company

        Returns:
            ID of the saved record
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO confidence_scores
                (company_code, overall_confidence, data_quality, timestamp,
                 validation_summary, recommendations)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                company_code,
                confidence_data.get('overall_confidence'),
                confidence_data.get('data_quality'),
                confidence_data.get('validation_timestamp', {}).get('timestamp', datetime.now().isoformat()),
                json.dumps(confidence_data.get('validation_results', [])),
                json.dumps(confidence_data.get('recommendations', []))
            ))

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            print(f"Error saving confidence score: {e}")
            self.conn.rollback()
            return -1

    def log_discrepancy(self, company_code: str, metric: str,
                       source1: str, value1: float,
                       source2: str, value2: float,
                       resolution: str = None) -> int:
        """
        Log a discrepancy between sources

        Returns:
            ID of the logged discrepancy
        """
        cursor = self.conn.cursor()

        # Calculate discrepancy percentage
        if value1 and value2:
            avg_value = (abs(value1) + abs(value2)) / 2
            discrepancy_pct = abs(value1 - value2) / avg_value * 100
        else:
            discrepancy_pct = 100

        try:
            cursor.execute("""
                INSERT INTO discrepancy_logs
                (company_code, metric_name, source_1, value_1, source_2, value_2,
                 discrepancy_pct, timestamp, resolution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_code, metric, source1, value1, source2, value2,
                discrepancy_pct, datetime.now().isoformat(), resolution
            ))

            self.conn.commit()
            return cursor.lastrowid

        except Exception as e:
            print(f"Error logging discrepancy: {e}")
            self.conn.rollback()
            return -1

    def save_daily_quality_metrics(self, company_code: str, metrics: Dict):
        """
        Save daily data quality metrics

        Args:
            company_code: Company identifier
            metrics: Quality metrics dictionary
        """
        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO data_quality_metrics
                (company_code, date, sources_available, metrics_validated,
                 avg_confidence, high_confidence_count, medium_confidence_count,
                 low_confidence_count, failed_validations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_code,
                datetime.now().date().isoformat(),
                metrics.get('sources_available', 0),
                metrics.get('metrics_validated', 0),
                metrics.get('avg_confidence', 0),
                metrics.get('high_confidence_count', 0),
                metrics.get('medium_confidence_count', 0),
                metrics.get('low_confidence_count', 0),
                metrics.get('failed_validations', 0)
            ))

            self.conn.commit()

        except Exception as e:
            print(f"Error saving quality metrics: {e}")
            self.conn.rollback()

    def get_latest_validation(self, company_code: str, metric: str = None) -> Optional[Dict]:
        """
        Get the latest validation result for a company

        Args:
            company_code: Company identifier
            metric: Optional specific metric to retrieve

        Returns:
            Latest validation data or None
        """
        cursor = self.conn.cursor()

        if metric:
            query = """
                SELECT * FROM validation_results
                WHERE company_code = ? AND metric_name = ?
                ORDER BY validation_timestamp DESC
                LIMIT 1
            """
            cursor.execute(query, (company_code, metric))
        else:
            query = """
                SELECT * FROM validation_results
                WHERE company_code = ?
                ORDER BY validation_timestamp DESC
                LIMIT 1
            """
            cursor.execute(query, (company_code,))

        row = cursor.fetchone()
        if row:
            return self._row_to_dict(cursor, row)
        return None

    def get_confidence_history(self, company_code: str, days_back: int = 30) -> List[Dict]:
        """
        Get confidence score history for a company

        Args:
            company_code: Company identifier
            days_back: Number of days to look back

        Returns:
            List of confidence scores over time
        """
        cursor = self.conn.cursor()

        since_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        cursor.execute("""
            SELECT * FROM confidence_scores
            WHERE company_code = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        """, (company_code, since_date))

        return [self._row_to_dict(cursor, row) for row in cursor.fetchall()]

    def get_discrepancy_report(self, company_code: str = None,
                               threshold_pct: float = 10.0) -> List[Dict]:
        """
        Get discrepancies above a threshold

        Args:
            company_code: Optional company filter
            threshold_pct: Minimum discrepancy percentage

        Returns:
            List of significant discrepancies
        """
        cursor = self.conn.cursor()

        if company_code:
            query = """
                SELECT * FROM discrepancy_logs
                WHERE company_code = ? AND discrepancy_pct >= ?
                ORDER BY timestamp DESC
                LIMIT 100
            """
            cursor.execute(query, (company_code, threshold_pct))
        else:
            query = """
                SELECT * FROM discrepancy_logs
                WHERE discrepancy_pct >= ?
                ORDER BY timestamp DESC
                LIMIT 100
            """
            cursor.execute(query, (threshold_pct,))

        return [self._row_to_dict(cursor, row) for row in cursor.fetchall()]

    def get_quality_trends(self, company_code: str = None, days: int = 30) -> Dict:
        """
        Get data quality trends

        Args:
            company_code: Optional company filter
            days: Number of days to analyze

        Returns:
            Quality trend analysis
        """
        cursor = self.conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).date().isoformat()

        if company_code:
            query = """
                SELECT
                    AVG(avg_confidence) as avg_confidence,
                    AVG(sources_available) as avg_sources,
                    SUM(high_confidence_count) as total_high_conf,
                    SUM(medium_confidence_count) as total_medium_conf,
                    SUM(low_confidence_count) as total_low_conf,
                    SUM(failed_validations) as total_failures,
                    COUNT(DISTINCT date) as days_tracked
                FROM data_quality_metrics
                WHERE company_code = ? AND date >= ?
            """
            cursor.execute(query, (company_code, since_date))
        else:
            query = """
                SELECT
                    AVG(avg_confidence) as avg_confidence,
                    AVG(sources_available) as avg_sources,
                    SUM(high_confidence_count) as total_high_conf,
                    SUM(medium_confidence_count) as total_medium_conf,
                    SUM(low_confidence_count) as total_low_conf,
                    SUM(failed_validations) as total_failures,
                    COUNT(DISTINCT date) as days_tracked,
                    COUNT(DISTINCT company_code) as companies_tracked
                FROM data_quality_metrics
                WHERE date >= ?
            """
            cursor.execute(query, (since_date,))

        result = cursor.fetchone()
        if result:
            return self._row_to_dict(cursor, result)
        return {}

    def _row_to_dict(self, cursor, row) -> Dict:
        """Convert a database row to dictionary"""
        if not row:
            return {}

        columns = [description[0] for description in cursor.description]
        row_dict = dict(zip(columns, row))

        # Parse JSON fields
        json_fields = ['data_json', 'sources_data', 'validation_summary', 'recommendations']
        for field in json_fields:
            if field in row_dict and row_dict[field]:
                try:
                    row_dict[field] = json.loads(row_dict[field])
                except:
                    pass

        return row_dict

    def generate_quality_report(self, company_code: str = None) -> Dict:
        """
        Generate a comprehensive data quality report

        Args:
            company_code: Optional company filter

        Returns:
            Comprehensive quality report
        """
        report = {
            'generated_at': DataTimestamp.create_timestamp(),
            'report_type': 'company' if company_code else 'system-wide'
        }

        # Get quality trends
        report['quality_trends'] = self.get_quality_trends(company_code, days=30)

        # Get recent discrepancies
        report['significant_discrepancies'] = self.get_discrepancy_report(
            company_code, threshold_pct=15.0
        )

        if company_code:
            # Company-specific data
            report['company_code'] = company_code
            report['confidence_history'] = self.get_confidence_history(company_code, days_back=7)
            report['latest_validation'] = self.get_latest_validation(company_code)
        else:
            # System-wide statistics
            cursor = self.conn.cursor()

            # Get company coverage
            cursor.execute("""
                SELECT COUNT(DISTINCT company_code) as companies_validated
                FROM validation_results
                WHERE validation_timestamp >= datetime('now', '-7 days')
            """)
            result = cursor.fetchone()
            if result:
                report['companies_validated_week'] = result[0]

            # Get validation volume
            cursor.execute("""
                SELECT COUNT(*) as total_validations
                FROM validation_results
                WHERE validation_timestamp >= datetime('now', '-24 hours')
            """)
            result = cursor.fetchone()
            if result:
                report['validations_24h'] = result[0]

        return report

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Test the database
if __name__ == "__main__":
    db = ValidationDatabase("test_validation.db")

    print("Testing Validation Database")
    print("=" * 60)

    # Test saving source data
    source_data = {
        'fetch_timestamp': DataTimestamp.create_timestamp(),
        'status': 'success',
        'revenue_yoy': 15.5,
        'profit_yoy': 22.3
    }

    source_id = db.save_source_data("TCS", "BSE_DIRECT", source_data)
    print(f"Saved source data with ID: {source_id}")

    # Test saving validation result
    validation = {
        'company_code': 'TCS',
        'metric': 'revenue_yoy',
        'timestamp': DataTimestamp.create_timestamp(),
        'sources': {'BSE': 15.5, 'NSE': 15.2, 'Yahoo': 16.1},
        'discrepancy_pct': 3.5,
        'confidence_score': 85.0,
        'recommended_value': 15.6,
        'reason': 'Sources agree within tolerance'
    }

    validation_id = db.save_validation_result(validation)
    print(f"Saved validation result with ID: {validation_id}")

    # Test logging discrepancy
    discrepancy_id = db.log_discrepancy(
        "TCS", "profit_yoy",
        "Screener", -790.0,
        "BSE", 22.3,
        "BSE value used - Screener data likely erroneous"
    )
    print(f"Logged discrepancy with ID: {discrepancy_id}")

    # Test saving confidence score
    confidence_data = {
        'overall_confidence': 82.5,
        'data_quality': 'HIGH',
        'validation_timestamp': DataTimestamp.create_timestamp(),
        'validation_results': [validation],
        'recommendations': ['Data quality is high', 'Safe to use for analysis']
    }

    confidence_id = db.save_confidence_score("TCS", confidence_data)
    print(f"Saved confidence score with ID: {confidence_id}")

    # Test generating report
    print("\nGenerating Quality Report...")
    report = db.generate_quality_report("TCS")
    print(f"Report Type: {report['report_type']}")
    print(f"Generated At: {report['generated_at']['timestamp']}")

    db.close()
    print("\nDatabase test complete!")