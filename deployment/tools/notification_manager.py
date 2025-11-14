"""
Tool 4: Notification Manager

Manages deployment notifications:
- Slack notifications
- Email notifications
- Deployment event logging

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import json
import os
from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationSeverity(Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class DeploymentEvent:
    """Deployment event details"""
    event_type: str
    environment: str
    deployment_id: str
    message: str
    severity: str
    timestamp: str
    details: Optional[Dict] = None


class NotificationManager:
    """Deployment notification manager"""

    def __init__(
        self,
        slack_webhook: Optional[str] = None,
        email_config: Optional[Dict] = None,
        log_file: Optional[str] = None
    ):
        """
        Initialize notification manager

        Args:
            slack_webhook: Slack webhook URL
            email_config: Email configuration
            log_file: Path to deployment log file
        """
        self.slack_webhook = slack_webhook or os.getenv('SLACK_WEBHOOK_URL')
        self.email_config = email_config
        self.log_file = log_file or 'deployment/logs/deployment_events.jsonl'

    def send_slack_notification(
        self,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        details: Optional[Dict] = None
    ) -> bool:
        """
        Send notification to Slack

        Args:
            message: Notification message
            severity: Severity level
            details: Additional details

        Returns:
            True if sent successfully
        """
        if not self.slack_webhook:
            logger.warning("⚠️  Slack webhook not configured")
            return False

        # Map severity to Slack color
        colors = {
            NotificationSeverity.INFO: "#36a64f",
            NotificationSeverity.WARNING: "#ff9900",
            NotificationSeverity.ERROR: "#ff0000",
            NotificationSeverity.SUCCESS: "#00ff00"
        }

        # Build Slack message
        slack_message = {
            "text": message,
            "attachments": [{
                "color": colors.get(severity, "#36a64f"),
                "fields": [
                    {"title": "Severity", "value": severity.value, "short": True},
                    {"title": "Timestamp", "value": datetime.now().isoformat(), "short": True}
                ]
            }]
        }

        if details:
            for key, value in details.items():
                slack_message["attachments"][0]["fields"].append({
                    "title": key.replace('_', ' ').title(),
                    "value": str(value),
                    "short": False
                })

        try:
            import requests
            response = requests.post(
                self.slack_webhook,
                json=slack_message,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Slack notification sent")
                return True
            else:
                logger.error(f"❌ Slack notification failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Slack notification error: {e}")
            return False

    def send_email_notification(
        self,
        subject: str,
        body: str,
        to_addresses: Optional[list] = None
    ) -> bool:
        """
        Send email notification

        Args:
            subject: Email subject
            body: Email body
            to_addresses: Recipient email addresses

        Returns:
            True if sent successfully
        """
        if not self.email_config:
            logger.warning("⚠️  Email not configured")
            return False

        # Placeholder for email implementation
        # In production, use SMTP or email service
        logger.info(f"📧 Email notification: {subject}")
        logger.info(f"   To: {to_addresses}")
        logger.info(f"   Body: {body[:100]}...")

        return True

    def log_deployment_event(
        self,
        event: DeploymentEvent
    ):
        """
        Log deployment event to file

        Args:
            event: DeploymentEvent to log
        """
        try:
            # Ensure log directory exists
            log_dir = os.path.dirname(self.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            # Append event to log file (JSONL format)
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(asdict(event)) + '\n')

            logger.debug(f"📝 Event logged: {event.event_type}")

        except Exception as e:
            logger.error(f"❌ Failed to log event: {e}")

    def notify_deployment_start(
        self,
        environment: str,
        deployment_id: str,
        version: str
    ):
        """Notify deployment started"""
        event = DeploymentEvent(
            event_type="deployment_start",
            environment=environment,
            deployment_id=deployment_id,
            message=f"Deployment to {environment} started",
            severity=NotificationSeverity.INFO.value,
            timestamp=datetime.now().isoformat(),
            details={'version': version}
        )

        self.log_deployment_event(event)
        self.send_slack_notification(
            f"🚀 Deployment to {environment} started",
            NotificationSeverity.INFO,
            {'deployment_id': deployment_id, 'version': version}
        )

    def notify_deployment_success(
        self,
        environment: str,
        deployment_id: str,
        version: str,
        duration: float,
        url: str
    ):
        """Notify deployment succeeded"""
        event = DeploymentEvent(
            event_type="deployment_success",
            environment=environment,
            deployment_id=deployment_id,
            message=f"Deployment to {environment} succeeded",
            severity=NotificationSeverity.SUCCESS.value,
            timestamp=datetime.now().isoformat(),
            details={
                'version': version,
                'duration': duration,
                'url': url
            }
        )

        self.log_deployment_event(event)
        self.send_slack_notification(
            f"✅ Deployment to {environment} succeeded!",
            NotificationSeverity.SUCCESS,
            {
                'deployment_id': deployment_id,
                'version': version,
                'duration': f"{duration:.2f}s",
                'url': url
            }
        )

    def notify_deployment_failure(
        self,
        environment: str,
        deployment_id: str,
        error: str
    ):
        """Notify deployment failed"""
        event = DeploymentEvent(
            event_type="deployment_failure",
            environment=environment,
            deployment_id=deployment_id,
            message=f"Deployment to {environment} failed",
            severity=NotificationSeverity.ERROR.value,
            timestamp=datetime.now().isoformat(),
            details={'error': error}
        )

        self.log_deployment_event(event)
        self.send_slack_notification(
            f"❌ Deployment to {environment} failed",
            NotificationSeverity.ERROR,
            {'deployment_id': deployment_id, 'error': error}
        )

    def notify_rollback(
        self,
        environment: str,
        deployment_id: str,
        reason: str
    ):
        """Notify rollback triggered"""
        event = DeploymentEvent(
            event_type="rollback",
            environment=environment,
            deployment_id=deployment_id,
            message=f"Rollback triggered for {environment}",
            severity=NotificationSeverity.WARNING.value,
            timestamp=datetime.now().isoformat(),
            details={'reason': reason}
        )

        self.log_deployment_event(event)
        self.send_slack_notification(
            f"🔄 Rollback triggered for {environment}",
            NotificationSeverity.WARNING,
            {'deployment_id': deployment_id, 'reason': reason}
        )


if __name__ == "__main__":
    """Test notification manager"""
    manager = NotificationManager()

    # Test event logging
    manager.notify_deployment_start(
        environment="staging",
        deployment_id="deploy_123",
        version="v1.0.0"
    )

    manager.notify_deployment_success(
        environment="staging",
        deployment_id="deploy_123",
        version="v1.0.0",
        duration=120.5,
        url="http://localhost:8001"
    )

    print("✅ Notifications tested")
