#!/usr/bin/env python3
"""
Migrate Historical Earnings Announcements to Intelligence System

This script:
1. Reads all announcements from vcp_trading_local.db
2. Classifies each announcement
3. Imports into announcement_intelligence.db
4. Extracts intelligence from actionable categories (EARNINGS, ORDER_WIN, CAPEX)
"""
import sys
import logging
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.intelligence.announcement_classifier import AnnouncementClassifier
from src.intelligence.intelligence_extractor import IntelligenceExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SOURCE_DB = "/home/ubuntu/vcp/vcp_trading_local.db"
TARGET_DB = "data/announcement_intelligence.db"

def generate_announcement_id(company_name: str, bse_code: str, timestamp: str) -> str:
    """Generate unique ID for announcement"""
    unique_str = f"{company_name}_{bse_code}_{timestamp}"
    return hashlib.md5(unique_str.encode()).hexdigest()

def migrate_announcements():
    """Migrate all announcements from source to target database"""
    logger.info("=" * 80)
    logger.info("MIGRATING HISTORICAL ANNOUNCEMENTS")
    logger.info("=" * 80)

    # Connect to both databases
    source_conn = sqlite3.connect(SOURCE_DB)
    source_conn.row_factory = sqlite3.Row
    source_cursor = source_conn.cursor()

    target_conn = sqlite3.connect(TARGET_DB)
    target_cursor = target_conn.cursor()

    # Get all announcements from source
    source_cursor.execute("""
        SELECT
            company_name,
            bse_code,
            alert_type,
            subject,
            pdf_url,
            received_timestamp
        FROM earnings_announcements
        ORDER BY received_timestamp DESC
    """)

    announcements = source_cursor.fetchall()
    logger.info(f"Found {len(announcements)} announcements in source database")

    # Initialize classifier
    classifier = AnnouncementClassifier()

    # Track statistics
    stats = {
        'total': len(announcements),
        'imported': 0,
        'duplicates': 0,
        'by_category': {}
    }

    for row in announcements:
        try:
            # Convert to dictionary
            ann_dict = {
                'company_name': row['company_name'],
                'bse_code': row['bse_code'],
                'title': row['subject'] or '',
                'category': row['alert_type'] or '',  # BSE category (not our classification)
                'description': '',
                'pdf_url': row['pdf_url'] or '',
                'timestamp': row['received_timestamp']
            }

            # Generate unique ID
            ann_id = generate_announcement_id(
                ann_dict['company_name'],
                ann_dict['bse_code'],
                ann_dict['timestamp']
            )

            # Check if already exists
            target_cursor.execute(
                "SELECT id FROM announcements WHERE id = ?",
                (ann_id,)
            )
            if target_cursor.fetchone():
                stats['duplicates'] += 1
                continue

            # Classify announcement
            classified_category = classifier.classify(ann_dict)

            # Track category stats
            stats['by_category'][classified_category] = \
                stats['by_category'].get(classified_category, 0) + 1

            # Insert into target database
            target_cursor.execute("""
                INSERT INTO announcements (
                    id, bse_code, company_name, category, title,
                    description, pdf_url, timestamp, processed, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ann_id,
                ann_dict['bse_code'],
                ann_dict['company_name'],
                classified_category,  # Our classified category
                ann_dict['title'],
                ann_dict['description'],
                ann_dict['pdf_url'],
                ann_dict['timestamp'],
                False,
                datetime.now().isoformat()
            ))

            stats['imported'] += 1

            # Log progress every 1000 records
            if stats['imported'] % 1000 == 0:
                logger.info(f"   Imported {stats['imported']:,} announcements...")

        except Exception as e:
            logger.error(f"Error processing announcement: {e}")
            continue

    target_conn.commit()

    # Close connections
    source_conn.close()
    target_conn.close()

    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ MIGRATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total announcements: {stats['total']:,}")
    logger.info(f"Imported: {stats['imported']:,}")
    logger.info(f"Duplicates skipped: {stats['duplicates']:,}")
    logger.info("")
    logger.info("Category Breakdown:")
    for category, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        logger.info(f"   {category}: {count:,}")

    return stats

def extract_intelligence_batch(limit: int = 100, skip_pdf: bool = False):
    """Extract intelligence from actionable announcements in batches"""
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"EXTRACTING INTELLIGENCE (Batch size: {limit})")
    logger.info("=" * 80)

    conn = sqlite3.connect(TARGET_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get unprocessed actionable announcements
    cursor.execute("""
        SELECT a.*
        FROM announcements a
        LEFT JOIN extracted_intelligence e ON a.id = e.announcement_id
        WHERE a.category IN ('EARNINGS', 'ORDER_WIN', 'CAPEX')
          AND e.announcement_id IS NULL
        ORDER BY a.timestamp DESC
        LIMIT ?
    """, (limit,))

    unprocessed = [dict(row) for row in cursor.fetchall()]
    logger.info(f"Found {len(unprocessed)} unprocessed announcements")

    if len(unprocessed) == 0:
        logger.info("No announcements to process")
        conn.close()
        return 0

    extractor = IntelligenceExtractor()
    success_count = 0

    for i, ann in enumerate(unprocessed, 1):
        try:
            logger.info(f"   [{i}/{len(unprocessed)}] {ann['company_name']} - {ann['category']}")

            result = extractor.extract_intelligence(ann, ann['category'])

            # Save intelligence
            # Convert dict to JSON string for database storage
            import json
            intelligence_json = json.dumps(result.get('extracted_data', {}))

            cursor.execute("""
                INSERT OR REPLACE INTO extracted_intelligence
                (announcement_id, category, intelligence_data, status, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (
                ann['id'],
                ann['category'],
                intelligence_json,
                result.get('status')
            ))

            if result.get('status') == 'success':
                success_count += 1

        except Exception as e:
            logger.error(f"   ❌ Error: {e}")

    conn.commit()
    conn.close()

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ Extraction Complete: {success_count}/{len(unprocessed)} successful")
    logger.info("=" * 80)

    return success_count

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Migrate historical announcements to intelligence system'
    )
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Migrate announcements from vcp_trading_local.db'
    )
    parser.add_argument(
        '--extract',
        type=int,
        metavar='LIMIT',
        help='Extract intelligence from N unprocessed announcements'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Migrate all announcements and extract intelligence (batch of 100)'
    )

    args = parser.parse_args()

    if not any([args.migrate, args.extract, args.all]):
        args.all = True

    logger.info("")
    logger.info("🧠 HISTORICAL ANNOUNCEMENT MIGRATION")
    logger.info("")

    if args.all or args.migrate:
        migrate_announcements()

    if args.all or args.extract:
        batch_size = args.extract if args.extract else 100
        extract_intelligence_batch(batch_size)

    logger.info("")
    logger.info("✅ COMPLETE")

if __name__ == "__main__":
    main()
