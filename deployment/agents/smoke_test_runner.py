"""
Agent 3: Smoke Test Runner

Runs critical smoke tests after deployment:
- Single prediction endpoint
- Batch prediction endpoint
- Health check endpoint
- Metrics endpoint
- Response time validation

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import time
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SmokeTestResult:
    """Result of a smoke test"""
    test_name: str
    passed: bool
    message: str
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    details: Optional[Dict] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SmokeTestReport:
    """Comprehensive smoke test report"""
    overall_passed: bool
    total_tests: int
    passed_tests: int
    failed_tests: int
    avg_response_time_ms: float
    results: List[SmokeTestResult]
    timestamp: str
    duration_seconds: float

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            **asdict(self),
            'results': [asdict(r) for r in self.results]
        }


class SmokeTestRunner:
    """
    Smoke test runner agent

    Tests critical API endpoints after deployment
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize smoke test runner

        Args:
            base_url: Base URL of API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[SmokeTestResult] = []

    def test_health_endpoint(self) -> SmokeTestResult:
        """
        Test health check endpoint

        Returns:
            SmokeTestResult for health check
        """
        logger.info("🏥 Testing health endpoint...")

        url = f"{self.base_url}/api/v1/health"

        try:
            start_time = time.time()
            response = requests.get(url, timeout=self.timeout)
            response_time_ms = (time.time() - start_time) * 1000

            passed = response.status_code == 200

            if passed:
                data = response.json()
                message = f"Health check passed: {data.get('status', 'unknown')}"
                details = {
                    'status': data.get('status'),
                    'model_loaded': data.get('model_loaded'),
                    'uptime_seconds': data.get('uptime_seconds')
                }
            else:
                message = f"Health check failed: HTTP {response.status_code}"
                details = {'error': response.text[:200]}

            return SmokeTestResult(
                test_name="health_endpoint",
                passed=passed,
                message=message,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                details=details
            )

        except requests.Timeout:
            return SmokeTestResult(
                test_name="health_endpoint",
                passed=False,
                message=f"Request timed out after {self.timeout}s"
            )
        except Exception as e:
            return SmokeTestResult(
                test_name="health_endpoint",
                passed=False,
                message=f"Health check failed: {e}"
            )

    def test_single_prediction(self) -> SmokeTestResult:
        """
        Test single prediction endpoint with sample data

        Returns:
            SmokeTestResult for single prediction
        """
        logger.info("🎯 Testing single prediction endpoint...")

        url = f"{self.base_url}/api/v1/predict"

        # Sample prediction request
        payload = {
            "bse_code": "500325",  # Reliance
            "nse_symbol": "RELIANCE",
            "prediction_date": "2025-11-14",
            "include_features": False
        }

        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=self.timeout)
            response_time_ms = (time.time() - start_time) * 1000

            passed = response.status_code == 200 and response_time_ms < 100

            if response.status_code == 200:
                data = response.json()
                has_prediction = 'predicted_label' in data and 'probability' in data

                if has_prediction and response_time_ms < 100:
                    message = f"Prediction succeeded in {response_time_ms:.2f}ms"
                elif has_prediction:
                    message = f"Prediction succeeded but slow ({response_time_ms:.2f}ms > 100ms)"
                    passed = False
                else:
                    message = "Response missing required fields"
                    passed = False

                details = {
                    'predicted_label': data.get('predicted_label'),
                    'probability': data.get('probability'),
                    'confidence': data.get('confidence'),
                    'model_version': data.get('model_version')
                }
            else:
                message = f"Prediction failed: HTTP {response.status_code}"
                details = {'error': response.text[:200]}
                passed = False

            return SmokeTestResult(
                test_name="single_prediction",
                passed=passed,
                message=message,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                details=details
            )

        except requests.Timeout:
            return SmokeTestResult(
                test_name="single_prediction",
                passed=False,
                message=f"Request timed out after {self.timeout}s"
            )
        except Exception as e:
            return SmokeTestResult(
                test_name="single_prediction",
                passed=False,
                message=f"Prediction failed: {e}"
            )

    def test_batch_prediction(self) -> SmokeTestResult:
        """
        Test batch prediction endpoint with 10 sample stocks

        Returns:
            SmokeTestResult for batch prediction
        """
        logger.info("📦 Testing batch prediction endpoint...")

        url = f"{self.base_url}/api/v1/batch_predict"

        # Sample batch request (10 stocks)
        sample_stocks = [
            {"bse_code": "500325", "prediction_date": "2025-11-14"},  # Reliance
            {"bse_code": "500112", "prediction_date": "2025-11-14"},  # SBI
            {"bse_code": "532540", "prediction_date": "2025-11-14"},  # TCS
            {"bse_code": "500180", "prediction_date": "2025-11-14"},  # HDFC Bank
            {"bse_code": "500209", "prediction_date": "2025-11-14"},  # Infosys
            {"bse_code": "500510", "prediction_date": "2025-11-14"},  # L&T
            {"bse_code": "532174", "prediction_date": "2025-11-14"},  # ICICI Bank
            {"bse_code": "500696", "prediction_date": "2025-11-14"},  # Hindal
            {"bse_code": "532978", "prediction_date": "2025-11-14"},  # Bharti Airtel
            {"bse_code": "500010", "prediction_date": "2025-11-14"},  # HDFC
        ]

        payload = {"predictions": sample_stocks}

        try:
            start_time = time.time()
            response = requests.post(url, json=payload, timeout=self.timeout)
            response_time_ms = (time.time() - start_time) * 1000

            passed = response.status_code == 200

            if passed:
                data = response.json()
                is_list = isinstance(data, list)
                has_10_results = len(data) == 10 if is_list else False

                if is_list and has_10_results:
                    message = f"Batch prediction succeeded: {len(data)} stocks in {response_time_ms:.2f}ms"
                    details = {
                        'num_predictions': len(data),
                        'avg_probability': sum(p.get('probability', 0) for p in data) / len(data),
                        'sample_prediction': data[0] if data else None
                    }
                else:
                    message = f"Unexpected response format or count: {len(data) if is_list else 'not a list'}"
                    details = {'response_type': type(data).__name__}
                    passed = False
            else:
                message = f"Batch prediction failed: HTTP {response.status_code}"
                details = {'error': response.text[:200]}
                passed = False

            return SmokeTestResult(
                test_name="batch_prediction",
                passed=passed,
                message=message,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                details=details
            )

        except requests.Timeout:
            return SmokeTestResult(
                test_name="batch_prediction",
                passed=False,
                message=f"Request timed out after {self.timeout}s"
            )
        except Exception as e:
            return SmokeTestResult(
                test_name="batch_prediction",
                passed=False,
                message=f"Batch prediction failed: {e}"
            )

    def test_metrics_endpoint(self) -> SmokeTestResult:
        """
        Test metrics endpoint (Prometheus format)

        Returns:
            SmokeTestResult for metrics endpoint
        """
        logger.info("📊 Testing metrics endpoint...")

        url = f"{self.base_url}/api/v1/metrics"

        try:
            start_time = time.time()
            response = requests.get(url, timeout=self.timeout)
            response_time_ms = (time.time() - start_time) * 1000

            passed = response.status_code == 200

            if passed:
                metrics_text = response.text
                has_metrics = 'prediction_requests_total' in metrics_text

                if has_metrics:
                    message = "Metrics endpoint working"
                    details = {
                        'format': 'prometheus',
                        'length': len(metrics_text)
                    }
                else:
                    message = "Metrics endpoint returned unexpected format"
                    details = {'preview': metrics_text[:100]}
                    passed = False
            else:
                message = f"Metrics endpoint failed: HTTP {response.status_code}"
                details = {'error': response.text[:200]}
                passed = False

            return SmokeTestResult(
                test_name="metrics_endpoint",
                passed=passed,
                message=message,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                details=details
            )

        except requests.Timeout:
            return SmokeTestResult(
                test_name="metrics_endpoint",
                passed=False,
                message=f"Request timed out after {self.timeout}s"
            )
        except Exception as e:
            return SmokeTestResult(
                test_name="metrics_endpoint",
                passed=False,
                message=f"Metrics endpoint failed: {e}"
            )

    def run_all_smoke_tests(self) -> SmokeTestReport:
        """
        Run all critical smoke tests

        Returns:
            SmokeTestReport with all results
        """
        logger.info("🚀 Starting smoke tests...")
        start_time = datetime.now()

        results = []

        # Run all smoke tests
        results.append(self.test_health_endpoint())
        results.append(self.test_single_prediction())
        results.append(self.test_batch_prediction())
        results.append(self.test_metrics_endpoint())

        # Calculate summary
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = len(results) - passed_tests
        overall_passed = failed_tests == 0

        # Calculate average response time (only for successful tests)
        response_times = [r.response_time_ms for r in results if r.response_time_ms is not None]
        avg_response_time_ms = sum(response_times) / len(response_times) if response_times else 0

        duration = (datetime.now() - start_time).total_seconds()

        report = SmokeTestReport(
            overall_passed=overall_passed,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            avg_response_time_ms=avg_response_time_ms,
            results=results,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration
        )

        # Log summary
        if overall_passed:
            logger.info(f"✅ All {len(results)} smoke tests passed!")
            logger.info(f"📊 Average response time: {avg_response_time_ms:.2f}ms")
        else:
            logger.error(f"❌ {failed_tests}/{len(results)} smoke tests failed")
            for result in results:
                if not result.passed:
                    logger.error(f"  - {result.test_name}: {result.message}")

        return report


if __name__ == "__main__":
    """Run smoke tests"""
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    runner = SmokeTestRunner(base_url=base_url)
    report = runner.run_all_smoke_tests()

    if report.overall_passed:
        print(f"\n✅ ALL SMOKE TESTS PASSED")
        print(f"{report.total_tests} tests completed in {report.duration_seconds:.2f}s")
        print(f"Average response time: {report.avg_response_time_ms:.2f}ms")
        exit(0)
    else:
        print(f"\n❌ SMOKE TESTS FAILED")
        print(f"{report.failed_tests}/{report.total_tests} tests failed")
        exit(1)
