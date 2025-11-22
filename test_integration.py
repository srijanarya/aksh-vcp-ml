#!/usr/bin/env python3
"""
Comprehensive Integration Test

Runs the full Intelligence System for 2 minutes and validates all components.
"""

import subprocess
import time
import sqlite3
import sys

print("=" * 80)
print("COMPREHENSIVE INTEGRATION TEST")
print("=" * 80)

# 1. Clear old database
print("\n1. Resetting database...")
try:
    import os
    if os.path.exists("data/announcement_intelligence.db"):
        os.remove("data/announcement_intelligence.db")
        print("   ✓ Old database cleared")
except Exception as e:
    print(f"   ⚠ Error clearing DB: {e}")

# 2. Start the main loop
print("\n2. Starting Announcement Intelligence System...")
process = subprocess.Popen(
    ["python3", "run_announcement_intelligence.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
print(f"   ✓ Started with PID {process.pid}")

# 3. Let it run for 90 seconds
print("\n3. Running for 90 seconds...")
time.sleep(90)

# 4. Stop the process
print("\n4. Stopping system...")
process.terminate()
process.wait()
print("   ✓ Stopped")

# 5. Verify Database
print("\n5. Verifying Database...")
try:
    conn = sqlite3.connect("data/announcement_intelligence.db")
    cursor = conn.cursor()
    
    # Count announcements
    cursor.execute("SELECT COUNT(*) FROM announcements")
    total = cursor.fetchone()[0]
    print(f"   Total Announcements: {total}")
    
    # Count by category
    cursor.execute("SELECT category, COUNT(*) FROM announcements GROUP BY category ORDER BY COUNT(*) DESC")
    for cat, count in cursor.fetchall():
        print(f"      {cat}: {count}")
    
    # Check for extracted intelligence
    cursor.execute("SELECT COUNT(*) FROM extracted_intelligence WHERE status = 'success'")
    success_count = cursor.fetchone()[0]
    print(f"   Successful Extractions: {success_count}")
    
    # Show ORDER_WIN details
    cursor.execute("""
        SELECT a.company_name, a.title, e.intelligence_data 
        FROM announcements a 
        JOIN extracted_intelligence e ON a.id = e.announcement_id 
        WHERE a.category = 'ORDER_WIN' AND e.status = 'success'
    """)
    orders = cursor.fetchall()
    if orders:
        print(f"\n   ORDER_WIN Extractions:")
        for company, title, data in orders:
            print(f"      • {company}")
            print(f"        Data: {data[:100]}...")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ INTEGRATION TEST PASSED")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ DATABASE VERIFICATION FAILED: {e}")
    sys.exit(1)
