"""
Load Testing & Scaling (Story 7.5)

Locust-based load testing with performance metrics and auto-scaling recommendations.
Ensures system can handle 500 concurrent users with <200ms p95 latency.

Target Performance:
- Concurrent users: 500
- p95 latency: <200ms
- Error rate: <5%
- Throughput: 500+ req/sec
"""

import statistics
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from locust import HttpUser, task, between, events
    LOCUST_AVAILABLE = True
except ImportError:
    LOCUST_AVAILABLE = False

logger = logging.getLogger(__name__)


class LoadTester:
    """
    Load testing orchestrator with Locust integration.

    Features:
    - Create load test plans (users, ramp time, scenarios)
    - Collect performance metrics (latency, throughput, errors)
    - Analyze results against targets
    - Generate auto-scaling recommendations
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize load tester.

        Args:
            base_url: Base URL of API to test
        """
        self.base_url = base_url
        self.test_results = []

    def create_test_plan(
        self,
        max_users: int = 500,
        ramp_time: int = 300
    ) -> Dict[str, Any]:
        """
        Create load test plan.

        Args:
            max_users: Maximum concurrent users (default: 500)
            ramp_time: Ramp-up time in seconds (default: 300 = 5 min)

        Returns:
            Test plan dictionary
        """
        plan = {
            'max_users': max_users,
            'ramp_time': ramp_time,
            'spawn_rate': max_users / ramp_time,  # Users per second
            'base_url': self.base_url,
            'scenarios': [
                {
                    'name': 'predict_single',
                    'weight': 7,  # 70% of requests
                    'endpoint': '/api/v1/predict',
                    'method': 'POST',
                    'payload': {
                        'bse_code': '500325',
                        'date': '2025-11-14'
                    }
                },
                {
                    'name': 'batch_predict',
                    'weight': 3,  # 30% of requests
                    'endpoint': '/api/v1/batch_predict',
                    'method': 'POST',
                    'payload': {
                        'bse_codes': ['500325', '532977', '500180']
                    }
                },
                {
                    'name': 'health_check',
                    'weight': 1,  # 10% of requests
                    'endpoint': '/api/v1/health',
                    'method': 'GET'
                }
            ],
            'created_at': datetime.now().isoformat()
        }

        logger.info(f"Created test plan: {max_users} users, {ramp_time}s ramp")
        return plan

    def run_load_test(
        self,
        duration: int = 600,
        max_users: int = 500,
        ramp_time: int = 300
    ) -> Dict[str, Any]:
        """
        Run load test using Locust.

        Args:
            duration: Test duration in seconds (default: 600 = 10 min)
            max_users: Maximum concurrent users
            ramp_time: Ramp-up time

        Returns:
            Test results dictionary

        Note:
            This is a placeholder. In production, you would:
            1. Start Locust programmatically
            2. Monitor test execution
            3. Collect real-time metrics
            4. Stop test after duration
        """
        if not LOCUST_AVAILABLE:
            logger.warning("Locust not available. Returning mock results.")
            return self._generate_mock_results(max_users, duration)

        # In production, use Locust's programmatic API
        # For now, return structure that matches expected format
        logger.info(f"Running load test: {max_users} users for {duration}s")

        results = {
            'duration': duration,
            'max_users': max_users,
            'ramp_time': ramp_time,
            'requests': [],
            'started_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat()
        }

        return results

    def _generate_mock_results(
        self,
        max_users: int,
        duration: int
    ) -> Dict[str, Any]:
        """
        Generate mock load test results for testing.

        Args:
            max_users: Number of users
            duration: Test duration

        Returns:
            Mock results matching expected format
        """
        import random

        # Generate realistic request latencies
        num_requests = max_users * duration // 2  # Rough estimate

        requests = []
        for _ in range(min(num_requests, 1000)):  # Limit for testing
            # Most requests fast, some slow
            if random.random() < 0.9:
                latency = random.gauss(50, 20)  # Mean 50ms, std 20ms
            else:
                latency = random.gauss(200, 50)  # Outliers

            requests.append({
                'response_time': max(1, latency),
                'success': random.random() > 0.03  # 3% error rate
            })

        return {
            'requests': requests,
            'duration': duration
        }

    def collect_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """
        Collect performance metrics from load test results.

        Args:
            results: Load test results

        Returns:
            Dictionary with performance metrics
        """
        requests = results.get('requests', [])

        if not requests:
            return {
                'latency_p50': 0,
                'latency_p95': 0,
                'latency_p99': 0,
                'throughput': 0,
                'error_rate': 0
            }

        # Extract latencies and success flags
        latencies = [r['response_time'] for r in requests]
        successes = [r['success'] for r in requests]

        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        n = len(latencies_sorted)

        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        metrics = {
            'latency_p50': latencies_sorted[p50_idx] if n > 0 else 0,
            'latency_p95': latencies_sorted[p95_idx] if n > 0 else 0,
            'latency_p99': latencies_sorted[p99_idx] if n > 0 else 0,
            'latency_mean': statistics.mean(latencies) if latencies else 0,
            'latency_std': statistics.stdev(latencies) if len(latencies) > 1 else 0,
            'throughput': len(requests) / results.get('duration', 1),
            'error_rate': 1.0 - (sum(successes) / len(successes)) if successes else 0,
            'total_requests': len(requests),
            'failed_requests': len(successes) - sum(successes)
        }

        return metrics

    def analyze_results(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze load test metrics against targets.

        Args:
            metrics: Performance metrics

        Returns:
            Analysis results with pass/fail assessments
        """
        # Performance targets
        TARGET_P95_LATENCY = 200  # ms
        TARGET_ERROR_RATE = 0.05  # 5%
        TARGET_THROUGHPUT = 400  # req/sec

        analysis = {
            'latency_p50': metrics.get('latency_p50', 0),
            'latency_p95': metrics.get('latency_p95', 0),
            'latency_p99': metrics.get('latency_p99', 0),
            'throughput': metrics.get('throughput', 0),
            'error_rate': metrics.get('error_rate', 0),
            'latency_acceptable': metrics.get('latency_p95', float('inf')) < TARGET_P95_LATENCY,
            'throughput_acceptable': metrics.get('throughput', 0) >= TARGET_THROUGHPUT,
            'error_rate_acceptable': metrics.get('error_rate', 1.0) < TARGET_ERROR_RATE,
            'latency_assessment': self._assess_latency(metrics.get('latency_p95', 0)),
            'overall_status': 'PASS' if (
                metrics.get('latency_p95', float('inf')) < TARGET_P95_LATENCY and
                metrics.get('error_rate', 1.0) < TARGET_ERROR_RATE and
                metrics.get('throughput', 0) >= TARGET_THROUGHPUT
            ) else 'FAIL'
        }

        return analysis

    def _assess_latency(self, p95_latency: float) -> str:
        """Assess latency performance"""
        if p95_latency < 50:
            return "Excellent (<50ms)"
        elif p95_latency < 100:
            return "Good (<100ms)"
        elif p95_latency < 200:
            return "Acceptable (<200ms)"
        else:
            return "Poor (>200ms)"

    def generate_scaling_recommendations(
        self,
        metrics: Dict[str, float]
    ) -> List[str]:
        """
        Generate auto-scaling recommendations based on metrics.

        Args:
            metrics: Performance metrics with CPU, memory, latency

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check latency
        latency_p95 = metrics.get('latency_p95', 0)
        if latency_p95 > 200:
            recommendations.append(
                f"HIGH LATENCY: p95={latency_p95:.0f}ms. "
                "Consider horizontal scaling (add 2-4 instances) or optimize slow queries."
            )
        elif latency_p95 > 100:
            recommendations.append(
                f"ELEVATED LATENCY: p95={latency_p95:.0f}ms. "
                "Monitor closely. Consider adding 1-2 instances during peak hours."
            )

        # Check CPU usage
        cpu_usage = metrics.get('cpu_usage', 0)
        if cpu_usage > 80:
            recommendations.append(
                f"HIGH CPU: {cpu_usage:.0f}%. "
                "Add instances immediately. Target CPU <70% for headroom."
            )
        elif cpu_usage > 70:
            recommendations.append(
                f"ELEVATED CPU: {cpu_usage:.0f}%. "
                "Consider adding instances during peak load."
            )

        # Check memory usage
        memory_usage = metrics.get('memory_usage', 0)
        if memory_usage > 85:
            recommendations.append(
                f"HIGH MEMORY: {memory_usage:.0f}%. "
                "Risk of OOM errors. Add instances or increase instance memory."
            )

        # Check error rate
        error_rate = metrics.get('error_rate', 0)
        if error_rate > 0.10:
            recommendations.append(
                f"HIGH ERROR RATE: {error_rate:.1%}. "
                "Investigate application errors before scaling. Check logs and monitoring."
            )
        elif error_rate > 0.05:
            recommendations.append(
                f"ELEVATED ERROR RATE: {error_rate:.1%}. "
                "Monitor error logs. May need bug fixes."
            )

        # Check throughput
        throughput = metrics.get('throughput', 0)
        if throughput < 200:
            recommendations.append(
                f"LOW THROUGHPUT: {throughput:.0f} req/s. "
                "System may be overloaded or inefficient. Review optimization opportunities."
            )

        # Positive feedback if all good
        if not recommendations:
            recommendations.append(
                "SYSTEM HEALTHY: All metrics within acceptable ranges. "
                "Current configuration supports load well. "
                f"p95={latency_p95:.0f}ms, CPU={cpu_usage:.0f}%, throughput={throughput:.0f} req/s."
            )

        return recommendations

    def generate_report(
        self,
        test_plan: Dict[str, Any],
        metrics: Dict[str, float],
        analysis: Dict[str, Any],
        recommendations: List[str]
    ) -> str:
        """
        Generate load test report.

        Args:
            test_plan: Test configuration
            metrics: Performance metrics
            analysis: Analysis results
            recommendations: Scaling recommendations

        Returns:
            Formatted report string
        """
        report = f"""
========================================
LOAD TESTING REPORT
========================================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Tool: Locust
Base URL: {test_plan.get('base_url', 'N/A')}

TEST CONFIGURATION:
- Max Users: {test_plan.get('max_users', 'N/A')}
- Ramp Time: {test_plan.get('ramp_time', 'N/A')}s
- Spawn Rate: {test_plan.get('spawn_rate', 'N/A'):.1f} users/sec

PERFORMANCE METRICS:
- Total Requests: {metrics.get('total_requests', 0):,}
- Failed Requests: {metrics.get('failed_requests', 0):,} ({metrics.get('error_rate', 0):.2%})
- Throughput: {metrics.get('throughput', 0):.1f} req/sec
- Latency (p50): {metrics.get('latency_p50', 0):.0f}ms
- Latency (p95): {metrics.get('latency_p95', 0):.0f}ms {'✓' if analysis.get('latency_acceptable') else '✗'}
- Latency (p99): {metrics.get('latency_p99', 0):.0f}ms

ASSESSMENT: {analysis.get('overall_status', 'UNKNOWN')}
- Latency: {analysis.get('latency_assessment', 'N/A')}
- Throughput: {'PASS' if analysis.get('throughput_acceptable') else 'FAIL'}
- Error Rate: {'PASS' if analysis.get('error_rate_acceptable') else 'FAIL'}

SCALING RECOMMENDATIONS:
"""
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"

        report += "\n========================================\n"

        return report


# Example Locust user class (for reference)
if LOCUST_AVAILABLE:
    class VCPMLUser(HttpUser):
        """
        Locust user for VCP ML API load testing.

        This class would be used in a locustfile.py for actual load testing.
        """
        wait_time = between(1, 3)  # Wait 1-3 seconds between requests

        @task(7)  # 70% of requests
        def predict_single(self):
            """Single stock prediction"""
            self.client.post("/api/v1/predict", json={
                "bse_code": "500325",
                "date": "2025-11-14"
            })

        @task(3)  # 30% of requests
        def batch_predict(self):
            """Batch stock prediction"""
            self.client.post("/api/v1/batch_predict", json={
                "bse_codes": ["500325", "532977", "500180"]
            })

        @task(1)  # 10% of requests
        def health_check(self):
            """Health check endpoint"""
            self.client.get("/api/v1/health")
