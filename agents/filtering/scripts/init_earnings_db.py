#!/usr/bin/env python3
"""
Initialize Earnings Calendar and Mapping Databases

This script sets up the databases required for BSE filtering:
1. Earnings calendar database (earnings_calendar.db)
2. BSE-NSE mapping database (bse_nse_mapping.db)

Run this once before using the BSE filtering system.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.filtering.tools.bse_earnings_calendar_tool import BSEEarningsCalendarTool
from agents.filtering.tools.stock_filter_by_earnings_tool import StockFilterByEarningsTool
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def init_databases():
    """Initialize all required databases"""
    print("\n" + "="*70)
    print("  EARNINGS CALENDAR & MAPPING DATABASE INITIALIZATION")
    print("="*70 + "\n")

    # Initialize earnings calendar database
    print("📊 Initializing earnings calendar database...")
    earnings_tool = BSEEarningsCalendarTool(db_path="data/earnings_calendar.db")
    print("✅ Earnings calendar database initialized")
    print(f"   Location: {earnings_tool.db_path}")

    # Initialize BSE-NSE mapping database
    print("\n🗺️  Initializing BSE-NSE mapping database...")
    filter_tool = StockFilterByEarningsTool(mapping_db_path="data/bse_nse_mapping.db")
    print("✅ Mapping database initialized")
    print(f"   Location: {filter_tool.mapping_db_path}")

    # Load Nifty 50 mappings
    print("\n📥 Loading Nifty 50 BSE-NSE mappings...")
    filter_tool.load_nifty_mappings()

    # Get coverage statistics
    coverage = filter_tool.get_mapping_coverage()
    print(f"✅ Mappings loaded:")
    print(f"   Total mappings: {coverage['total_mappings']}")
    print(f"   Unique NSE symbols: {coverage['unique_nse_symbols']}")
    print(f"   Unique BSE codes: {coverage['unique_bse_codes']}")

    # Verify earnings database
    print("\n🔍 Verifying earnings database...")
    import sqlite3
    conn = sqlite3.connect(str(earnings_tool.db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM earnings_calendar")
    count = cursor.fetchone()[0]
    print(f"✅ Earnings calendar: {count} announcements cached")

    conn.close()

    print("\n" + "="*70)
    print("  INITIALIZATION COMPLETE!")
    print("="*70)

    print("\n✨ Next steps:")
    print("   1. Warm the earnings cache: agent.warm_earnings_cache()")
    print("   2. Add more BSE-NSE mappings as needed")
    print("   3. Integrate with backtest_with_angel.py")

    print("\n📚 Usage example:")
    print("""
    from agents.filtering.bse_filtering_agent import BSEFilteringAgent

    agent = BSEFilteringAgent()
    result = agent.filter_universe_by_earnings(
        original_universe=['RELIANCE', 'TCS', 'INFY', ...],
        lookforward_days=7
    )

    print(f"Filtered: {result['original_size']} → {result['filtered_size']} stocks")
    """)

    print("\n✅ Setup complete! Databases are ready to use.\n")


if __name__ == "__main__":
    try:
        init_databases()
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
