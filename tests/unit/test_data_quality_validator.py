"""
Unit tests for Story 1.6: DataQualityValidator

TDD Phase: RED (write tests first)
Target: ≥90% test coverage

Test Coverage:
- AC1.6.1: DataQualityValidator class and ValidationReport
- AC1.6.2: Check 1 - ≥200,000 labeled samples
- AC1.6.3: Check 2 - Class distribution 5-15%
- AC1.6.4: Check 3 - ≥80% companies with complete financials
- AC1.6.5: Check 4 - ≥95% price data completeness
- AC1.6.6: Check 5 - ≥80% BSE-NSE mapping coverage
- AC1.6.7: Generate comprehensive validation report
- AC1.6.8: Provide actionable remediation steps
"""

import pytest
import sqlite3
import os
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, Mock


class TestDataQualityValidatorInitialization:
    """Test DataQualityValidator class initialization"""

    def test_validator_class_exists(self):
        """AC1.6.1: Verify DataQualityValidator class can be imported"""
        from agents.ml.ml_data_collector import DataQualityValidator
        assert DataQualityValidator is not None

    def test_validator_instantiation(self, tmp_path):
        """AC1.6.1: Test DataQualityValidator can be instantiated with db_paths"""
        from agents.ml.ml_data_collector import DataQualityValidator

        db_paths = {
            'upper_circuits': str(tmp_path / 'upper_circuits.db'),
            'financials': str(tmp_path / 'financials.db'),
            'price_movements': str(tmp_path / 'price_movements.db'),
            'bse_nse_mapping': str(tmp_path / 'mapping.db'),
            'master_stock_list': str(tmp_path / 'master.db')
        }

        validator = DataQualityValidator(db_paths=db_paths)

        assert validator.db_paths == db_paths

    def test_validation_report_dataclass_exists(self):
        """AC1.6.1: Verify ValidationReport dataclass structure"""
        from agents.ml.ml_data_collector import ValidationReport

        report = ValidationReport(
            timestamp=datetime.now(),
            checks_passed=4,
            checks_failed=1,
            total_samples=200000,
            usable_companies=4000,
            estimated_model_f1=0.68,
            checks=[],
            remediation_steps=[]
        )

        assert report.checks_passed == 4
        assert report.checks_failed == 1
        assert report.total_samples == 200000

    def test_check_result_dataclass_exists(self):
        """AC1.6.1: Verify CheckResult dataclass structure"""
        from agents.ml.ml_data_collector import CheckResult

        check = CheckResult(
            check_name="Labeled Samples Count",
            status="PASS",
            metric_value=205432.0,
            threshold=200000.0,
            passed=True,
            details="Sufficient samples for training"
        )

        assert check.check_name == "Labeled Samples Count"
        assert check.passed is True


