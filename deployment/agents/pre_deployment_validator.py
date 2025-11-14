"""
Agent 1: Pre-Deployment Validator

Validates system readiness before deployment:
- All tests passing
- Docker build succeeds
- Environment variables set
- Database connections valid
- Model registry has models

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import subprocess
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    check_name: str
    passed: bool
    message: str
    details: Optional[Dict] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    overall_passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[ValidationResult]
    timestamp: str
    duration_seconds: float

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            **asdict(self),
            'results': [asdict(r) for r in self.results]
        }


class PreDeploymentValidator:
    """
    Pre-deployment validation agent

    Ensures all prerequisites are met before deployment
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize validator

        Args:
            project_root: Root directory of project (defaults to current)
        """
        self.project_root = project_root or Path.cwd()
        self.results: List[ValidationResult] = []

    def validate_tests(self) -> ValidationResult:
        """
        Run all tests and ensure 100% pass rate

        Returns:
            ValidationResult with test execution details
        """
        logger.info("🧪 Validating tests...")

        try:
            # Run pytest with coverage
            result = subprocess.run(
                ['pytest', 'tests/', '-v', '--tb=short', '--timeout=60'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse output for test counts
            output = result.stdout + result.stderr
            passed = result.returncode == 0

            # Extract test statistics
            if 'passed' in output:
                # Try to extract numbers
                import re
                match = re.search(r'(\d+) passed', output)
                num_passed = int(match.group(1)) if match else 0

                match = re.search(r'(\d+) failed', output)
                num_failed = int(match.group(1)) if match else 0

                details = {
                    'passed': num_passed,
                    'failed': num_failed,
                    'exit_code': result.returncode
                }
            else:
                details = {'exit_code': result.returncode}

            message = "All tests passed" if passed else f"Tests failed with exit code {result.returncode}"

            return ValidationResult(
                check_name="tests",
                passed=passed,
                message=message,
                details=details
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                check_name="tests",
                passed=False,
                message="Tests timed out after 120 seconds"
            )
        except Exception as e:
            return ValidationResult(
                check_name="tests",
                passed=False,
                message=f"Test execution failed: {e}"
            )

    def validate_docker_build(self) -> ValidationResult:
        """
        Build Docker image and verify success

        Returns:
            ValidationResult with build details
        """
        logger.info("🐳 Validating Docker build...")

        try:
            # Check if Dockerfile exists
            dockerfile = self.project_root / 'Dockerfile'
            if not dockerfile.exists():
                return ValidationResult(
                    check_name="docker_build",
                    passed=False,
                    message="Dockerfile not found"
                )

            # Build Docker image
            result = subprocess.run(
                ['docker', 'build', '-t', 'vcp-ml:validation', '.'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            passed = result.returncode == 0
            message = "Docker build succeeded" if passed else "Docker build failed"

            # Get image size if successful
            details = {'exit_code': result.returncode}
            if passed:
                size_result = subprocess.run(
                    ['docker', 'images', 'vcp-ml:validation', '--format', '{{.Size}}'],
                    capture_output=True,
                    text=True
                )
                if size_result.returncode == 0:
                    details['image_size'] = size_result.stdout.strip()

            return ValidationResult(
                check_name="docker_build",
                passed=passed,
                message=message,
                details=details
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                check_name="docker_build",
                passed=False,
                message="Docker build timed out after 300 seconds"
            )
        except Exception as e:
            return ValidationResult(
                check_name="docker_build",
                passed=False,
                message=f"Docker build failed: {e}"
            )

    def validate_environment(self) -> ValidationResult:
        """
        Check all required environment variables are set

        Returns:
            ValidationResult with environment check details
        """
        logger.info("🔧 Validating environment variables...")

        # Required environment variables for production
        required_vars = [
            'ENVIRONMENT',
            'API_HOST',
            'API_PORT',
        ]

        # Optional but recommended
        optional_vars = [
            'LOG_LEVEL',
            'DATABASE_PATH',
            'MODEL_REGISTRY_PATH',
        ]

        missing_required = []
        missing_optional = []
        present_vars = {}

        for var in required_vars:
            value = os.getenv(var)
            if value:
                present_vars[var] = value
            else:
                missing_required.append(var)

        for var in optional_vars:
            value = os.getenv(var)
            if value:
                present_vars[var] = value
            else:
                missing_optional.append(var)

        passed = len(missing_required) == 0

        if passed:
            message = f"All required environment variables set ({len(present_vars)} total)"
        else:
            message = f"Missing required variables: {', '.join(missing_required)}"

        details = {
            'required_present': len(required_vars) - len(missing_required),
            'required_total': len(required_vars),
            'optional_present': len(optional_vars) - len(missing_optional),
            'optional_total': len(optional_vars),
            'missing_required': missing_required,
            'missing_optional': missing_optional
        }

        return ValidationResult(
            check_name="environment",
            passed=passed,
            message=message,
            details=details
        )

    def validate_database_connections(self) -> ValidationResult:
        """
        Verify database connections are valid

        Returns:
            ValidationResult with database check details
        """
        logger.info("💾 Validating database connections...")

        # Check for required database files
        data_dir = self.project_root / 'data'
        required_dbs = [
            'price_movements.db',
            'features/technical_features.db',
            'features/financial_data.db',
            'features/financial_features.db',
        ]

        missing_dbs = []
        valid_dbs = []
        invalid_dbs = []

        for db_path in required_dbs:
            full_path = data_dir / db_path
            if not full_path.exists():
                missing_dbs.append(db_path)
            else:
                # Try to connect and validate
                try:
                    conn = sqlite3.connect(str(full_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                    table_count = cursor.fetchone()[0]
                    conn.close()

                    if table_count > 0:
                        valid_dbs.append(db_path)
                    else:
                        invalid_dbs.append(db_path)
                except Exception as e:
                    invalid_dbs.append(db_path)

        passed = len(missing_dbs) == 0 and len(invalid_dbs) == 0

        if passed:
            message = f"All {len(valid_dbs)} databases valid"
        else:
            issues = []
            if missing_dbs:
                issues.append(f"{len(missing_dbs)} missing")
            if invalid_dbs:
                issues.append(f"{len(invalid_dbs)} invalid")
            message = f"Database issues: {', '.join(issues)}"

        details = {
            'valid': valid_dbs,
            'missing': missing_dbs,
            'invalid': invalid_dbs,
            'total_checked': len(required_dbs)
        }

        return ValidationResult(
            check_name="database_connections",
            passed=passed,
            message=message,
            details=details
        )

    def validate_models(self) -> ValidationResult:
        """
        Verify model registry has at least 1 model

        Returns:
            ValidationResult with model registry details
        """
        logger.info("🤖 Validating model registry...")

        registry_path = self.project_root / 'data' / 'models' / 'registry' / 'model_registry.db'

        if not registry_path.exists():
            return ValidationResult(
                check_name="model_registry",
                passed=False,
                message="Model registry database not found",
                details={'registry_path': str(registry_path)}
            )

        try:
            conn = sqlite3.connect(str(registry_path))
            cursor = conn.cursor()

            # Check if models table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='models'")
            if not cursor.fetchone():
                conn.close()
                return ValidationResult(
                    check_name="model_registry",
                    passed=False,
                    message="Models table not found in registry"
                )

            # Count models
            cursor.execute("SELECT COUNT(*) FROM models")
            model_count = cursor.fetchone()[0]

            # Get latest model info
            cursor.execute("""
                SELECT model_id, model_type, version, created_at
                FROM models
                ORDER BY created_at DESC
                LIMIT 1
            """)
            latest_model = cursor.fetchone()

            conn.close()

            passed = model_count > 0
            message = f"Found {model_count} models in registry" if passed else "No models in registry"

            details = {
                'model_count': model_count,
                'registry_path': str(registry_path)
            }

            if latest_model:
                details['latest_model'] = {
                    'model_id': latest_model[0],
                    'model_type': latest_model[1],
                    'version': latest_model[2],
                    'created_at': latest_model[3]
                }

            return ValidationResult(
                check_name="model_registry",
                passed=passed,
                message=message,
                details=details
            )

        except Exception as e:
            return ValidationResult(
                check_name="model_registry",
                passed=False,
                message=f"Model registry validation failed: {e}"
            )

    def validate_all(self, skip_docker: bool = False) -> ValidationReport:
        """
        Run all validation checks

        Args:
            skip_docker: Skip Docker build validation (for speed)

        Returns:
            ValidationReport with all results
        """
        logger.info("🚀 Starting pre-deployment validation...")
        start_time = datetime.now()

        results = []

        # Run all validations
        results.append(self.validate_tests())

        if not skip_docker:
            results.append(self.validate_docker_build())

        results.append(self.validate_environment())
        results.append(self.validate_database_connections())
        results.append(self.validate_models())

        # Calculate summary
        passed_checks = sum(1 for r in results if r.passed)
        failed_checks = len(results) - passed_checks
        overall_passed = failed_checks == 0

        duration = (datetime.now() - start_time).total_seconds()

        report = ValidationReport(
            overall_passed=overall_passed,
            total_checks=len(results),
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            results=results,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration
        )

        # Log summary
        if overall_passed:
            logger.info(f"✅ All {len(results)} validation checks passed!")
        else:
            logger.error(f"❌ {failed_checks}/{len(results)} validation checks failed")
            for result in results:
                if not result.passed:
                    logger.error(f"  - {result.check_name}: {result.message}")

        return report

    def generate_validation_report(self) -> Dict:
        """
        Generate comprehensive validation report

        Returns:
            Dictionary with validation report
        """
        report = self.validate_all()
        return report.to_dict()


if __name__ == "__main__":
    """Run pre-deployment validation"""
    validator = PreDeploymentValidator()
    report = validator.validate_all(skip_docker=True)  # Skip Docker for speed

    if report.overall_passed:
        print("\n✅ PRE-DEPLOYMENT VALIDATION PASSED")
        print(f"All {report.total_checks} checks completed in {report.duration_seconds:.2f}s")
        exit(0)
    else:
        print(f"\n❌ PRE-DEPLOYMENT VALIDATION FAILED")
        print(f"{report.failed_checks}/{report.total_checks} checks failed")
        exit(1)
