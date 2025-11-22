#!/usr/bin/env python3
"""
Reclassify and Reprocess All Announcements

This script:
1. Reclassifies ALL announcements with the fixed classifier
2. Extracts intelligence from newly identified EARNINGS/ORDER/CAPEX announcements
3. Shows statistics on reclassification results
"""
import sys
import logging
import sqlite3
from pathlib import Path

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

DB_PATH = "data/announcement_intelligence.db"

def reclassify_all_announcements():
    """Reclassify all announcements with fixed classifier"""
    logger.info("=" * 80)
    logger.info("RECLASSIFYING ALL ANNOUNCEMENTS")
    logger.info("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all announcements
    cursor.execute("SELECT * FROM announcements ORDER BY timestamp DESC")
    announcements = [dict(row) for row in cursor.fetchall()]

    logger.info(f"Found {len(announcements)} total announcements")

    # Track changes
    classifier = AnnouncementClassifier()
    category_changes = {}

    for ann in announcements:
        # Note: 'category' field in DB stores the classified category
        old_category = ann.get('category', 'UNKNOWN')
        new_category = classifier.classify(ann)

        if old_category != new_category:
            logger.info(f"   CHANGED: {ann['company_name'][:30]}: {old_category} -> {new_category}")
            category_changes[ann['id']] = (old_category, new_category)

        # Update category in database
        cursor.execute("""
            UPDATE announcements
            SET category = ?
            WHERE id = ?
        """, (new_category, ann['id']))

    conn.commit()

    # Show summary
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ Reclassification Complete: {len(category_changes)} announcements changed")
    logger.info("=" * 80)

    # Count by category
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM announcements
        GROUP BY category
        ORDER BY count DESC
    """)

    logger.info("")
    logger.info("Category Distribution:")
    for row in cursor.fetchall():
        logger.info(f"   {row[0]}: {row[1]} announcements")

    conn.close()
    return len(category_changes)

def extract_missing_intelligence():
    """Extract intelligence from newly identified actionable announcements"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("EXTRACTING INTELLIGENCE FROM NEWLY CLASSIFIED ANNOUNCEMENTS")
    logger.info("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get announcements that:
    # 1. Are now classified as EARNINGS/ORDER_WIN/CAPEX
    # 2. Don't have extracted intelligence yet
    cursor.execute("""
        SELECT a.*
        FROM announcements a
        LEFT JOIN extracted_intelligence e ON a.id = e.announcement_id
        WHERE a.category IN ('EARNINGS', 'ORDER_WIN', 'CAPEX')
          AND e.announcement_id IS NULL
        ORDER BY a.timestamp DESC
    """)

    unprocessed = [dict(row) for row in cursor.fetchall()]
    logger.info(f"Found {len(unprocessed)} unprocessed announcements to extract")

    extractor = IntelligenceExtractor()
    success_count = 0

    for ann in unprocessed:
        try:
            logger.info(f"   Processing: {ann['company_name']} - {ann['category']}")

            result = extractor.extract_intelligence(ann, ann['category'])

            # Save intelligence
            cursor.execute("""
                INSERT OR REPLACE INTO extracted_intelligence
                (announcement_id, category, extracted_data, status, extracted_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (
                ann['id'],
                ann['category'],
                result.get('extracted_data'),
                result.get('status')
            ))

            if result.get('status') == 'success':
                success_count += 1
                logger.info(f"   ✅ Extracted: {result['extracted_data']}")
            else:
                logger.info(f"   ⚠️ Skipped or failed")

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
    logger.info("")
    logger.info("🧠 ANNOUNCEMENT RECLASSIFICATION AND INTELLIGENCE EXTRACTION")
    logger.info("")

    # Step 1: Reclassify all announcements
    changes = reclassify_all_announcements()

    # Step 2: Extract intelligence from newly classified announcements
    if changes > 0:
        extracted = extract_missing_intelligence()
    else:
        logger.info("")
        logger.info("No category changes detected - skipping intelligence extraction")
        extracted = 0

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ COMPLETE: {changes} reclassified, {extracted} new extractions")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
