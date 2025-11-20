"""
MLFeatureEngineerAgent - Orchestrates feature engineering pipeline

This agent coordinates the extraction of features from various domains:
- Financial (Revenue, Profit, Margins)
- Technical (RSI, MACD, Bollinger Bands)
- Sentiment (Momentum, Reaction, Volatility)
- Seasonality (Quarterly patterns)

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import logging
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from .financial_feature_extractor import FinancialFeatureExtractor
from .technical_feature_extractor import TechnicalFeatureExtractor
from .sentiment_feature_extractor import SentimentFeatureExtractor
from .seasonality_feature_extractor import SeasonalityFeatureExtractor
from agents.ml.fundamental_analysis_agent import FundamentalAnalysisAgent
from agents.ml.blockbuster_feature_extractor import MLBlockbusterFeatureExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "agent": "MLFeatureEngineerAgent", "message": "%(message)s"}',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class FeatureEngineerConfig:
    """Configuration for feature engineering"""
    db_base_path: str
    batch_size: int = 100

class MLFeatureEngineerAgent:
    """
    Orchestrates feature extraction for the ML pipeline.
    
    Responsibilities:
    1. Manage feature databases
    2. Coordinate batch feature extraction
    3. Ensure data consistency across feature sets
    """

    def __init__(self, db_base_path: str):
        """
        Initialize MLFeatureEngineerAgent
        
        Args:
            db_base_path: Base directory for databases
        """
        self.config = FeatureEngineerConfig(db_base_path=db_base_path)
        
        # Define database paths
        self.paths = {
            'financials_db': os.path.join(db_base_path, "historical_financials.db"),
            'price_db': os.path.join(db_base_path, "price_movements.db"),
            'labels_db': os.path.join(db_base_path, "upper_circuit_labels.db"),
            'historical_prices_db': os.path.join(db_base_path, "price_movements.db"), # Reusing price_movements as historical source
            'financial_features_db': os.path.join(db_base_path, "features", "financial_features.db"),
            'technical_features_db': os.path.join(db_base_path, "features", "technical_features.db"),
            'sentiment_features_db': os.path.join(db_base_path, "features", "sentiment_features.db"),
            'seasonality_features_db': os.path.join(db_base_path, "features", "seasonality_features.db"),
            'fundamental_features_db': os.path.join(db_base_path, "features", "fundamental_features.db"),
            'blockbuster_features_db': os.path.join(db_base_path, "features", "blockbuster_features.db")
        }
        
        # Ensure features directory exists
        os.makedirs(os.path.dirname(self.paths['financial_features_db']), exist_ok=True)
        
        # Initialize extractors (lazy loading could be implemented if needed)
        self._initialize_extractors()
        
        logger.info(f"MLFeatureEngineerAgent initialized with DB path: {db_base_path}")

    def _initialize_extractors(self):
        """Initialize all feature extractors"""
        try:
            self.financial_extractor = FinancialFeatureExtractor(
                financials_db_path=self.paths['financials_db'],
                output_db_path=self.paths['financial_features_db']
            )
            
            self.technical_extractor = TechnicalFeatureExtractor(
                price_db_path=self.paths['price_db'],
                output_db_path=self.paths['technical_features_db']
            )
            
            self.sentiment_extractor = SentimentFeatureExtractor(
                price_db_path=self.paths['price_db'],
                labels_db_path=self.paths['labels_db'],
                output_db_path=self.paths['sentiment_features_db']
            )
            
            self.seasonality_extractor = SeasonalityFeatureExtractor(
                output_db_path=self.paths['seasonality_features_db'],
                labels_db_path=self.paths['labels_db']
            )
            
            # Initialize Fundamental Analysis Agent
            self.fundamental_agent = FundamentalAnalysisAgent(
                db_path=self.paths['fundamental_features_db']
            )

            # Initialize Blockbuster Feature Extractor
            self.blockbuster_extractor = MLBlockbusterFeatureExtractor()

            logger.info("All feature extractors initialized successfully (including blockbuster features)")
            
        except Exception as e:
            logger.error(f"Failed to initialize extractors: {e}")
            raise

    def engineer_batch_features(self, samples: List[Dict[str, str]], feature_dbs: Optional[Dict[str, str]] = None) -> Dict[str, int]:
        """
        Engineer features for a batch of samples.
        
        Args:
            samples: List of dicts with 'bse_code' and 'date'
            feature_dbs: Optional override for feature DB paths
            
        Returns:
            Dict with counts of features extracted per category
        """
        logger.info(f"Starting batch feature engineering for {len(samples)} samples")
        
        results = {
            'financial': 0,
            'technical': 0,
            'sentiment': 0,
            'seasonality': 0,
            'fundamental': 0,
            'blockbuster': 0
        }
        
        try:
            # 1. Financial Features
            logger.info("Extracting financial features...")
            fin_df = self.financial_extractor.extract_features_batch(samples)
            results['financial'] = len(fin_df)
            
            # 2. Technical Features
            logger.info("Extracting technical features...")
            tech_df = self.technical_extractor.extract_features_batch(samples)
            results['technical'] = len(tech_df)
            
            # 3. Sentiment Features
            logger.info("Extracting sentiment features...")
            sent_df = self.sentiment_extractor.extract_features_batch(samples)
            results['sentiment'] = len(sent_df)
            
            # 4. Seasonality Features
            logger.info("Extracting seasonality features...")
            seas_df = self.seasonality_extractor.extract_features_batch(samples)
            results['seasonality'] = len(seas_df)
            
            # 5. Fundamental Features (Simulated extraction for samples)
            logger.info("Extracting fundamental features...")
            # Group by bse_code to minimize DB opens
            bse_codes = set(s['bse_code'] for s in samples)
            # Use a fixed date range for simulation/fetching
            start_date = min(s['date'] for s in samples)
            end_date = max(s['date'] for s in samples)

            for code in bse_codes:
                self.fundamental_agent.analyze_company(code, start_date, end_date)
            results['fundamental'] = len(samples) # Assuming success

            # 6. Blockbuster Features
            logger.info("Extracting blockbuster features...")
            # Run the blockbuster feature extraction
            blockbuster_df = self.blockbuster_extractor.extract_all_features()
            self.blockbuster_extractor.save_features(blockbuster_df)
            results['blockbuster'] = len(blockbuster_df)

            logger.info(f"Batch engineering complete. Results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error during batch feature engineering: {e}")
            raise

    def get_feature_stats(self) -> Dict[str, int]:
        """Get statistics about extracted features"""
        # This would query the DBs to get counts
        # Placeholder implementation
        return {
            'financial_count': 0,
            'technical_count': 0,
            'sentiment_count': 0,
            'seasonality_count': 0
        }
