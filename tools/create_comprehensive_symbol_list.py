#!/usr/bin/env python3
"""
Create comprehensive symbol list from NSE and BSE sources
Merges symbols and formats them for Yahoo Finance (.NS suffix)
"""
import csv
import sys
import re
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

NSE_CSV = PROJECT_ROOT / "nse_equity_list.csv"
BSE_BHAV_COPY = PROJECT_ROOT / "data" / "cache" / "bhav_copy" / "BSE_EQ241224.CSV"
OUTPUT_DIR = PROJECT_ROOT / "agents" / "backtesting" / "symbol_lists"
OUTPUT_FILE = OUTPUT_DIR / "nse_bse_all_stocks.txt"

def clean_symbol(symbol):
    """Clean and normalize stock symbol"""
    # Remove extra spaces
    symbol = symbol.strip()
    # Remove trailing dots
    symbol = symbol.rstrip('.')
    # Remove special characters that Yahoo Finance doesn't like
    symbol = re.sub(r'[&\s\-]', '', symbol)
    # Convert to uppercase
    symbol = symbol.upper()
    return symbol

def extract_nse_symbols():
    """Extract symbols from NSE equity list"""
    symbols = set()

    print(f"Reading NSE equity list from {NSE_CSV}...")

    with open(NSE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row.get('SYMBOL', '').strip()
            if symbol and len(symbol) > 0:
                # Clean and add .NS suffix
                clean_sym = clean_symbol(symbol)
                symbols.add(f"{clean_sym}.NS")

    print(f"  Found {len(symbols)} NSE symbols")
    return symbols

def extract_bse_symbols_from_bhav():
    """Extract symbols from BSE Bhav Copy (daily equity report)"""
    symbols = set()

    if not BSE_BHAV_COPY.exists():
        print(f"⚠️  BSE Bhav Copy not found: {BSE_BHAV_COPY}")
        return symbols

    print(f"Reading BSE Bhav Copy from {BSE_BHAV_COPY}...")

    with open(BSE_BHAV_COPY, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # BSE format: SC_NAME contains stock name
            stock_name = row.get('SC_NAME', '').strip()
            sc_code = row.get('SC_CODE', '').strip()

            if stock_name and len(stock_name) > 0:
                # Clean the stock name to create symbol
                # BSE names like "ABB LTD.    " -> "ABBLTD"
                clean_sym = clean_symbol(stock_name)

                # Only add if it looks like a valid symbol (not too long)
                if len(clean_sym) > 0 and len(clean_sym) <= 25:
                    symbols.add(f"{clean_sym}.NS")

    print(f"  Found {len(symbols)} BSE symbols")
    return symbols

def merge_and_save(nse_symbols, bse_symbols):
    """Merge symbol sets and save to file"""

    # Merge sets (automatically removes duplicates)
    all_symbols = nse_symbols.union(bse_symbols)

    # Sort alphabetically
    sorted_symbols = sorted(all_symbols)

    print(f"\nTotal unique symbols: {len(sorted_symbols)}")
    print(f"  NSE: {len(nse_symbols)}")
    print(f"  BSE: {len(bse_symbols)}")
    print(f"  Overlap: {len(nse_symbols.intersection(bse_symbols))}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save as comma-separated for CLI usage
    with open(OUTPUT_FILE, 'w') as f:
        f.write(','.join(sorted_symbols))

    print(f"\nSaved {len(sorted_symbols)} symbols to {OUTPUT_FILE}")

    # Also save as one-per-line for easy viewing
    list_file = OUTPUT_DIR / "nse_bse_all_stocks_list.txt"
    with open(list_file, 'w') as f:
        for symbol in sorted_symbols:
            f.write(f"{symbol}\n")

    print(f"Saved symbol list to {list_file}")

    return sorted_symbols

if __name__ == '__main__':
    print("=" * 70)
    print("Creating comprehensive symbol list from NSE + BSE")
    print("=" * 70)
    print()

    # Extract symbols
    nse_symbols = extract_nse_symbols()
    bse_symbols = extract_bse_symbols_from_bhav()

    # Merge and save
    all_symbols = merge_and_save(nse_symbols, bse_symbols)

    print("\n" + "=" * 70)
    print("First 20 symbols:")
    for symbol in all_symbols[:20]:
        print(f"  {symbol}")

    print("\n" + "=" * 70)
    print("To run comprehensive backtest:")
    print(f'  python3 agents/backtesting/cli.py analyze \\')
    print(f'    --strategy strategies/multi_timeframe_breakout.py \\')
    print(f'    --start-date 2022-01-01 \\')
    print(f'    --end-date 2024-11-01 \\')
    print(f'    --symbols "$(cat {OUTPUT_FILE})"')
    print("=" * 70)
