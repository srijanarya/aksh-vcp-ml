"""
Agent 4: Deployment Monitor

Monitors deployment health and triggers rollback if needed:
- Real-time health monitoring
- API performance tracking
- Failure detection
- Alert notifications

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import time
import requests
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status snapshot"""
    timestamp: str
    status: str
    response_time_ms: float
    model_loaded: bool
    uptime_seconds: Optional[float] = None
    error: Optional[str] = None


@dataclass
class MonitoringResult:
    """Result of deployment monitoring"""
    deployment_id: str
    passed: bool
    duration_seconds: float
    health_checks: int
    failed_checks: int
    avg_response_time_ms: float
    health_snapshots: list
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class DeploymentMonitor:
    """
    Deployment monitoring agent

    Monitors deployment health and triggers rollback if needed
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        check_interval: int = 30,
        rollback_threshold: float = 0.95
    ):
        """
        Initialize deployment monitor

        Args:
            base_url: Base URL of API
            check_interval: Seconds between health checks
            rollback_threshold: Health threshold (rollback if below)
        """
        self.base_url = base_url.rstrip('/')
        self.check_interval = check_interval
        self.rollback_threshold = rollback_threshold

    def check_api_health(self) -> HealthStatus:
        """
        Check API health

        Returns:
            HealthStatus snapshot
        """
        url = f"{self.base_url}/api/v1/health"

        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return HealthStatus(
                    timestamp=datetime.now().isoformat(),
                    status=data.get('status', 'unknown'),
                    response_time_ms=response_time_ms,
                    model_loaded=data.get('model_loaded', False),
                    uptime_seconds=data.get('uptime_seconds')
                )
            else:
                return HealthStatus(
                    timestamp=datetime.now().isoformat(),
                    status='unhealthy',
                    response_time_ms=response_time_ms,
                    model_loaded=False,
                    error=f"HTTP {response.status_code}"
                )

        except Exception as e:
            return HealthStatus(
                timestamp=datetime.now().isoformat(),
                status='error',
                response_time_ms=0,
                model_loaded=False,
                error=str(e)
            )

    def monitor_deployment(
        self,
        deployment_id: str,
        duration: int = 300
    ) -> MonitoringResult:
        """
        Monitor deployment for specified duration

        Args:
            deployment_id: Unique deployment identifier
            duration: Monitoring duration in seconds

        Returns:
            MonitoringResult with monitoring data
        """
        logger.info(f"👀 Monitoring deployment {deployment_id} for {duration}s...")

        start_time = time.time()
        end_time = start_time + duration

        health_snapshots = []
        failed_checks = 0

        while time.time() < end_time:
            # Check health
            health = self.check_api_health()
            health_snapshots.append(health)

            # Log status
            if health.status == 'healthy':
                logger.info(f"  ✓ Health check passed ({health.response_time_ms:.2f}ms)")
            else:
                logger.warning(f"  ✗ Health check failed: {health.error or health.status}")
                failed_checks += 1

            # Check if rollback needed
            health_rate = 1 - (failed_checks / len(health_snapshots))
            if health_rate < self.rollback_threshold:
                logger.error(f"🚨 Health rate {health_rate:.2%} below threshold {self.rollback_threshold:.2%}")
                logger.error("Triggering rollback...")
                break

            # Wait for next check
            time.sleep(self.check_interval)

        # Calculate summary
        duration_actual = time.time() - start_time
        response_times = [h.response_time_ms for h in health_snapshots if h.response_time_ms > 0]
        avg_response_time_ms = sum(response_times) / len(response_times) if response_times else 0

        health_rate = 1 - (failed_checks / len(health_snapshots)) if health_snapshots else 0
        passed = health_rate >= self.rollback_threshold

        result = MonitoringResult(
            deployment_id=deployment_id,
            passed=passed,
            duration_seconds=duration_actual,
            health_checks=len(health_snapshots),
            failed_checks=failed_checks,
            avg_response_time_ms=avg_response_time_ms,
            health_snapshots=[asdict(h) for h in health_snapshots],
            timestamp=datetime.now().isoformat()
        )

        if passed:
            logger.info(f"✅ Monitoring completed: {health_rate:.2%} health rate")
        else:
            logger.error(f"❌ Monitoring failed: {health_rate:.2%} health rate")

        return result

    def trigger_rollback(self, reason: str):
        """
        Trigger rollback (to be implemented with RollbackAgent)

        Args:
            reason: Reason for rollback
        """
        logger.error(f"🔄 ROLLBACK TRIGGERED: {reason}")
        # This will be integrated with RollbackAgent

    def send_alert(self, message: str, severity: str = "warning"):
        """
        Send deployment alert

        Args:
            message: Alert message
            severity: Alert severity (info, warning, error)
        """
        # Log locally
        if severity == "error":
            logger.error(f"🚨 ALERT: {message}")
        elif severity == "warning":
            logger.warning(f"⚠️  ALERT: {message}")
        else:
            logger.info(f"ℹ️  ALERT: {message}")

        # Future: Send to Slack/Email via NotificationManager


if __name__ == "__main__":
    """Run deployment monitoring"""
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    monitor = DeploymentMonitor(base_url=base_url)
    result = monitor.monitor_deployment(
        deployment_id=f"deploy_{int(time.time())}",
        duration=duration
    )

    if result.passed:
        print(f"\n✅ MONITORING PASSED")
        print(f"Health checks: {result.health_checks - result.failed_checks}/{result.health_checks}")
        print(f"Average response time: {result.avg_response_time_ms:.2f}ms")
        exit(0)
    else:
        print(f"\n❌ MONITORING FAILED")
        print(f"Failed checks: {result.failed_checks}/{result.health_checks}")
        exit(1)
