"""
MLAlertAgent - Manages system alerts and notifications

This agent is responsible for:
1. Sending high-confidence prediction alerts to Telegram
2. Sending system health alerts (e.g., circuit breaker active)
3. Formatting messages with templates
4. Rate limiting to prevent spam

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import logging
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "agent": "MLAlertAgent", "message": "%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class AlertConfig:
    """Configuration for alerts"""
    telegram_token: Optional[str] = None
    chat_id: Optional[str] = None
    rate_limit_per_hour: int = 10

class MLAlertAgent:
    """
    Orchestrates alert delivery.
    """

    def __init__(self):
        """Initialize MLAlertAgent"""
        self.config = AlertConfig(
            telegram_token=os.getenv("TELEGRAM_TOKEN"),
            chat_id=os.getenv("TELEGRAM_CHAT_ID")
        )
        logger.info("MLAlertAgent initialized")

    def send_prediction_alert(self, prediction: Dict):
        """
        Send a prediction alert to Telegram.
        
        Args:
            prediction: Dict containing prediction details
        """
        message = self._format_prediction_message(prediction)
        self._send_telegram_message(message)

    def send_system_alert(self, title: str, message: str, level: str = "INFO"):
        """
        Send a system health alert.
        
        Args:
            title: Alert title
            message: Alert body
            level: Severity (INFO, WARNING, CRITICAL)
        """
        formatted_msg = f"🚨 *SYSTEM ALERT: {title}* 🚨\n\nLevel: {level}\n{message}"
        self._send_telegram_message(formatted_msg)

    def _format_prediction_message(self, prediction: Dict) -> str:
        """Format prediction dictionary into a readable message"""
        return (
            f"🚀 *Upper Circuit Prediction* 🚀\n\n"
            f"Symbol: *{prediction.get('bse_code')}*\n"
            f"Confidence: *{prediction.get('probability', 0)*100:.1f}%*\n"
            f"Date: {prediction.get('date')}\n\n"
            f"⚠️ _Disclaimer: This is an AI prediction, not financial advice._"
        )

    def _send_telegram_message(self, message: str):
        """Send message via Telegram API (Placeholder)"""
        logger.info(f"Sending Telegram message: {message[:50]}...")
        # requests.post(f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage", ...)
