"""
MLLabelQualityAgent - Improves label quality for ML training

This agent is responsible for:
1. Re-labeling samples with proper circuit thresholds
2. Validating label quality
3. Tracking label distribution
4. Identifying real circuit breaker events

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import logging
import sqlite3
import os
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

# Import circuit identifier tool
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.circuit_identifier import identify_circuits, get_circuit_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{\"timestamp\": \"%(asctime)s\", \"level\": \"%(levelname)s\", \"agent\": \"MLLabelQualityAgent\", \"message\": \"%(message)s\"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class LabelQualityConfig:
    """Configuration for label quality agent"""
    db_base_path: str
    circuit_threshold: float = 10.0  # 10% for real circuits
    backup_labels: bool = True


class MLLabelQualityAgent:
    """
    Orchestrates label quality improvement.
    """

    def __init__(self, db_base_path: str, circuit_threshold: float = 10.0):
        """
        Initialize MLLabelQualityAgent
        
        Args:
            db_base_path: Base directory for data
            circuit_threshold: Minimum price change % for circuit (default: 10.0)
        """
        self.config = LabelQualityConfig(
            db_base_path=db_base_path,
            circuit_threshold=circuit_threshold
        )
        
        self.price_db = os.path.join(db_base_path, "price_movements.db")
        self.labels_db = os.path.join(db_base_path, "upper_circuit_labels.db")
        
        logger.info(f"MLLabelQualityAgent initialized with threshold={circuit_threshold}%")

    def relabel_circuits(self) -> Dict:
        """
        Re-label all samples with proper circuit threshold.
        
        Returns:
            Dict with relabeling results
        """
        logger.info(f"Starting re-labeling with {self.config.circuit_threshold}% threshold...")
        
        # Backup existing labels if requested
        if self.config.backup_labels:
            self._backup_labels()
        
        # Identify real circuits
        circuits = identify_circuits(
            self.price_db,
            threshold=self.config.circuit_threshold
        )
        
        logger.info(f"Identified {len(circuits)} circuit events")
        
        # Get ALL price movements to create negative labels
        conn = sqlite3.connect(self.price_db)
        cursor_price = conn.cursor()
        cursor_price.execute("""
            SELECT p1.bse_code, p2.date, 
                   ((p2.close - p1.close) / p1.close * 100) as pct_change
            FROM price_movements p1
            JOIN price_movements p2 
                ON p1.bse_code = p2.bse_code 
                AND date(p2.date) = date(p1.date, '+1 day')
            WHERE p1.close > 0
        """)
        all_movements = cursor_price.fetchall()
        conn.close()
        
        logger.info(f"Found {len(all_movements)} total price movements")
        
        # Create set of circuit dates for quick lookup
        circuit_set = {(c['bse_code'], c['circuit_date']) for c in circuits}
        
        # Clear existing labels
        conn = sqlite3.connect(self.labels_db)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM upper_circuit_labels")
        conn.commit()
        
        # Insert all labels (positive and negative)
        positive_count = 0
        negative_count = 0
        
        for bse_code, date, pct_change in all_movements:
            try:
                is_circuit = (bse_code, date) in circuit_set
                label = 1 if is_circuit else 0
                
                cursor.execute("""
                    INSERT OR REPLACE INTO upper_circuit_labels
                    (bse_code, earnings_date, next_day_date, price_change_pct, hit_circuit, label)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    bse_code,
                    date,
                    date,
                    pct_change,
                    1 if is_circuit else 0,
                    label
                ))
                
                if label == 1:
                    positive_count += 1
                else:
                    negative_count += 1
                    
            except Exception as e:
                logger.error(f"Error inserting label: {e}")
        
        conn.commit()
        conn.close()
        
        # Get label statistics
        stats = self.get_label_stats()
        
        logger.info(f"Re-labeling complete: {positive_count} positive, {negative_count} negative labels")
        
        return {
            "circuits_identified": len(circuits),
            "labels_created": positive_count + negative_count,
            "positive_labels": positive_count,
            "negative_labels": negative_count,
            "label_stats": stats
        }

    def _backup_labels(self):
        """Backup existing labels to a timestamped table"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table = f"upper_circuit_labels_backup_{timestamp}"
        
        conn = sqlite3.connect(self.labels_db)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"""
                CREATE TABLE {backup_table} AS 
                SELECT * FROM upper_circuit_labels
            """)
            conn.commit()
            logger.info(f"Labels backed up to {backup_table}")
        except Exception as e:
            logger.warning(f"Could not backup labels: {e}")
        finally:
            conn.close()

    def get_label_stats(self) -> Dict:
        """
        Get statistics about current labels.
        
        Returns:
            Dict with label statistics
        """
        conn = sqlite3.connect(self.labels_db)
        cursor = conn.cursor()
        
        # Total labels
        cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels")
        total = cursor.fetchone()[0]
        
        # Positive labels
        cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels WHERE label = 1")
        positive = cursor.fetchone()[0]
        
        # Negative labels
        negative = total - positive
        
        # Average price change for positives
        cursor.execute("""
            SELECT AVG(price_change_pct), MIN(price_change_pct), MAX(price_change_pct)
            FROM upper_circuit_labels 
            WHERE label = 1
        """)
        row = cursor.fetchone()
        avg_change, min_change, max_change = row if row[0] else (0, 0, 0)
        
        conn.close()
        
        stats = {
            "total_labels": total,
            "positive_labels": positive,
            "negative_labels": negative,
            "positive_ratio": positive / total if total > 0 else 0,
            "avg_price_change": float(avg_change) if avg_change else 0,
            "min_price_change": float(min_change) if min_change else 0,
            "max_price_change": float(max_change) if max_change else 0
        }
        
        return stats

    def validate_labels(self) -> Dict:
        """
        Validate label quality.
        
        Returns:
            Dict with validation results
        """
        logger.info("Validating label quality...")
        
        stats = self.get_label_stats()
        
        # Check for issues
        issues = []
        
        # Check class balance
        if stats['positive_ratio'] < 0.01:
            issues.append("Very low positive ratio (<1%)")
        elif stats['positive_ratio'] > 0.5:
            issues.append("Very high positive ratio (>50%)")
        
        # Check minimum positive samples
        if stats['positive_labels'] < 50:
            issues.append(f"Insufficient positive samples ({stats['positive_labels']} < 50)")
        
        # Check price change range
        if stats['avg_price_change'] < self.config.circuit_threshold:
            issues.append(f"Average price change below threshold")
        
        validation = {
            "valid": len(issues) == 0,
            "issues": issues,
            "stats": stats,
            "recommendations": []
        }
        
        # Add recommendations
        if stats['positive_labels'] < 50:
            validation['recommendations'].append("Collect more historical data")
        if stats['positive_ratio'] < 0.05:
            validation['recommendations'].append("Lower circuit threshold or use oversampling")
        
        return validation

    def identify_real_circuits(self) -> List[Dict]:
        """
        Identify actual circuit breaker events.
        
        Returns:
            List of circuit events
        """
        circuits = identify_circuits(
            self.price_db,
            threshold=self.config.circuit_threshold
        )
        
        logger.info(f"Identified {len(circuits)} real circuit events")
        
        return circuits


if __name__ == "__main__":
    # Demo usage
    print("=== MLLabelQualityAgent Demo ===\n")
    
    agent = MLLabelQualityAgent(
        db_base_path="/Users/srijan/Desktop/aksh/data",
        circuit_threshold=10.0
    )
    
    # Get current stats
    stats = agent.get_label_stats()
    print(f"Current Labels:")
    print(f"  Total: {stats['total_labels']}")
    print(f"  Positive: {stats['positive_labels']} ({stats['positive_ratio']*100:.1f}%)")
    print(f"  Negative: {stats['negative_labels']}")
    
    # Validate
    validation = agent.validate_labels()
    print(f"\nValidation: {'✅ PASS' if validation['valid'] else '❌ FAIL'}")
    if validation['issues']:
        print("Issues:")
        for issue in validation['issues']:
            print(f"  - {issue}")
