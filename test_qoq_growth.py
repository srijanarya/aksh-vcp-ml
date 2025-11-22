#!/usr/bin/env python3
"""
Test QoQ Growth Calculation

Verifies that the TrueBlockbusterDetector can calculate both YoY and QoQ growth
from the historical data in the database.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.ml.true_blockbuster_detector import TrueBlockbusterDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_qoq_calculation():
    """Test QoQ growth calculation with a company that has historical data"""
    
    detector = TrueBlockbusterDetector()
    
    # Test with a company that should have multiple quarters of data
    # (from the historical backfill we just completed)
    test_companies = [
        ("500325", "Reliance Industries"),
        ("532540", "TCS"),
        ("500180", "HDFC Bank")
    ]
    
    print("=" * 80)
    print("Testing QoQ Growth Calculation")
    print("=" * 80)
    
    for bse_code, name in test_companies:
        print(f"\n📊 Testing: {name} ({bse_code})")
        print("-" * 80)
        
        try:
            result = detector.analyze_stock(bse_code, name)
            
            if result['data']:
                data = result['data']
                print(f"\n✅ Growth Metrics:")
                print(f"   Revenue YoY: {data.get('revenue_yoy', 'N/A'):.1f}%")
                print(f"   Revenue QoQ: {data.get('revenue_qoq', 'N/A'):.1f}%")
                print(f"   Profit YoY:  {data.get('pat_yoy', 'N/A'):.1f}%")
                print(f"   Profit QoQ:  {data.get('pat_qoq', 'N/A'):.1f}%")
                
                if result['is_blockbuster']:
                    print(f"\n🌟 BLOCKBUSTER! Score: {result['score']}/100")
                    print(f"   Reasons:")
                    for reason in result['reasons']:
                        print(f"   • {reason}")
                else:
                    print(f"\n📊 Not a blockbuster (Score: {result['score']}/100)")
                    if result['failures']:
                        print(f"   Why it failed:")
                        for failure in result['failures'][:3]:
                            print(f"   • {failure}")
            else:
                print(f"❌ No data available")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_qoq_calculation()
