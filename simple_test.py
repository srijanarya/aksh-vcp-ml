#!/usr/bin/env python3
"""
Super Simple Test - Just shows the data gaps
No complex imports needed!
"""

import json
import sqlite3
from pathlib import Path

print("\n" + "="*80)
print("🧪 INTELLIGENT EARNINGS COLLECTOR - SIMPLE TEST")
print("="*80)

# Path to files
master_list = Path("/Users/srijan/vcp_clean_test/data/master_stock_list.json")
db_path = Path("/Users/srijan/vcp_clean_test/data/earnings_calendar.db")

# Load master stock list
print("\n📂 Loading master stock list...")
with open(master_list, 'r') as f:
    master_data = json.load(f)

total_companies = master_data.get('total_companies', 0)
print(f"✓ Master list has {total_companies:,} companies")

# Load companies with earnings from database
print("\n📊 Checking earnings database...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(DISTINCT bse_code) FROM earnings WHERE bse_code IS NOT NULL")
companies_with_data = cursor.fetchone()[0]

conn.close()

print(f"✓ Database has earnings for {companies_with_data:,} companies")

# Calculate gap
gap = total_companies - companies_with_data
gap_pct = (gap / total_companies * 100) if total_companies > 0 else 0

print("\n" + "="*80)
print("📈 SUMMARY")
print("="*80)
print(f"Total companies tracked:     {total_companies:,}")
print(f"Companies with earnings:     {companies_with_data:,} ({100-gap_pct:.1f}%)")
print(f"Companies WITHOUT earnings:  {gap:,} ({gap_pct:.1f}%)")
print("="*80)

print("\n💡 What This Means:")
print(f"   The Intelligent Collector needs to find earnings data")
print(f"   for {gap:,} companies using AI + web search.")
print()
print("📋 Sample Companies Missing Data:")

# Show some examples
if master_data.get('companies'):
    # Get companies with earnings
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT bse_code FROM earnings WHERE bse_code IS NOT NULL")
    codes_with_data = {row[0] for row in cursor.fetchall()}
    conn.close()

    # Find companies without data
    missing_count = 0
    for company in master_data['companies'][:100]:  # Check first 100
        code = company.get('code')
        name = company.get('company_name', code)

        if code and code not in codes_with_data:
            missing_count += 1
            if missing_count <= 5:
                print(f"   {missing_count}. {name} ({code})")
            if missing_count >= 5:
                break

print("\n✅ Test Complete!")
print("\n📚 Next Steps:")
print("   1. The system is ready to automatically find this missing data")
print("   2. It will use: BSE/NSE scrapers → Web search → AI inference")
print("   3. Run collection via:")
print("      cd /Users/srijan/vcp_clean_test/vcp")
print("      python scripts/daily_earnings_gap_filler.py --max-companies 10")
print("="*80 + "\n")
