#!/usr/bin/env python3
"""
Historical Intelligence Processor

Processes all historical announcements to extract intelligence data:
1. Retries failed extractions
2. Processes unprocessed earnings/order/capex announcements
3. Optionally fetches older historical data from BSE

Can be run standalone or as a scheduled job.
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.intelligence.announcement_classifier import AnnouncementClassifier
from src.intelligence.intelligence_extractor import IntelligenceExtractor
from src.data.announcement_db import AnnouncementIntelligenceDB
from src.data.corporate_announcement_fetcher import CorporateAnnouncementFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("historical_intelligence_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HistoricalIntelligenceProcessor:
    """Process historical announcements for intelligence extraction"""

    def __init__(self):
        self.classifier = AnnouncementClassifier()
        self.extractor = IntelligenceExtractor()
        self.db = AnnouncementIntelligenceDB()
        self.fetcher = CorporateAnnouncementFetcher()

    def retry_failed_extractions(self) -> int:
        """Retry all failed intelligence extractions"""
        logger.info("🔄 Retrying failed extractions...")

        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all failed extractions with announcement details
        cursor.execute("""
            SELECT a.*, e.category as extraction_category
            FROM announcements a
            JOIN extracted_intelligence e ON a.id = e.announcement_id
            WHERE e.status = 'failed'
            ORDER BY a.timestamp DESC
        """)

        failed = [dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"   Found {len(failed)} failed extractions to retry")

        success_count = 0
        for ann in failed:
            try:
                logger.info(f"   Retrying: {ann['company_name']} - {ann['extraction_category']}")

                result = self.extractor.extract_intelligence(
                    ann,
                    ann['extraction_category']
                )

                # Update the extraction
                self.db.save_intelligence(
                    ann['id'],
                    ann['extraction_category'],
                    result.get('extracted_data'),
                    result.get('status')
                )

                if result.get('status') == 'success':
                    success_count += 1
                    logger.info(f"   ✅ Success: {result['extracted_data']}")
                else:
                    logger.warning(f"   ❌ Still failed")

            except Exception as e:
                logger.error(f"   ❌ Error retrying {ann['company_name']}: {e}")

        logger.info(f"✅ Retry complete: {success_count}/{len(failed)} now successful")
        return success_count

    def process_unprocessed_announcements(self) -> int:
        """Process announcements that haven't been analyzed yet"""
        logger.info("📋 Processing unprocessed announcements...")

        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get unprocessed earnings/order/capex announcements
        cursor.execute("""
            SELECT a.*
            FROM announcements a
            LEFT JOIN extracted_intelligence e ON a.id = e.announcement_id
            WHERE a.category IN ('EARNINGS', 'ORDER_WIN', 'CAPEX')
              AND e.announcement_id IS NULL
            ORDER BY a.timestamp DESC
        """)

        unprocessed = [dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"   Found {len(unprocessed)} unprocessed announcements")

        success_count = 0
        for ann in unprocessed:
            try:
                logger.info(f"   Processing: {ann['company_name']} - {ann['category']}")

                result = self.extractor.extract_intelligence(ann, ann['category'])

                self.db.save_intelligence(
                    ann['id'],
                    ann['category'],
                    result.get('extracted_data'),
                    result.get('status')
                )

                if result.get('status') == 'success':
                    success_count += 1
                    logger.info(f"   ✅ Extracted: {result['extracted_data']}")
                else:
                    logger.warning(f"   ⚠️ Skipped or failed")

            except Exception as e:
                logger.error(f"   ❌ Error processing {ann['company_name']}: {e}")

        logger.info(f"✅ Processing complete: {success_count}/{len(unprocessed)} successful")
        return success_count

    def backfill_historical_data(self, days_back: int = 7) -> int:
        """Fetch and process historical announcements from BSE"""
        logger.info(f"📥 Backfilling {days_back} days of historical data...")

        from datetime import date
        total_new = 0

        for day_offset in range(days_back):
            target_date = date.today() - timedelta(days=day_offset)
            logger.info(f"   Fetching: {target_date}")

            try:
                announcements = self.fetcher.fetch_latest_announcements()

                new_count = 0
                for ann in announcements:
                    # Classify
                    category = self.classifier.classify(ann)
                    ann['category_derived'] = category

                    # Save (deduplicates automatically)
                    is_new = self.db.save_announcement(ann)

                    if is_new:
                        new_count += 1

                        # Extract intelligence if relevant
                        if category in [
                            AnnouncementClassifier.CAT_ORDER,
                            AnnouncementClassifier.CAT_CAPEX,
                            AnnouncementClassifier.CAT_EARNINGS
                        ]:
                            result = self.extractor.extract_intelligence(ann, category)
                            self.db.save_intelligence(
                                ann['id'],
                                category,
                                result.get('extracted_data'),
                                result.get('status')
                            )

                total_new += new_count
                logger.info(f"   Added {new_count} new announcements")

            except Exception as e:
                logger.error(f"   ❌ Error fetching {target_date}: {e}")

        logger.info(f"✅ Backfill complete: {total_new} new announcements added")
        return total_new


def main():
    parser = argparse.ArgumentParser(
        description='Process historical announcement intelligence'
    )
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='Retry all failed extractions'
    )
    parser.add_argument(
        '--process-unprocessed',
        action='store_true',
        help='Process unprocessed earnings announcements'
    )
    parser.add_argument(
        '--backfill',
        type=int,
        metavar='DAYS',
        help='Backfill N days of historical data from BSE'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all processing (retry + unprocessed + 7 days backfill)'
    )

    args = parser.parse_args()

    # If no args, default to --all
    if not any([args.retry_failed, args.process_unprocessed, args.backfill, args.all]):
        args.all = True

    logger.info("="*80)
    logger.info("🧠 HISTORICAL INTELLIGENCE PROCESSOR")
    logger.info("="*80)
    logger.info("")

    processor = HistoricalIntelligenceProcessor()

    total_successes = 0

    # Run requested operations
    if args.all or args.retry_failed:
        logger.info("")
        logger.info("STEP 1: Retrying Failed Extractions")
        logger.info("-" * 80)
        total_successes += processor.retry_failed_extractions()

    if args.all or args.process_unprocessed:
        logger.info("")
        logger.info("STEP 2: Processing Unprocessed Announcements")
        logger.info("-" * 80)
        total_successes += processor.process_unprocessed_announcements()

    if args.backfill or args.all:
        days = args.backfill if args.backfill else 7
        logger.info("")
        logger.info(f"STEP 3: Backfilling {days} Days of Historical Data")
        logger.info("-" * 80)
        processor.backfill_historical_data(days)

    logger.info("")
    logger.info("="*80)
    logger.info(f"✅ PROCESSING COMPLETE - {total_successes} new successful extractions")
    logger.info("="*80)


if __name__ == "__main__":
    main()
