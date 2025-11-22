#!/usr/bin/env python3
"""
Extract all stock symbols from VCP database for comprehensive backtesting
"""
import sqlite3
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "vcp_trading_local.db"

def extract_symbols():
    """Extract unique symbols from database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Try to find table with symbols/stocks
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"Found {len(tables)} tables in database")
    print("Tables:", ", ".join(tables[:10]), "..." if len(tables) > 10 else "")

    symbols = set()

    # Try common column names in each table
    for table in tables:
        try:
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [row[1] for row in cursor.fetchall()]

            # Look for symbol/stock columns
            symbol_col = None
            for col in columns:
                if col.lower() in ['symbol', 'ticker', 'stock_symbol', 'nse_symbol', 'bse_symbol', 'company_symbol']:
                    symbol_col = col
                    break

            if symbol_col:
                cursor.execute(f"SELECT DISTINCT {symbol_col} FROM {table} WHERE {symbol_col} IS NOT NULL;")
                table_symbols = [row[0] for row in cursor.fetchall()]
                print(f"  {table}: {len(table_symbols)} symbols (column: {symbol_col})")
                symbols.update(table_symbols)
        except Exception as e:
            pass  # Skip tables that don't have symbol columns

    conn.close()

    # Filter out invalid symbols
    valid_symbols = []
    for sym in symbols:
        if isinstance(sym, str) and len(sym) > 0:
            # Add .NS suffix if not present
            if not sym.endswith('.NS') and not sym.endswith('.BO'):
                sym = f"{sym}.NS"
            valid_symbols.append(sym)

    return sorted(valid_symbols)

if __name__ == '__main__':
    print(f"Extracting symbols from {DB_PATH}...")
    symbols = extract_symbols()

    print(f"\nTotal unique symbols: {len(symbols)}")
    print("\nFirst 20 symbols:")
    for sym in symbols[:20]:
        print(f"  {sym}")

    # Write to file
    output_file = PROJECT_ROOT / "agents" / "backtesting" / "symbol_lists" / "all_master_symbols.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write(','.join(symbols))

    print(f"\nSaved {len(symbols)} symbols to {output_file}")
    print(f"\nTo run backtest:")
    print(f'  python3 agents/backtesting/cli.py analyze \\')
    print(f'    --strategy strategies/multi_timeframe_breakout.py \\')
    print(f'    --start-date 2022-01-01 \\')
    print(f'    --end-date 2024-11-01 \\')
    print(f'    --symbols "$(cat {output_file})"')
