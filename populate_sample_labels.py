"""
Populate Sample Labels

This script creates sample upper circuit labels for demonstration purposes.
It analyzes price movements and creates labels for days with significant price increases.
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_BASE_PATH = "/Users/srijan/Desktop/aksh/data"

def populate_labels():
    # Connect to databases
    price_db = sqlite3.connect(os.path.join(DB_BASE_PATH, "price_movements.db"))
    labels_db = sqlite3.connect(os.path.join(DB_BASE_PATH, "upper_circuit_labels.db"))
    
    # Get all price records
    price_cursor = price_db.cursor()
    price_cursor.execute("""
        SELECT bse_code, date, close, open
        FROM price_movements
        ORDER BY bse_code, date
    """)
    
    rows = price_cursor.fetchall()
    
    # Group by company
    company_data = {}
    for bse_code, date, close, open_price in rows:
        if bse_code not in company_data:
            company_data[bse_code] = []
        company_data[bse_code].append({
            'date': date,
            'close': close,
            'open': open_price
        })
    
    # Create labels based on price movements
    labels_cursor = labels_db.cursor()
    labels_created = 0
    
    for bse_code, prices in company_data.items():
        for i in range(len(prices) - 1):
            current = prices[i]
            next_day = prices[i + 1]
            
            # Calculate price change
            if current['close'] > 0:
                price_change_pct = ((next_day['close'] - current['close']) / current['close']) * 100
                
                # Label as upper circuit if price increased by > 2%
                # (Using 2% for demo to get some positive samples)
                label = 1 if price_change_pct > 2.0 else 0
                
                # Insert label (using current date as "earnings_date" for demo)
                try:
                    labels_cursor.execute("""
                        INSERT OR REPLACE INTO upper_circuit_labels
                        (bse_code, earnings_date, next_day_date, price_change_pct, hit_circuit, label)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        bse_code,
                        current['date'],
                        next_day['date'],
                        price_change_pct,
                        1 if label == 1 else 0,
                        label
                    ))
                    labels_created += 1
                except Exception as e:
                    print(f"Error inserting label: {e}")
    
    labels_db.commit()
    
    # Print statistics
    labels_cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels WHERE label = 1")
    positive_count = labels_cursor.fetchone()[0]
    
    labels_cursor.execute("SELECT COUNT(*) FROM upper_circuit_labels WHERE label = 0")
    negative_count = labels_cursor.fetchone()[0]
    
    print(f"✅ Created {labels_created} labels")
    print(f"   Positive (upper circuit): {positive_count}")
    print(f"   Negative (no circuit): {negative_count}")
    print(f"   Class balance: {positive_count / labels_created * 100:.1f}% positive")
    
    price_db.close()
    labels_db.close()

if __name__ == "__main__":
    populate_labels()