class TestLabeledSamplesCountCheck:
    """Test Check 1: Verify ≥200,000 labeled samples (AC1.6.2)"""

    def test_labeled_samples_check_pass(self, tmp_path):
        """AC1.6.2: Check passes when samples ≥ 200,000"""
        from agents.ml.ml_data_collector import DataQualityValidator

        # Create mock database
        db_path = tmp_path / 'upper_circuits.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                label_id INTEGER PRIMARY KEY,
                bse_code TEXT,
                earnings_date DATE,
                label INTEGER
            )
        """)

        # Insert 205,432 samples
        for i in range(205432):
            cursor.execute("INSERT INTO upper_circuit_labels (bse_code, earnings_date, label) VALUES (?, ?, ?)",
                         (f"50{i % 1000:04d}", '2024-01-01', i % 10 < 1))

        conn.commit()
        conn.close()

        db_paths = {'upper_circuits': str(db_path)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_labeled_samples_count()

        assert check_result.passed is True
        assert check_result.metric_value >= 200000
        assert check_result.status == "PASS"
        assert "Sufficient samples" in check_result.details

    def test_labeled_samples_check_fail(self, tmp_path):
        """AC1.6.2: Check fails when samples < 200,000"""
        from agents.ml.ml_data_collector import DataQualityValidator

        # Create mock database
        db_path = tmp_path / 'upper_circuits.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                label_id INTEGER PRIMARY KEY,
                bse_code TEXT,
                label INTEGER
            )
        """)

        # Insert only 185,000 samples
        for i in range(185000):
            cursor.execute("INSERT INTO upper_circuit_labels (bse_code, label) VALUES (?, ?)",
                         (f"50{i % 1000:04d}", i % 10 < 1))

        conn.commit()
        conn.close()

        db_paths = {'upper_circuits': str(db_path)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_labeled_samples_count()

        assert check_result.passed is False
        assert check_result.metric_value < 200000
        assert check_result.status == "FAIL"
        assert "below threshold" in check_result.details.lower()


class TestClassDistributionCheck:
    """Test Check 2: Verify class distribution 5-15% (AC1.6.3)"""

    def test_class_distribution_check_pass(self, tmp_path):
        """AC1.6.3: Check passes when 5% ≤ positive ratio ≤ 15%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        db_path = tmp_path / 'upper_circuits.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE upper_circuit_labels (
                label_id INTEGER PRIMARY KEY,
                label INTEGER
            )
        """)

        # 8.3% positive (830 out of 10,000)
        for i in range(10000):
            cursor.execute("INSERT INTO upper_circuit_labels (label) VALUES (?)", (1 if i < 830 else 0,))

        conn.commit()
        conn.close()

        db_paths = {'upper_circuits': str(db_path)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_class_distribution()

        assert check_result.passed is True
        assert 5.0 <= check_result.metric_value <= 15.0
        assert check_result.status == "PASS"

    def test_class_distribution_too_low(self, tmp_path):
        """AC1.6.3: Check fails when positive ratio < 5%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        db_path = tmp_path / 'upper_circuits.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE upper_circuit_labels (label_id INTEGER PRIMARY KEY, label INTEGER)")

        # 3.2% positive (320 out of 10,000)
        for i in range(10000):
            cursor.execute("INSERT INTO upper_circuit_labels (label) VALUES (?)", (1 if i < 320 else 0,))

        conn.commit()
        conn.close()

        db_paths = {'upper_circuits': str(db_path)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_class_distribution()

        assert check_result.passed is False
        assert check_result.metric_value < 5.0
        assert "imbalance" in check_result.details.lower()

    def test_class_distribution_too_high(self, tmp_path):
        """AC1.6.3: Check fails when positive ratio > 15%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        db_path = tmp_path / 'upper_circuits.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE upper_circuit_labels (label_id INTEGER PRIMARY KEY, label INTEGER)")

        # 18.5% positive (1850 out of 10,000)
        for i in range(10000):
            cursor.execute("INSERT INTO upper_circuit_labels (label) VALUES (?)", (1 if i < 1850 else 0,))

        conn.commit()
        conn.close()

        db_paths = {'upper_circuits': str(db_path)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_class_distribution()

        assert check_result.passed is False
        assert check_result.metric_value > 15.0


class TestFinancialDataCoverageCheck:
    """Test Check 3: Verify ≥80% companies with complete financials (AC1.6.4)"""

    def test_financial_coverage_check_pass(self, tmp_path):
        """AC1.6.4: Check passes when coverage ≥ 80%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        financials_db = tmp_path / 'financials.db'
        master_db = tmp_path / 'master.db'

        # Create financials database
        conn = sqlite3.connect(str(financials_db))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE historical_financials (
                bse_code TEXT,
                quarter TEXT,
                year INTEGER
            )
        """)

        # 4,000 companies with 12+ quarters
        for bse_code in range(4000):
            for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                for year in [2022, 2023, 2024]:
                    cursor.execute("INSERT INTO historical_financials (bse_code, quarter, year) VALUES (?, ?, ?)",
                                 (f"50{bse_code:04d}", quarter, year))

        conn.commit()
        conn.close()

        # Create master database
        conn = sqlite3.connect(str(master_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE master_stock_list (bse_code TEXT PRIMARY KEY)")

        for i in range(5000):
            cursor.execute("INSERT INTO master_stock_list (bse_code) VALUES (?)", (f"50{i:04d}",))

        conn.commit()
        conn.close()

        db_paths = {'financials': str(financials_db), 'master_stock_list': str(master_db)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_financial_data_coverage()

        assert check_result.passed is True
        assert check_result.metric_value >= 80.0
        assert check_result.status == "PASS"

    def test_financial_coverage_check_fail(self, tmp_path):
        """AC1.6.4: Check fails when coverage < 80%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        financials_db = tmp_path / 'financials.db'
        master_db = tmp_path / 'master.db'

        # Create financials database
        conn = sqlite3.connect(str(financials_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE historical_financials (bse_code TEXT, quarter TEXT, year INTEGER)")

        # Only 3,625 companies with 12+ quarters (72.5%)
        for bse_code in range(3625):
            for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                for year in [2022, 2023, 2024]:
                    cursor.execute("INSERT INTO historical_financials (bse_code, quarter, year) VALUES (?, ?, ?)",
                                 (f"50{bse_code:04d}", quarter, year))

        conn.commit()
        conn.close()

        # Create master database
        conn = sqlite3.connect(str(master_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE master_stock_list (bse_code TEXT PRIMARY KEY)")

        for i in range(5000):
            cursor.execute("INSERT INTO master_stock_list (bse_code) VALUES (?)", (f"50{i:04d}",))

        conn.commit()
        conn.close()

        db_paths = {'financials': str(financials_db), 'master_stock_list': str(master_db)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_financial_data_coverage()

        assert check_result.passed is False
        assert check_result.metric_value < 80.0


class TestPriceDataCompletenessCheck:
    """Test Check 4: Verify ≥95% price data completeness (AC1.6.5)"""

    def test_price_completeness_check_pass(self, tmp_path):
        """AC1.6.5: Check passes when avg completeness ≥ 95%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        db_path = tmp_path / 'price_movements.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE price_movements (
                bse_code TEXT,
                date DATE
            )
        """)

        # 100 companies with 950/975 dates each (97.4% completeness)
        from datetime import datetime, timedelta
        for bse_code in range(100):
            for day_offset in range(950):
                date = (datetime(2022, 1, 1) + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO price_movements (bse_code, date) VALUES (?, ?)",
                             (f"50{bse_code:04d}", date))

        conn.commit()
        conn.close()

        db_paths = {'price_movements': str(db_path)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_price_data_completeness()

        assert check_result.passed is True
        assert check_result.metric_value >= 95.0

    def test_price_completeness_check_fail(self, tmp_path):
        """AC1.6.5: Check fails when avg completeness < 95%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        db_path = tmp_path / 'price_movements.db'
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE price_movements (bse_code TEXT, date DATE)")

        # 100 companies with 890/975 dates each (91.3% completeness)
        from datetime import datetime, timedelta
        for bse_code in range(100):
            for day_offset in range(890):
                date = (datetime(2022, 1, 1) + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO price_movements (bse_code, date) VALUES (?, ?)",
                             (f"50{bse_code:04d}", date))

        conn.commit()
        conn.close()

        db_paths = {'price_movements': str(db_path)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_price_data_completeness()

        assert check_result.passed is False
        assert check_result.metric_value < 95.0


class TestBSENSEMappingCoverageCheck:
    """Test Check 5: Verify ≥80% BSE-NSE mapping coverage (AC1.6.6)"""

    def test_mapping_coverage_check_pass(self, tmp_path):
        """AC1.6.6: Check passes when mapping coverage ≥ 80%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        mapping_db = tmp_path / 'mapping.db'
        master_db = tmp_path / 'master.db'

        # Create mapping database
        conn = sqlite3.connect(str(mapping_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE mappings (bse_code TEXT PRIMARY KEY, nse_symbol TEXT)")

        for i in range(4100):  # 4100/5000 = 82%
            cursor.execute("INSERT INTO mappings (bse_code, nse_symbol) VALUES (?, ?)",
                         (f"50{i:04d}", f"SYM{i}"))

        conn.commit()
        conn.close()

        # Create master database
        conn = sqlite3.connect(str(master_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE master_stock_list (bse_code TEXT PRIMARY KEY)")

        for i in range(5000):
            cursor.execute("INSERT INTO master_stock_list (bse_code) VALUES (?)", (f"50{i:04d}",))

        conn.commit()
        conn.close()

        db_paths = {'bse_nse_mapping': str(mapping_db), 'master_stock_list': str(master_db)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_bse_nse_mapping_coverage()

        assert check_result.passed is True
        assert check_result.metric_value >= 80.0

    def test_mapping_coverage_check_fail(self, tmp_path):
        """AC1.6.6: Check fails when mapping coverage < 80%"""
        from agents.ml.ml_data_collector import DataQualityValidator

        mapping_db = tmp_path / 'mapping.db'
        master_db = tmp_path / 'master.db'

        # Create mapping database
        conn = sqlite3.connect(str(mapping_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE mappings (bse_code TEXT PRIMARY KEY, nse_symbol TEXT)")

        for i in range(3825):  # 3825/5000 = 76.5%
            cursor.execute("INSERT INTO mappings (bse_code, nse_symbol) VALUES (?, ?)",
                         (f"50{i:04d}", f"SYM{i}"))

        conn.commit()
        conn.close()

        # Create master database
        conn = sqlite3.connect(str(master_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE master_stock_list (bse_code TEXT PRIMARY KEY)")

        for i in range(5000):
            cursor.execute("INSERT INTO master_stock_list (bse_code) VALUES (?)", (f"50{i:04d}",))

        conn.commit()
        conn.close()

        db_paths = {'bse_nse_mapping': str(mapping_db), 'master_stock_list': str(master_db)}
        validator = DataQualityValidator(db_paths=db_paths)

        check_result = validator.check_bse_nse_mapping_coverage()

        assert check_result.passed is False
        assert check_result.metric_value < 80.0


class TestValidationWorkflow:
    """Test full validation workflow (AC1.6.7)"""

    def test_validate_training_readiness_all_pass(self, tmp_path):
        """AC1.6.7: All checks pass → status PASS"""
        from agents.ml.ml_data_collector import DataQualityValidator

        # Create mock databases with passing data
        db_paths = self._create_passing_databases(tmp_path)

        validator = DataQualityValidator(db_paths=db_paths)
        report = validator.validate_training_readiness()

        assert report.checks_passed == 5
        assert report.checks_failed == 0
        assert len(report.checks) == 5
        assert all(check.passed for check in report.checks)
        assert report.estimated_model_f1 >= 0.70

    def test_validate_training_readiness_some_fail(self, tmp_path):
        """AC1.6.7: Some checks fail → status FAIL with remediation"""
        from agents.ml.ml_data_collector import DataQualityValidator

        # Create mock databases with failing data
        db_paths = self._create_failing_databases(tmp_path)

        validator = DataQualityValidator(db_paths=db_paths)
        report = validator.validate_training_readiness()

        assert report.checks_failed > 0
        assert len(report.remediation_steps) > 0
        assert report.estimated_model_f1 < 0.70

    def _create_passing_databases(self, tmp_path):
        """Helper: Create databases with all checks passing"""
        # Upper circuits DB (205K samples, 8.3% positive)
        uc_db = tmp_path / 'upper_circuits.db'
        conn = sqlite3.connect(str(uc_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE upper_circuit_labels (label_id INTEGER PRIMARY KEY, label INTEGER)")
        for i in range(205000):
            cursor.execute("INSERT INTO upper_circuit_labels (label) VALUES (?)", (1 if i < 17000 else 0,))
        conn.commit()
        conn.close()

        # Financials DB (4100/5000 = 82%)
        fin_db = tmp_path / 'financials.db'
        conn = sqlite3.connect(str(fin_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE historical_financials (bse_code TEXT, quarter TEXT, year INTEGER)")
        for bse_code in range(4100):
            for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                for year in [2022, 2023, 2024]:
                    cursor.execute("INSERT INTO historical_financials (bse_code, quarter, year) VALUES (?, ?, ?)",
                                 (f"50{bse_code:04d}", quarter, year))
        conn.commit()
        conn.close()

        # Price movements DB (96% completeness)
        from datetime import datetime, timedelta
        price_db = tmp_path / 'price_movements.db'
        conn = sqlite3.connect(str(price_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE price_movements (bse_code TEXT, date DATE)")
        for bse_code in range(100):
            for day_offset in range(935):  # 935/975 = 95.9%
                date = (datetime(2022, 1, 1) + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO price_movements (bse_code, date) VALUES (?, ?)",
                             (f"50{bse_code:04d}", date))
        conn.commit()
        conn.close()

        # Mapping DB (82%)
        map_db = tmp_path / 'mapping.db'
        conn = sqlite3.connect(str(map_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE mappings (bse_code TEXT PRIMARY KEY, nse_symbol TEXT)")
        for i in range(4100):
            cursor.execute("INSERT INTO mappings (bse_code, nse_symbol) VALUES (?, ?)",
                         (f"50{i:04d}", f"SYM{i}"))
        conn.commit()
        conn.close()

        # Master list DB
        master_db = tmp_path / 'master.db'
        conn = sqlite3.connect(str(master_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE master_stock_list (bse_code TEXT PRIMARY KEY)")
        for i in range(5000):
            cursor.execute("INSERT INTO master_stock_list (bse_code) VALUES (?)", (f"50{i:04d}",))
        conn.commit()
        conn.close()

        return {
            'upper_circuits': str(uc_db),
            'financials': str(fin_db),
            'price_movements': str(price_db),
            'bse_nse_mapping': str(map_db),
            'master_stock_list': str(master_db)
        }

    def _create_failing_databases(self, tmp_path):
        """Helper: Create databases with failing checks"""
        # Create a failing upper circuits DB (below threshold)
        uc_db = tmp_path / 'upper_circuits_fail.db'
        conn = sqlite3.connect(str(uc_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE upper_circuit_labels (label_id INTEGER PRIMARY KEY, label INTEGER)")
        for i in range(185000):  # Below threshold
            cursor.execute("INSERT INTO upper_circuit_labels (label) VALUES (?)", (1 if i < 6000 else 0,))
        conn.commit()
        conn.close()

        # Create other databases (same as passing but with different paths)
        from datetime import datetime, timedelta

        # Financials DB
        fin_db = tmp_path / 'financials_fail.db'
        conn = sqlite3.connect(str(fin_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE historical_financials (bse_code TEXT, quarter TEXT, year INTEGER)")
        for bse_code in range(4100):
            for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                for year in [2022, 2023, 2024]:
                    cursor.execute("INSERT INTO historical_financials (bse_code, quarter, year) VALUES (?, ?, ?)",
                                 (f"50{bse_code:04d}", quarter, year))
        conn.commit()
        conn.close()

        # Price movements DB
        price_db = tmp_path / 'price_movements_fail.db'
        conn = sqlite3.connect(str(price_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE price_movements (bse_code TEXT, date DATE)")
        for bse_code in range(100):
            for day_offset in range(935):
                date = (datetime(2022, 1, 1) + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO price_movements (bse_code, date) VALUES (?, ?)",
                             (f"50{bse_code:04d}", date))
        conn.commit()
        conn.close()

        # Mapping DB
        map_db = tmp_path / 'mapping_fail.db'
        conn = sqlite3.connect(str(map_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE mappings (bse_code TEXT PRIMARY KEY, nse_symbol TEXT)")
        for i in range(4100):
            cursor.execute("INSERT INTO mappings (bse_code, nse_symbol) VALUES (?, ?)",
                         (f"50{i:04d}", f"SYM{i}"))
        conn.commit()
        conn.close()

        # Master list DB
        master_db = tmp_path / 'master_fail.db'
        conn = sqlite3.connect(str(master_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE master_stock_list (bse_code TEXT PRIMARY KEY)")
        for i in range(5000):
            cursor.execute("INSERT INTO master_stock_list (bse_code) VALUES (?)", (f"50{i:04d}",))
        conn.commit()
        conn.close()

        return {
            'upper_circuits': str(uc_db),
            'financials': str(fin_db),
            'price_movements': str(price_db),
            'bse_nse_mapping': str(map_db),
            'master_stock_list': str(master_db)
        }


class TestRemediationSteps:
    """Test remediation step generation (AC1.6.8)"""

    def test_generate_remediation_for_low_samples(self, tmp_path):
        """AC1.6.8: Generate remediation when sample count is low"""
        from agents.ml.ml_data_collector import DataQualityValidator, CheckResult

        validator = DataQualityValidator(db_paths={})

        failed_checks = [
            CheckResult(
                check_name="Labeled Samples Count",
                status="FAIL",
                metric_value=185000.0,
                threshold=200000.0,
                passed=False,
                details="15,000 samples below threshold"
            )
        ]

        remediation_steps = validator.generate_remediation_steps(failed_checks)

        assert len(remediation_steps) > 0
        assert any("Extend date range" in step or "2021" in step for step in remediation_steps)

    def test_prioritize_critical_failures(self, tmp_path):
        """AC1.6.8: Priority 1 failures listed first"""
        from agents.ml.ml_data_collector import DataQualityValidator, CheckResult

        validator = DataQualityValidator(db_paths={})

        failed_checks = [
            CheckResult("Price Completeness", "FAIL", 91.0, 95.0, False, ""),
            CheckResult("Labeled Samples", "FAIL", 95000.0, 200000.0, False, "Critical"),  # Critical
        ]

        remediation_steps = validator.generate_remediation_steps(failed_checks)

        # Priority 1 (critical) should come first
        assert "Priority 1" in remediation_steps[0] or "CRITICAL" in remediation_steps[0].upper()


class TestReportGeneration:
    """Test report generation and saving (AC1.6.7)"""

    def test_save_report_to_file(self, tmp_path):
        """AC1.6.7: Save report to specified file path"""
        from agents.ml.ml_data_collector import DataQualityValidator, ValidationReport, CheckResult
        from datetime import datetime

        report = ValidationReport(
            timestamp=datetime.now(),
            checks_passed=4,
            checks_failed=1,
            total_samples=205000,
            usable_companies=4100,
            estimated_model_f1=0.68,
            checks=[],
            remediation_steps=["Step 1", "Step 2"]
        )

        validator = DataQualityValidator(db_paths={})
        output_path = str(tmp_path / "report.txt")

        validator.save_report(report, output_path)

        assert os.path.exists(output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        assert "DATA QUALITY VALIDATION REPORT" in content
        assert "Passed: 4" in content
        assert "Failed: 1" in content

    def test_report_format_matches_spec(self, tmp_path):
        """AC1.6.7: Report format matches specification"""
        from agents.ml.ml_data_collector import DataQualityValidator

        db_paths = TestValidationWorkflow()._create_passing_databases(tmp_path)
        validator = DataQualityValidator(db_paths=db_paths)

        report = validator.validate_training_readiness()
        output_path = str(tmp_path / "report.txt")
        validator.save_report(report, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        # Verify key sections
        assert "========================================" in content
        assert "CHECK RESULTS:" in content
        assert "OVERALL STATUS:" in content
        assert "USABLE DATA:" in content
        assert "ESTIMATED MODEL PERFORMANCE:" in content
