#!/usr/bin/env python3
"""
Clean Stock Universe - Remove Bonds, Debt Securities, and Illiquid Stocks

This script filters the stock list to include only equity securities.
"""

import re
from pathlib import Path


def is_bond_or_debt(symbol: str) -> bool:
    """
    Identify if a symbol represents a bond, debenture, or debt security

    Patterns that indicate non-equity:
    - Starts with numbers (e.g., 182TB12625, 563GS2026)
    - Contains 'GS', 'TB', 'SDL', 'FL' (Government Securities, Treasury Bills, State Development Loans, Floating Rate)
    - Contains 'NCB', 'NCD' (Non-Convertible Bonds/Debentures)
    """
    # Remove .NS or .BO suffix for checking
    clean_symbol = symbol.replace('.NS', '').replace('.BO', '')

    # Starts with numbers (government securities, bonds)
    if re.match(r'^\d', clean_symbol):
        return True

    # Contains debt security indicators
    debt_patterns = ['GS', 'TB', 'SDL', 'FL', 'NCB', 'NCD', 'GSEC']
    for pattern in debt_patterns:
        if pattern in clean_symbol.upper():
            return True

    return False


def is_special_series(symbol: str) -> bool:
    """
    Identify special series (preference shares, warrants, etc.)

    Patterns:
    - (PS) - Preference Shares
    - -PP - Preference Shares
    - W1, W2 - Warrants
    """
    clean_symbol = symbol.replace('.NS', '').replace('.BO', '')

    # Preference shares
    if '(PS)' in clean_symbol or '-PP' in clean_symbol or 'PREF' in clean_symbol.upper():
        return True

    # Warrants
    if re.search(r'W\d', clean_symbol):
        return True

    return False


def clean_stock_list(input_file: str, output_file: str):
    """
    Clean the stock list by removing non-equity securities
    """
    print("=" * 70)
    print("STOCK UNIVERSE CLEANER")
    print("=" * 70)
    print()

    input_path = Path(input_file)

    if not input_path.exists():
        print(f"❌ Input file not found: {input_file}")
        return

    # Read all symbols
    with open(input_file, 'r') as f:
        all_symbols = [line.strip() for line in f if line.strip()]

    print(f"📋 Total symbols in input: {len(all_symbols)}")
    print()

    # Categorize symbols
    bonds = []
    special_series = []
    clean_stocks = []

    for symbol in all_symbols:
        if is_bond_or_debt(symbol):
            bonds.append(symbol)
        elif is_special_series(symbol):
            special_series.append(symbol)
        else:
            clean_stocks.append(symbol)

    # Statistics
    print("🔍 Categorization Results:")
    print(f"   Bonds/Debt Securities: {len(bonds)} ({len(bonds)/len(all_symbols)*100:.1f}%)")
    print(f"   Special Series: {len(special_series)} ({len(special_series)/len(all_symbols)*100:.1f}%)")
    print(f"   Clean Equity Stocks: {len(clean_stocks)} ({len(clean_stocks)/len(all_symbols)*100:.1f}%)")
    print()

    # Show some examples of removed items
    if bonds:
        print("📊 Example Bonds Removed:")
        for bond in bonds[:5]:
            print(f"   - {bond}")
        print()

    if special_series:
        print("📊 Example Special Series Removed:")
        for series in special_series[:5]:
            print(f"   - {series}")
        print()

    # Separate NSE and BSE
    nse_stocks = [s for s in clean_stocks if '.NS' in s]
    bse_stocks = [s for s in clean_stocks if '.BO' in s]

    print(f"📈 Exchange Distribution:")
    print(f"   NSE Stocks: {len(nse_stocks)}")
    print(f"   BSE Stocks: {len(bse_stocks)}")
    print()

    # Write clean list
    with open(output_file, 'w') as f:
        for symbol in clean_stocks:
            f.write(f"{symbol}\n")

    print(f"✅ Clean stock list saved to: {output_file}")
    print(f"   Total clean stocks: {len(clean_stocks)}")
    print()

    # Also create NSE-only list
    nse_only_file = output_file.replace('.txt', '_nse_only.txt')
    with open(nse_only_file, 'w') as f:
        for symbol in nse_stocks:
            f.write(f"{symbol}\n")

    print(f"✅ NSE-only list saved to: {nse_only_file}")
    print(f"   Total NSE stocks: {len(nse_stocks)}")
    print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Original Universe: {len(all_symbols)} symbols")
    print(f"Removed: {len(bonds) + len(special_series)} non-equity securities")
    print(f"Clean Universe: {len(clean_stocks)} equity stocks")
    print(f"Reduction: {(len(bonds) + len(special_series))/len(all_symbols)*100:.1f}%")
    print("=" * 70)


def main():
    """Main function"""
    # Input and output paths
    input_file = Path(__file__).parent.parent / "agents/backtesting/symbol_lists/nse_bse_all_stocks.txt"
    output_file = Path(__file__).parent.parent / "agents/backtesting/symbol_lists/nse_bse_clean_stocks.txt"

    clean_stock_list(str(input_file), str(output_file))

    print()
    print("💡 Recommendation:")
    print("   Use nse_bse_clean_stocks_nse_only.txt for backtesting")
    print("   This contains only liquid NSE equity stocks")


if __name__ == "__main__":
    main()
