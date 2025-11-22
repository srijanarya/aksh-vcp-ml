#!/usr/bin/env python3
"""
Pre-load Angel One Symbol Tokens

Downloads and caches all NSE symbol tokens to avoid rate limiting
during backtests. Run this once before running large-scale backtests.

Usage:
    python3 tools/preload_angel_symbols.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
from typing import Dict, List
from src.data.angel_one_client import AngelOneClient

def load_nse_symbols() -> List[str]:
    """Load NSE symbols from stock list"""
    symbols_file = Path(__file__).parent.parent / "agents/backtesting/symbol_lists/nse_bse_all_stocks.txt"

    if not symbols_file.exists():
        print(f"❌ Symbol list not found: {symbols_file}")
        return []

    with open(symbols_file, 'r') as f:
        symbols = [line.strip() for line in f if line.strip() and '.NS' in line]

    # Remove .NS suffix
    symbols = [s.replace('.NS', '') for s in symbols]

    print(f"✅ Loaded {len(symbols)} NSE symbols")
    return symbols


def preload_symbol_tokens(
    client: AngelOneClient,
    symbols: List[str],
    cache_file: str = "/tmp/angel_symbol_cache.json",
    rate_limit_delay: float = 2.0
) -> Dict[str, str]:
    """
    Pre-load symbol tokens with aggressive rate limiting

    Args:
        client: Authenticated Angel One client
        symbols: List of NSE symbols (without .NS suffix)
        cache_file: Path to save cache
        rate_limit_delay: Seconds to wait between requests

    Returns:
        Dict mapping symbol to token
    """
    # Load existing cache if available
    token_cache = {}
    cache_path = Path(cache_file)

    if cache_path.exists():
        print(f"📦 Loading existing cache from {cache_file}")
        with open(cache_file, 'r') as f:
            token_cache = json.load(f)
        print(f"   Found {len(token_cache)} cached tokens")

    # Filter symbols that need lookup
    symbols_to_fetch = [s for s in symbols if s not in token_cache]
    print(f"\n🔍 Need to fetch {len(symbols_to_fetch)} symbol tokens")
    print(f"   Rate limit: {rate_limit_delay}s between requests")
    print(f"   Estimated time: {len(symbols_to_fetch) * rate_limit_delay / 60:.1f} minutes")
    print()

    success_count = 0
    error_count = 0

    for i, symbol in enumerate(symbols_to_fetch, 1):
        try:
            # Try with -EQ suffix first (equity)
            symbol_eq = f"{symbol}-EQ"

            response = client._smart_api.searchScrip("NSE", symbol_eq)

            if response.get('status') and response.get('data'):
                data = response['data']

                # Find exact match for symbol-EQ
                for item in data:
                    if item.get('tradingsymbol') == symbol_eq and item.get('exchange') == 'NSE':
                        token = item.get('symboltoken')
                        token_cache[symbol] = token
                        success_count += 1

                        if i % 10 == 0:
                            print(f"[{i}/{len(symbols_to_fetch)}] {symbol}: {token} (success: {success_count}, errors: {error_count})")

                        # Save cache every 50 symbols
                        if i % 50 == 0:
                            with open(cache_file, 'w') as f:
                                json.dump(token_cache, f, indent=2)
                            print(f"   💾 Saved checkpoint ({len(token_cache)} tokens cached)")

                        break
                else:
                    print(f"[{i}/{len(symbols_to_fetch)}] ⚠️  {symbol}: Not found in search results")
                    error_count += 1
            else:
                print(f"[{i}/{len(symbols_to_fetch)}] ⚠️  {symbol}: Search failed")
                error_count += 1

            # Rate limiting
            time.sleep(rate_limit_delay)

        except Exception as e:
            error_msg = str(e)
            if 'access rate' in error_msg.lower():
                print(f"\n❌ Rate limit hit at symbol {i}/{len(symbols_to_fetch)}")
                print(f"   Waiting 60 seconds before retry...")
                time.sleep(60)
                # Retry this symbol
                continue
            else:
                print(f"[{i}/{len(symbols_to_fetch)}] ❌ {symbol}: Error - {error_msg}")
                error_count += 1

            time.sleep(rate_limit_delay)

    # Final save
    with open(cache_file, 'w') as f:
        json.dump(token_cache, f, indent=2)

    print(f"\n{'='*70}")
    print(f"✅ Symbol token pre-loading complete!")
    print(f"{'='*70}")
    print(f"Total symbols: {len(symbols)}")
    print(f"Cached tokens: {len(token_cache)}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Cache file: {cache_file}")
    print(f"{'='*70}\n")

    return token_cache


def main():
    """Main function"""
    print("=" * 70)
    print("  ANGEL ONE SYMBOL TOKEN PRE-LOADER")
    print("=" * 70)
    print()

    # Initialize client
    env_path = Path(__file__).parent.parent / ".env.angel"

    if not env_path.exists():
        print(f"❌ Angel One credentials not found at {env_path}")
        print("   Please create .env.angel file")
        sys.exit(1)

    print("🔐 Authenticating with Angel One...")
    client = AngelOneClient.from_env_file(str(env_path))

    if not client.authenticate():
        print("❌ Authentication failed!")
        sys.exit(1)

    print("✅ Authenticated successfully!\n")

    # Load symbols
    symbols = load_nse_symbols()

    if not symbols:
        print("❌ No symbols to process")
        sys.exit(1)

    # Pre-load tokens
    token_cache = preload_symbol_tokens(
        client=client,
        symbols=symbols,
        cache_file="/tmp/angel_symbol_cache.json",
        rate_limit_delay=2.0  # 2 seconds between requests
    )

    print("✅ Pre-loading complete! You can now run backtests without symbol lookup delays.")


if __name__ == '__main__':
    main()
