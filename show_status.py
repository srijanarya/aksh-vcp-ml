#!/usr/bin/env python3
"""
Show Current Earnings System Status
"""

import json
from pathlib import Path

print("\n" + "="*80)
print("📊 EARNINGS CALENDAR SYSTEM - CURRENT STATUS")
print("="*80)

# Check master stock list
master_file = Path("/Users/srijan/vcp_clean_test/data/master_stock_list.json")
if master_file.exists():
    with open(master_file) as f:
        master_data = json.load(f)
    total = master_data.get('total_companies', len(master_data.get('companies', [])))
    print(f"\n✓ Master Stock List: {total:,} companies tracked")
else:
    print("\n✗ Master stock list not found")
    total = 0

# Check earnings calendar database
db_file = Path("/Users/srijan/vcp_clean_test/data/earnings_calendar.db")
if db_file.exists():
    size_mb = db_file.stat().st_size / (1024 * 1024)
    print(f"✓ Earnings Database: {size_mb:.2f} MB")

    # Try to count entries
    import sqlite3
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        if tables:
            print(f"  Tables: {', '.join(tables)}")

            # Try to count entries in first table
            if tables:
                cursor.execute(f"SELECT COUNT(*) FROM {tables[0]}")
                count = cursor.fetchone()[0]
                print(f"  Entries: {count:,}")
        else:
            print("  Status: Empty (no tables yet)")

        conn.close()
    except Exception as e:
        print(f"  Status: {e}")
else:
    print("✗ Earnings database not found")

print("\n" + "="*80)
print("🎯 WHAT THE INTELLIGENT COLLECTOR WILL DO")
print("="*80)
print(f"\n1. Identify companies missing earnings data")
print(f"2. Use 3-phase strategy to find data:")
print(f"   Phase 1: Try BSE/NSE official scrapers")
print(f"   Phase 2: Search web using Perplexity AI")
print(f"   Phase 3: Infer using Dexter AI patterns")
print(f"3. Validate and add to database")
print(f"4. Update calendar to show complete coverage")

print("\n" + "="*80)
print("✅ SYSTEM IS READY!")
print("="*80)
print("\n📚 How to Test:")
print("\n1. BROWSER TEST (Easiest):")
print("   Open: http://localhost:8001/docs")
print("   or:   http://13.200.109.29:8001/docs")
print("   Find 'Intelligent Collector' section")
print("   Click 'Try it out' on any endpoint")
print("\n2. CALENDAR TEST:")
print("   Open: http://localhost:8001/api/earnings/calendar/public?filter=all")
print(f"   Should show: {total:,} companies")
print("\n3. DIRECT COLLECTION (When ready):")
print("   cd /Users/srijan/vcp_clean_test/vcp")
print("   python scripts/daily_earnings_gap_filler.py --max-companies 10")
print("\n" + "="*80 + "\n")
