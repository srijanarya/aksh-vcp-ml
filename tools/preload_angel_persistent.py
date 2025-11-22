#!/usr/bin/env python3
"""
Persistent Angel One Symbol Preloader

SURVIVES SYSTEM RESTARTS - All data saved to project directory, not /tmp/

Downloads and caches all NSE symbol tokens to avoid rate limiting
during backtests. Run this once before running Angel One backtests.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time
from typing import Dict, List
from src.data.angel_one_client import AngelOneClient


# Persistent storage locations (in project directory, NOT /tmp/)
PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data" / "angel_cache"
CACHE_FILE = DATA_DIR / "angel_symbol_tokens.json"
CHECKPOINT_FILE = DATA_DIR / "angel_preload_checkpoint.json"


def load_nse_symbols() -> List[str]:
    """Load NSE symbols from clean stock list"""
    symbols_file = PROJECT_DIR / "agents/backtesting/symbol_lists/nse_bse_clean_stocks_nse_only.txt"

    if not symbols_file.exists():
        print(f"❌ Symbol list not found: {symbols_file}")
        return []

    with open(symbols_file, 'r') as f:
        symbols = [line.strip().replace('.NS', '') for line in f if line.strip() and '.NS' in line]

    print(f"✅ Loaded {len(symbols)} NSE symbols")
    return symbols


def load_checkpoint() -> dict:
    """Load checkpoint if exists"""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {'last_index': 0, 'success': 0, 'errors': 0}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint"""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def preload_symbol_tokens(
    client: AngelOneClient,
    symbols: List[str],
    rate_limit_delay: float = 3.0
) -> Dict[str, str]:
    """
    Pre-load symbol tokens with checkpointing

    Args:
        client: Authenticated Angel One client
        symbols: List of NSE symbols (without .NS suffix)
        rate_limit_delay: Seconds to wait between requests

    Returns:
        Dict mapping symbol to token
    """
    # Ensure directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing cache
    token_cache = {}
    if CACHE_FILE.exists():
        print(f"📦 Loading existing cache from {CACHE_FILE}")
        with open(CACHE_FILE, 'r') as f:
            token_cache = json.load(f)
        print(f"   Found {len(token_cache)} cached tokens")

    # Load checkpoint
    checkpoint = load_checkpoint()
    start_idx = checkpoint['last_index']
    success_count = checkpoint['success']
    error_count = checkpoint['errors']

    # Filter symbols that need lookup (not in cache and not yet processed)
    symbols_to_fetch = [s for i, s in enumerate(symbols) if s not in token_cache and i >= start_idx]

    if not symbols_to_fetch:
        print("\n✅ All symbols already cached!")
        return token_cache

    print(f"\n🔍 Need to fetch {len(symbols_to_fetch)} symbol tokens")
    print(f"   Starting from index: {start_idx}")
    print(f"   Rate limit: {rate_limit_delay}s between requests")
    print(f"   Estimated time: {len(symbols_to_fetch) * rate_limit_delay / 60:.1f} minutes")
    print(f"\n   💾 Data saved to: {DATA_DIR}")
    print(f"   ✅ SURVIVES RESTARTS - will resume from checkpoint")
    print()

    for i, symbol in enumerate(symbols_to_fetch, start_idx + 1):
        try:
            # Try with -EQ suffix first (equity)
            symbol_eq = f"{symbol}-EQ"
            response = client._smart_api.searchScrip("NSE", symbol_eq)

            found = False
            if response.get('status') and response.get('data'):
                data = response['data']
                for item in data:
                    if item.get('tradingsymbol') == symbol_eq and item.get('exchange') == 'NSE':
                        token = item.get('symboltoken')
                        token_cache[symbol] = token
                        success_count += 1
                        found = True
                        break

            if not found:
                # Try without -EQ suffix
                response2 = client._smart_api.searchScrip("NSE", symbol)
                if response2.get('status') and response2.get('data'):
                    for item in response2['data']:
                        if item.get('exchange') == 'NSE':
                            token = item.get('symboltoken')
                            token_cache[symbol] = token
                            success_count += 1
                            found = True
                            break

            if not found:
                error_count += 1

            # Progress update every 50 symbols
            if i % 50 == 0:
                # Save cache
                with open(CACHE_FILE, 'w') as f:
                    json.dump(token_cache, f, indent=2)

                # Save checkpoint
                save_checkpoint({
                    'last_index': i,
                    'success': success_count,
                    'errors': error_count
                })

                progress_pct = i / len(symbols) * 100
                print(f"[{i}/{len(symbols)}] {progress_pct:.1f}% | Cache: {len(token_cache)} | Success: {success_count} | Errors: {error_count}")

            time.sleep(rate_limit_delay)

        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted at symbol {i}/{len(symbols)}")
            with open(CACHE_FILE, 'w') as f:
                json.dump(token_cache, f, indent=2)
            save_checkpoint({
                'last_index': i,
                'success': success_count,
                'errors': error_count
            })
            print(f"   💾 Checkpoint saved. Run script again to resume.")
            sys.exit(0)

        except Exception as e:
            error_msg = str(e)
            if 'access rate' in error_msg.lower():
                print(f"\n❌ Rate limit hit at symbol {i}! Backing off 60s...")
                with open(CACHE_FILE, 'w') as f:
                    json.dump(token_cache, f, indent=2)
                save_checkpoint({
                    'last_index': i - 1,
                    'success': success_count,
                    'errors': error_count
                })
                time.sleep(60)
            else:
                error_count += 1

            time.sleep(rate_limit_delay)

    # Final save
    with open(CACHE_FILE, 'w') as f:
        json.dump(token_cache, f, indent=2)

    # Clear checkpoint on completion
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

    print(f"\n{'='*70}")
    print(f"✅ SYMBOL TOKEN PRE-LOADING COMPLETE!")
    print(f"{'='*70}")
    print(f"Total symbols: {len(symbols)}")
    print(f"Cached tokens: {len(token_cache)}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Cache file: {CACHE_FILE}")
    print(f"{'='*70}\n")

    return token_cache


def main():
    """Main function"""
    print("=" * 70)
    print("  PERSISTENT ANGEL ONE SYMBOL TOKEN PRE-LOADER")
    print("=" * 70)
    print()
    print("✅ SURVIVES RESTARTS - data saved to project directory")
    print()

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize client
    env_path = PROJECT_DIR / ".env.angel"

    if not env_path.exists():
        print(f"❌ Angel One credentials not found at {env_path}")
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
        rate_limit_delay=3.0
    )

    print("✅ Pre-loading complete!")
    print(f"   Cache saved to: {CACHE_FILE}")
    print(f"   You can now run Angel One backtests without rate limiting.")


if __name__ == '__main__':
    main()
