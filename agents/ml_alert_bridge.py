"""
ML Alert Bridge Agent
=====================
Integrates ML predictions with the existing VCP alert system.

This agent:
1. Monitors VCP detections from the existing system
2. Enriches each detection with ML predictions
3. Filters alerts based on ML confidence
4. Sends enhanced alerts via Telegram/Gmail

Author: VCP ML System
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
import requests
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels"""
    CRITICAL = "critical"  # ML prob > 0.7
    HIGH = "high"          # ML prob > 0.5
    MEDIUM = "medium"      # ML prob > 0.3
    LOW = "low"            # ML prob > 0.15
    FILTERED = "filtered"  # ML prob < 0.15 (don't send)


@dataclass
class VCPDetection:
    """VCP pattern detection from existing system"""
    symbol: str
    detection_time: datetime
    pattern_type: str
    vcp_score: float
    price: float
    volume: int
    source: str  # 'blockbuster' or 'vcp'


@dataclass
class MLEnhancedAlert:
    """Enhanced alert with ML predictions"""
    symbol: str
    detection_time: datetime
    pattern_type: str
    vcp_score: float
    ml_probability: float
    ml_prediction: int
    priority: AlertPriority
    price: float
    volume: int
    model_version: str
    confidence_level: str


class MLAlertBridge:
    """
    Bridge between VCP detection system and ML prediction API
    """

    def __init__(
        self,
        vcp_db_path: str = "/Users/srijan/vcp_clean_test/vcp/vcp_trading_local.db",
        ml_api_url: str = "http://13.200.109.29:8002",
        min_ml_threshold: float = 0.15,
        polling_interval: int = 60
    ):
        """
        Initialize ML Alert Bridge

        Args:
            vcp_db_path: Path to VCP database
            ml_api_url: URL of ML prediction API
            min_ml_threshold: Minimum ML probability to send alert
            polling_interval: Seconds between checks
        """
        self.vcp_db_path = vcp_db_path
        self.ml_api_url = ml_api_url.rstrip('/')
        self.min_ml_threshold = min_ml_threshold
        self.polling_interval = polling_interval

        # Track processed detections to avoid duplicates
        self.processed_detections: set = set()

        logger.info(f"ML Alert Bridge initialized")
        logger.info(f"VCP DB: {vcp_db_path}")
        logger.info(f"ML API: {ml_api_url}")
        logger.info(f"Min threshold: {min_ml_threshold}")

    async def get_recent_vcp_detections(
        self,
        minutes: int = 60
    ) -> List[VCPDetection]:
        """
        Fetch recent VCP detections from the existing system

        Args:
            minutes: Look back this many minutes

        Returns:
            List of VCP detections
        """
        detections = []
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        try:
            conn = sqlite3.connect(self.vcp_db_path)
            cursor = conn.cursor()

            # Query blockbuster detections
            query = """
                SELECT symbol, detection_time, pattern_type, score,
                       price, volume
                FROM blockbuster_detections
                WHERE detection_time >= ?
                ORDER BY detection_time DESC
            """

            cursor.execute(query, (cutoff_time.isoformat(),))
            rows = cursor.fetchall()

            for row in rows:
                detection = VCPDetection(
                    symbol=row[0],
                    detection_time=datetime.fromisoformat(row[1]),
                    pattern_type=row[2] or 'vcp',
                    vcp_score=row[3] or 0.0,
                    price=row[4] or 0.0,
                    volume=row[5] or 0,
                    source='blockbuster'
                )

                # Create unique ID to avoid duplicates
                det_id = f"{detection.symbol}_{detection.detection_time.isoformat()}"

                if det_id not in self.processed_detections:
                    detections.append(detection)
                    self.processed_detections.add(det_id)

            conn.close()

            logger.info(f"Found {len(detections)} new VCP detections")

        except Exception as e:
            logger.error(f"Error fetching VCP detections: {e}")

        return detections

    async def get_ml_prediction(
        self,
        symbol: str,
        features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get ML prediction from API

        Args:
            symbol: Stock symbol
            features: Optional feature dict

        Returns:
            Prediction response from ML API
        """
        try:
            url = f"{self.ml_api_url}/api/v1/predict"
            payload = {
                "symbol": symbol,
                "features": features or {}
            }

            response = requests.post(
                url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"ML API error for {symbol}: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"ML API request failed for {symbol}: {e}")
            return None

    def determine_priority(self, ml_probability: float) -> AlertPriority:
        """
        Determine alert priority based on ML probability

        Args:
            ml_probability: ML prediction probability

        Returns:
            Alert priority level
        """
        if ml_probability >= 0.7:
            return AlertPriority.CRITICAL
        elif ml_probability >= 0.5:
            return AlertPriority.HIGH
        elif ml_probability >= 0.3:
            return AlertPriority.MEDIUM
        elif ml_probability >= self.min_ml_threshold:
            return AlertPriority.LOW
        else:
            return AlertPriority.FILTERED

    async def enhance_detection_with_ml(
        self,
        detection: VCPDetection
    ) -> Optional[MLEnhancedAlert]:
        """
        Enhance VCP detection with ML prediction

        Args:
            detection: VCP detection

        Returns:
            Enhanced alert or None if filtered
        """
        # Get ML prediction
        ml_result = await self.get_ml_prediction(detection.symbol)

        if not ml_result:
            logger.warning(f"No ML prediction for {detection.symbol}, using default")
            ml_result = {
                "probability": 0.15,
                "prediction": 0,
                "model_version": "unknown"
            }

        ml_probability = ml_result.get('probability', 0.15)
        priority = self.determine_priority(ml_probability)

        # Filter out low-confidence alerts
        if priority == AlertPriority.FILTERED:
            logger.info(f"Filtered {detection.symbol} (prob: {ml_probability:.3f})")
            return None

        # Create enhanced alert
        enhanced_alert = MLEnhancedAlert(
            symbol=detection.symbol,
            detection_time=detection.detection_time,
            pattern_type=detection.pattern_type,
            vcp_score=detection.vcp_score,
            ml_probability=ml_probability,
            ml_prediction=ml_result.get('prediction', 0),
            priority=priority,
            price=detection.price,
            volume=detection.volume,
            model_version=ml_result.get('model_version', 'unknown'),
            confidence_level=self._get_confidence_level(ml_probability)
        )

        logger.info(
            f"Enhanced alert: {enhanced_alert.symbol} - "
            f"Priority: {priority.value}, ML Prob: {ml_probability:.3f}"
        )

        return enhanced_alert

    def _get_confidence_level(self, probability: float) -> str:
        """Get human-readable confidence level"""
        if probability >= 0.7:
            return "Very High"
        elif probability >= 0.5:
            return "High"
        elif probability >= 0.3:
            return "Medium"
        else:
            return "Low"

    async def send_telegram_alert(self, alert: MLEnhancedAlert) -> bool:
        """
        Send alert via Telegram

        Args:
            alert: Enhanced alert to send

        Returns:
            True if sent successfully
        """
        # TODO: Integrate with existing Telegram bot
        # For now, just log
        message = self._format_telegram_message(alert)
        logger.info(f"Telegram Alert:\n{message}")
        return True

    async def send_gmail_alert(self, alert: MLEnhancedAlert) -> bool:
        """
        Send alert via Gmail

        Args:
            alert: Enhanced alert to send

        Returns:
            True if sent successfully
        """
        # TODO: Integrate with existing Gmail system
        # For now, just log
        logger.info(f"Gmail Alert: {alert.symbol} - {alert.priority.value}")
        return True

    def _format_telegram_message(self, alert: MLEnhancedAlert) -> str:
        """Format alert message for Telegram"""
        emoji = {
            AlertPriority.CRITICAL: "🚨",
            AlertPriority.HIGH: "⚠️",
            AlertPriority.MEDIUM: "📊",
            AlertPriority.LOW: "ℹ️"
        }.get(alert.priority, "📈")

        message = f"""
{emoji} **ML-Enhanced VCP Alert**

**Symbol**: {alert.symbol}
**Priority**: {alert.priority.value.upper()}
**ML Probability**: {alert.ml_probability:.1%} ({alert.confidence_level})
**VCP Score**: {alert.vcp_score:.2f}
**Pattern**: {alert.pattern_type}

**Market Data**:
• Price: ₹{alert.price:.2f}
• Volume: {alert.volume:,}

**Model**: {alert.model_version}
**Time**: {alert.detection_time.strftime('%Y-%m-%d %H:%M:%S')}

🎯 Action: {'STRONG BUY' if alert.priority == AlertPriority.CRITICAL else 'Consider' if alert.priority == AlertPriority.HIGH else 'Monitor'}
        """.strip()

        return message

    async def process_detections(self):
        """
        Main processing loop - fetch VCP detections and enhance with ML
        """
        logger.info("Starting detection processing...")

        # Get recent VCP detections
        detections = await self.get_recent_vcp_detections(
            minutes=self.polling_interval
        )

        if not detections:
            logger.info("No new detections to process")
            return

        # Process each detection
        enhanced_alerts = []

        for detection in detections:
            enhanced_alert = await self.enhance_detection_with_ml(detection)

            if enhanced_alert:
                enhanced_alerts.append(enhanced_alert)

        # Send alerts
        logger.info(f"Sending {len(enhanced_alerts)} enhanced alerts...")

        for alert in enhanced_alerts:
            # Send via configured channels
            await self.send_telegram_alert(alert)

            # Send Gmail for high-priority alerts
            if alert.priority in [AlertPriority.CRITICAL, AlertPriority.HIGH]:
                await self.send_gmail_alert(alert)

        logger.info(f"Processed {len(detections)} detections, sent {len(enhanced_alerts)} alerts")

    async def run(self):
        """
        Run the ML Alert Bridge continuously
        """
        logger.info("ML Alert Bridge started")
        logger.info(f"Polling interval: {self.polling_interval}s")

        while True:
            try:
                await self.process_detections()

            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)

            # Wait before next poll
            await asyncio.sleep(self.polling_interval)


async def main():
    """Main entry point"""
    bridge = MLAlertBridge(
        vcp_db_path="/Users/srijan/vcp_clean_test/vcp/vcp_trading_local.db",
        ml_api_url="http://localhost:8002",  # Use localhost for testing
        min_ml_threshold=0.15,
        polling_interval=60  # Check every 60 seconds
    )

    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
