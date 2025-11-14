"""
Locust Load Testing File for VCP ML API

Usage:
    # Web UI mode (recommended for monitoring)
    locust -f locustfile.py --host=http://localhost:8000

    # Headless mode (automated testing)
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 500 --spawn-rate 5 --run-time 10m --headless

    # Generate HTML report
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 500 --spawn-rate 5 --run-time 10m --headless \
           --html=load_test_report.html

Performance Targets:
- Concurrent users: 500
- p95 latency: <200ms
- Error rate: <5%
- Throughput: 500+ req/sec
"""

from locust import HttpUser, task, between
import random


class VCPMLUser(HttpUser):
    """
    Simulated user for VCP ML prediction API.

    User behavior:
    - 70% single stock predictions
    - 30% batch predictions
    - 10% health checks
    - Wait 1-3 seconds between requests (realistic user behavior)
    """

    # Wait time between requests (simulates user think time)
    wait_time = between(1, 3)

    # Sample stock codes for testing
    SAMPLE_STOCKS = [
        "500325",  # Reliance
        "532977",  # Bajaj Finance
        "500180",  # HDFC Bank
        "500209",  # Infosys
        "532174",  # ICICI Bank
    ]

    def on_start(self):
        """Called when a user starts (can be used for login, setup, etc.)"""
        # For VCP ML API, we might want to authenticate or get API key
        # For now, just log that user started
        pass

    @task(7)  # Weight 7 = 70% of requests
    def predict_single_stock(self):
        """
        Single stock prediction request.

        Endpoint: POST /api/v1/predict
        Payload: {"bse_code": "500325", "date": "2025-11-14"}
        """
        bse_code = random.choice(self.SAMPLE_STOCKS)

        with self.client.post(
            "/api/v1/predict",
            json={
                "bse_code": bse_code,
                "date": "2025-11-14"
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Verify response has prediction
                try:
                    data = response.json()
                    if 'prediction' in data or 'label' in data:
                        response.success()
                    else:
                        response.failure("Response missing prediction field")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(3)  # Weight 3 = 30% of requests
    def batch_predict(self):
        """
        Batch prediction request.

        Endpoint: POST /api/v1/batch_predict
        Payload: {"predictions": [{"bse_code": "...", "date": "..."}]}
        """
        # Select 3-5 random stocks
        num_stocks = random.randint(3, 5)
        bse_codes = random.sample(self.SAMPLE_STOCKS, num_stocks)

        predictions = [
            {"bse_code": code, "date": "2025-11-14"}
            for code in bse_codes
        ]

        with self.client.post(
            "/api/v1/batch_predict",
            json={"predictions": predictions},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'predictions' in data or 'results' in data:
                        response.success()
                    else:
                        response.failure("Response missing predictions")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)  # Weight 1 = 10% of requests
    def health_check(self):
        """
        Health check request.

        Endpoint: GET /api/v1/health
        """
        with self.client.get(
            "/api/v1/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class SpikeTestUser(HttpUser):
    """
    User for spike testing (sudden traffic surge).

    Use this class for testing system behavior under sudden load spikes:
    locust -f locustfile.py --user-classes SpikeTestUser --host=http://localhost:8000
    """

    wait_time = between(0.5, 1.5)  # More aggressive

    SAMPLE_STOCKS = ["500325", "532977", "500180"]

    @task
    def rapid_predictions(self):
        """Make rapid prediction requests"""
        bse_code = random.choice(self.SAMPLE_STOCKS)
        self.client.post(
            "/api/v1/predict",
            json={"bse_code": bse_code, "date": "2025-11-14"}
        )


class StressTestUser(HttpUser):
    """
    User for stress testing (sustained high load).

    Use this class for testing system limits:
    locust -f locustfile.py --user-classes StressTestUser --host=http://localhost:8000 \
           --users 1000 --spawn-rate 10
    """

    wait_time = between(0.1, 0.5)  # Very aggressive

    SAMPLE_STOCKS = ["500325", "532977", "500180", "500209", "532174"]

    @task(10)
    def stress_predict(self):
        """Continuous prediction requests"""
        bse_code = random.choice(self.SAMPLE_STOCKS)
        self.client.post(
            "/api/v1/predict",
            json={"bse_code": bse_code, "date": "2025-11-14"},
            timeout=5  # Don't wait too long
        )

    @task(1)
    def stress_batch(self):
        """Batch prediction under stress"""
        bse_codes = random.sample(self.SAMPLE_STOCKS, 3)
        predictions = [{"bse_code": code, "date": "2025-11-14"} for code in bse_codes]
        self.client.post(
            "/api/v1/batch_predict",
            json={"predictions": predictions},
            timeout=10
        )


# Event handlers for custom metrics and reporting
from locust import events


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("=" * 50)
    print("VCP ML API Load Test Starting")
    print(f"Target: {environment.host}")
    print("=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("=" * 50)
    print("VCP ML API Load Test Complete")
    print("=" * 50)

    # Print summary statistics
    stats = environment.stats.total
    print(f"\nSUMMARY:")
    print(f"- Total Requests: {stats.num_requests:,}")
    print(f"- Failed Requests: {stats.num_failures:,} ({stats.fail_ratio:.1%})")
    print(f"- Average Response Time: {stats.avg_response_time:.0f}ms")
    print(f"- Median Response Time: {stats.median_response_time:.0f}ms")
    print(f"- 95th Percentile: {stats.get_response_time_percentile(0.95):.0f}ms")
    print(f"- 99th Percentile: {stats.get_response_time_percentile(0.99):.0f}ms")
    print(f"- Requests per Second: {stats.total_rps:.1f}")
    print("=" * 50)
