#!/usr/bin/env python3
"""
Backfill Historical Data for ML Training

Fetches 3 years of historical OHLCV data from Angel One
for all companies in the ML training set.
"""

import sys
import logging
from datetime import datetime, timedelta
from tools.angel_one_data_integration import AngelOneDataIntegration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# BSE Code to NSE Symbol mapping (expand this list)
# Based on common stocks in Indian markets
BSE_TO_NSE = {
    # Major Large Caps
    '500325': 'RELIANCE-EQ',
    '500112': 'SBIN-EQ',
    '532540': 'TCS-EQ',
    '500209': 'INFY-EQ',
    '500180': 'HDFCBANK-EQ',
    '532174': 'ICICIBANK-EQ',
    '500696': 'HINDUNILVR-EQ',
    '500010': 'HDFC-EQ',
    '532215': 'AXISBANK-EQ',
    '500820': 'ASIANPAINT-EQ',
    
    # Mid/Small Caps
    '532504': 'NAVINFLUOR-EQ',
    '500410': 'ACC-EQ',
    '532281': 'HCLTECH-EQ',
    '507815': 'GILLETTE-EQ',
    '500440': 'HINDALCO-EQ',
    '532712': 'RBLBANK-EQ',
    '532483': 'CANBK-EQ',
    '532977': 'BAJAJFINSV-EQ',
    '500034': 'BAJFINANCE-EQ',
    '532454': 'BHARTIARTL-EQ',
    
    # Add more as needed
    '500387': 'TVSMOTOR-EQ',
    '500570': 'TATAMOTORS-EQ',
    '532555': 'NTPC-EQ',
    '500547': 'BPCL-EQ',
    '532868': 'DMART-EQ',
}

def main():
    """Main backfill process"""
    
    print("=" * 70)
    print("ANGEL ONE HISTORICAL DATA BACKFILL")
    print("=" * 70)
    print(f"\nBackfilling data for {len(BSE_TO_NSE)} companies")
    print(f"Period: 3 years (approximately {3*365} days)")
    print(f"Target: Fix 'insufficient data' warnings in ML training\n")
    
    # Initialize Angel One integration
    print("Initializing Angel One client...")
    fetcher = AngelOneDataIntegration()
    
    # Authenticate
    if not fetcher.authenticate():
        print("❌ Authentication failed. Check credentials.")
        return 1
    
    print("✅ Authentication successful\n")
    
    # Backfill each company
    successful = 0
    failed = 0
    
    for bse_code, nse_symbol in BSE_TO_NSE.items():
        print(f"\n{'='*70}")
        print(f"Processing: {nse_symbol} (BSE: {bse_code})")
        print(f"{'='*70}")
        try:
            # Check if we already have data for this company
            # This is a simple check, ideally we'd query the DB, but for now we'll rely on the loop
            
            # Fetch 3 years of data
            import time
            time.sleep(0.5) # Rate limit protection (max 3 req/sec usually)
            
            df = fetcher.fetch_historical_prices(nse_symbol, days_back=3*365)
            
            if len(df) == 0:
                print(f"⚠️  No data returned for {nse_symbol}")
                failed += 1
                continue
            
            # Store to database
            try:
                fetcher.store_to_db(df, nse_symbol.replace('-EQ', ''))
                print(f"✅ Success: {len(df)} records stored")
                print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
                successful += 1
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    print(f"ℹ️  Data already exists for {nse_symbol} (UNIQUE constraint)")
                    successful += 1 # Count as success since we have data
                else:
                    raise e
            
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1
            time.sleep(1) # Wait longer on error
            continue
    
    # Summary
    print("\n" + "=" * 70)
    print("BACKFILL COMPLETE")
    print("=" * 70)
    print(f"✅ Successful: {successful}/{len(BSE_TO_NSE)}")
    print(f"❌ Failed: {failed}/{len(BSE_TO_NSE)}")
    print(f"\nData stored in: data/historical_prices.db")
    print("\nNext steps:")
    print("1. Verify data quality: SELECT COUNT(*) FROM historical_prices;")
    print("2. Re-run ML training to use new historical data")
    print("3. Check if 'insufficient data' warnings are resolved")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
