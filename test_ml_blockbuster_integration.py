#!/usr/bin/env python3
"""
TEST ML-BLOCKBUSTER INTEGRATION

This script verifies that the ML system now includes blockbuster features
in its training pipeline.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_blockbuster_features():
    """Check if blockbuster features are available"""
    features_db = Path("data/features/blockbuster_features.db")

    if not features_db.exists():
        logger.error(f"❌ Blockbuster features database not found at {features_db}")
        return False

    conn = sqlite3.connect(features_db)

    # Check table structure
    cursor = conn.execute("PRAGMA table_info(blockbuster_features)")
    columns = [row[1] for row in cursor.fetchall()]

    expected_columns = [
        'is_blockbuster', 'blockbuster_score', 'revenue_yoy_growth',
        'pat_yoy_growth', 'momentum_score', 'percentile_rank'
    ]

    missing = [col for col in expected_columns if col not in columns]
    if missing:
        logger.error(f"❌ Missing columns: {missing}")
        return False

    # Get statistics
    stats = pd.read_sql("""
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT symbol) as unique_symbols,
            SUM(is_blockbuster) as blockbusters,
            AVG(blockbuster_score) as avg_score,
            MAX(blockbuster_score) as max_score
        FROM blockbuster_features
    """, conn)

    conn.close()

    logger.info("✅ Blockbuster features database found and valid")
    logger.info(f"   - Total records: {stats['total_records'].iloc[0]:,}")
    logger.info(f"   - Unique symbols: {stats['unique_symbols'].iloc[0]:,}")
    logger.info(f"   - Blockbusters: {stats['blockbusters'].iloc[0]:,}")
    logger.info(f"   - Avg score: {stats['avg_score'].iloc[0]:.2f}")
    logger.info(f"   - Max score: {stats['max_score'].iloc[0]:.2f}")

    return True


def test_feature_engineer_integration():
    """Test if MLFeatureEngineerAgent includes blockbuster features"""
    try:
        from agents.ml.ml_feature_engineer import MLFeatureEngineerAgent

        # Initialize the agent
        agent = MLFeatureEngineerAgent(db_base_path="data")

        # Check if blockbuster extractor is initialized
        if not hasattr(agent, 'blockbuster_extractor'):
            logger.error("❌ MLFeatureEngineerAgent doesn't have blockbuster_extractor")
            return False

        logger.info("✅ MLFeatureEngineerAgent has blockbuster_extractor initialized")

        # Check if blockbuster features path is defined
        if 'blockbuster_features_db' not in agent.paths:
            logger.error("❌ blockbuster_features_db path not defined")
            return False

        logger.info("✅ blockbuster_features_db path is defined")
        return True

    except ImportError as e:
        logger.error(f"❌ Failed to import MLFeatureEngineerAgent: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing feature engineer: {e}")
        return False


def check_integration_with_ml_pipeline():
    """Check if blockbuster features can be joined with other features"""

    # Check if we can join blockbuster features with technical features
    blockbuster_db = Path("data/features/blockbuster_features.db")
    technical_db = Path("data/features/technical_features.db")

    if not blockbuster_db.exists() or not technical_db.exists():
        logger.warning("⚠️ Cannot test join - databases don't exist yet")
        return None

    # Try to join on common keys
    conn_b = sqlite3.connect(blockbuster_db)
    conn_t = sqlite3.connect(technical_db)

    blockbuster_df = pd.read_sql("""
        SELECT symbol, date, is_blockbuster, blockbuster_score
        FROM blockbuster_features
        LIMIT 10
    """, conn_b)

    technical_df = pd.read_sql("""
        SELECT bse_code as symbol, date, rsi_14, macd_signal
        FROM technical_features
        LIMIT 10
    """, conn_t)

    conn_b.close()
    conn_t.close()

    # Try to merge
    if not blockbuster_df.empty and not technical_df.empty:
        try:
            merged = pd.merge(
                technical_df,
                blockbuster_df,
                on=['symbol', 'date'],
                how='inner'
            )

            if not merged.empty:
                logger.info(f"✅ Successfully joined blockbuster with technical features ({len(merged)} records)")
                logger.info(f"   Columns: {list(merged.columns)}")
                return True
            else:
                logger.warning("⚠️ Join produced no results (might be no overlapping data)")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to join features: {e}")
            return False

    return None


def main():
    """Run all integration tests"""
    print("="*80)
    print("ML-BLOCKBUSTER INTEGRATION TEST")
    print("="*80)
    print()

    results = []

    # Test 1: Check blockbuster features database
    print("1. Checking blockbuster features database...")
    results.append(check_blockbuster_features())
    print()

    # Test 2: Check MLFeatureEngineerAgent integration
    print("2. Testing MLFeatureEngineerAgent integration...")
    results.append(test_feature_engineer_integration())
    print()

    # Test 3: Check feature joining capability
    print("3. Testing feature joining capability...")
    join_result = check_integration_with_ml_pipeline()
    if join_result is not None:
        results.append(join_result)
    print()

    # Summary
    print("="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r)
    total = len(results)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print()
        print("The ML system is now successfully integrated with blockbuster features!")
        print("Next steps:")
        print("1. Run ML training with the new features")
        print("2. Compare model performance with/without blockbuster features")
        print("3. Create dual-target models for both circuits and blockbusters")
    else:
        print(f"⚠️ SOME TESTS FAILED ({passed}/{total} passed)")
        print()
        print("Please fix the failed tests before proceeding with ML training.")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)