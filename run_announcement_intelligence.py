#!/usr/bin/env python3
"""
Run Announcement Intelligence System

Main loop that:
1. Fetches announcements from BSE
2. Classifies them
3. Extracts intelligence
4. Stores results
5. (Future) Triggers Alerts
"""

import time
import logging
import sys
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.corporate_announcement_fetcher import CorporateAnnouncementFetcher
from src.intelligence.announcement_classifier import AnnouncementClassifier
from src.intelligence.intelligence_extractor import IntelligenceExtractor
from src.data.announcement_db import AnnouncementIntelligenceDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("announcement_intelligence.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"\n🛑 Received signal {sig}, initiating graceful shutdown...")
    shutdown_requested = True

def main():
    global shutdown_requested
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting Corporate Announcement Intelligence System (CAIS)")
    logger.info("📊 Press Ctrl+C to stop gracefully")
    
    fetcher = CorporateAnnouncementFetcher()
    classifier = AnnouncementClassifier()
    extractor = IntelligenceExtractor()
    db = AnnouncementIntelligenceDB()
    
    POLL_INTERVAL = 60 # Seconds
    
    while not shutdown_requested:
        try:
            # 1. Fetch
            announcements = fetcher.fetch_latest_announcements()
            
            new_count = 0
            for ann in announcements:
                # Check shutdown flag between announcements
                if shutdown_requested:
                    break
                    
                # 2. Classify
                category = classifier.classify(ann)
                ann['category_derived'] = category
                
                # 3. Save (Deduplicate)
                is_new = db.save_announcement(ann)
                
                if is_new:
                    new_count += 1
                    logger.info(f"New Announcement: {ann['company_name']} - {category}")
                    
                    # 4. Extract Intelligence (if actionable)
                    if category in [AnnouncementClassifier.CAT_ORDER, AnnouncementClassifier.CAT_CAPEX, AnnouncementClassifier.CAT_EARNINGS]:
                        logger.info(f"   Extracting intelligence for {category}...")
                        result = extractor.extract_intelligence(ann, category)
                        
                        db.save_intelligence(ann['id'], category, result.get('extracted_data'), result.get('status'))
                        
                        if result.get('status') == 'success':
                            logger.info(f"   ✅ Intelligence Extracted: {result['extracted_data']}")
                            # TODO: Trigger Alert Here
                        else:
                            logger.warning(f"   ❌ Extraction Failed")
                    else:
                        # Mark as processed even if we don't extract (so we don't retry forever)
                        db.save_intelligence(ann['id'], category, {}, "skipped")
            
            if new_count == 0:
                logger.info("No new announcements.")
            
            # Sleep with periodic checks for shutdown
            for _ in range(POLL_INTERVAL):
                if shutdown_requested:
                    break
                time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Keyboard interrupt received, stopping CAIS...")
            shutdown_requested = True
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}", exc_info=True)
            if not shutdown_requested:
                logger.info(f"⏳ Retrying in {POLL_INTERVAL} seconds...")
                for _ in range(POLL_INTERVAL):
                    if shutdown_requested:
                        break
                    time.sleep(1)
    
    logger.info("✅ CAIS stopped gracefully")

if __name__ == "__main__":
    main()
