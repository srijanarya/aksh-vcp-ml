"""
ISIN Matcher - Match BSE and NSE stocks using ISIN codes

ISIN (International Securities Identification Number) is a unique 12-character
alphanumeric code that identifies securities. Same company has same ISIN across
BSE and NSE, making it the most reliable mapping method.

Format: IN + E/D + 9 digits + check digit (e.g., INE467B01029 for TCS)

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def build_isin_index(
    records: List[Dict],
    exchange_key: str = "exchange"
) -> Dict[str, List[Dict]]:
    """
    Build an index mapping ISINs to stock records.

    Args:
        records: List of stock records with "isin" field
        exchange_key: Key name for exchange field (default: "exchange")

    Returns:
        Dictionary mapping ISIN -> List[Dict] (one per exchange)

    Example:
        bse_records = [{"isin": "INE467B01029", "symbol": "500570", "exchange": "BSE"}]
        nse_records = [{"isin": "INE467B01029", "symbol": "TCS", "exchange": "NSE"}]

        all_records = bse_records + nse_records
        index = build_isin_index(all_records)

        # Result:
        # {
        #     "INE467B01029": [
        #         {"isin": "INE467B01029", "symbol": "500570", "exchange": "BSE"},
        #         {"isin": "INE467B01029", "symbol": "TCS", "exchange": "NSE"}
        #     ]
        # }
    """
    isin_index: Dict[str, List[Dict]] = {}

    for record in records:
        isin = record.get("isin", "").strip()

        # Validate ISIN format
        if not isin or len(isin) != 12:
            continue

        if not isin.startswith("IN"):
            logger.warning(f"Invalid ISIN format: {isin} (should start with 'IN')")
            continue

        # Add to index
        if isin not in isin_index:
            isin_index[isin] = []

        isin_index[isin].append(record)

    logger.info(
        f"Built ISIN index: {len(isin_index)} unique ISINs from {len(records)} records"
    )

    return isin_index


def match_by_isin(
    bse_records: List[Dict],
    nse_records: List[Dict]
) -> Tuple[List[Dict], List[str], List[str]]:
    """
    Match BSE and NSE stocks using ISIN codes.

    Args:
        bse_records: List of BSE stock records with "isin", "symbol" fields
        nse_records: List of NSE stock records with "isin", "symbol" fields

    Returns:
        Tuple of:
        - matched_pairs: List of dicts with BSE-NSE mapping
          [{"bse_code": "500570", "nse_symbol": "TCS", "isin": "INE467B01029", ...}]
        - unmatched_bse: List of BSE codes with no NSE match
        - unmatched_nse: List of NSE symbols with no BSE match

    Example:
        bse_data = [
            {"isin": "INE467B01029", "symbol": "500570", "name": "TCS Ltd"},
            {"isin": "INE009A01021", "symbol": "500209", "name": "Infosys"}
        ]
        nse_data = [
            {"isin": "INE467B01029", "symbol": "TCS", "name": "Tata Consultancy"},
            {"isin": "INE040A01034", "symbol": "HDFC", "name": "HDFC Ltd"}  # No BSE match
        ]

        matched, unmatched_bse, unmatched_nse = match_by_isin(bse_data, nse_data)

        print(f"Matched: {len(matched)}")  # 1 (TCS)
        print(f"Unmatched BSE: {unmatched_bse}")  # ['500209'] (Infosys)
        print(f"Unmatched NSE: {unmatched_nse}")  # ['HDFC']
    """
    # Build indexes
    bse_index = {}
    for record in bse_records:
        isin = record.get("isin", "").strip()
        if isin and len(isin) == 12:
            bse_index[isin] = record

    nse_index = {}
    for record in nse_records:
        isin = record.get("isin", "").strip()
        if isin and len(isin) == 12:
            nse_index[isin] = record

    logger.info(f"Built indexes: {len(bse_index)} BSE ISINs, {len(nse_index)} NSE ISINs")

    # Find matches
    matched_pairs = []
    matched_isins = set()

    for isin in bse_index:
        if isin in nse_index:
            bse_record = bse_index[isin]
            nse_record = nse_index[isin]

            matched_pair = {
                "isin": isin,
                "bse_code": bse_record.get("symbol", ""),
                "bse_name": bse_record.get("name", ""),
                "nse_symbol": nse_record.get("symbol", ""),
                "nse_name": nse_record.get("name", ""),
                "match_method": "isin",
                "match_confidence": 1.0  # ISIN match is 100% confidence
            }

            matched_pairs.append(matched_pair)
            matched_isins.add(isin)

    # Find unmatched
    unmatched_bse = [
        bse_index[isin].get("symbol", "")
        for isin in bse_index
        if isin not in matched_isins
    ]

    unmatched_nse = [
        nse_index[isin].get("symbol", "")
        for isin in nse_index
        if isin not in matched_isins
    ]

    logger.info(
        f"ISIN matching complete: {len(matched_pairs)} matched, "
        f"{len(unmatched_bse)} unmatched BSE, {len(unmatched_nse)} unmatched NSE"
    )

    match_rate = len(matched_pairs) / max(len(bse_index), 1) * 100
    logger.info(f"Match rate: {match_rate:.1f}% of BSE stocks have NSE ISIN match")

    return matched_pairs, unmatched_bse, unmatched_nse


def validate_isin(isin: str) -> Tuple[bool, Optional[str]]:
    """
    Validate ISIN format and checksum.

    Args:
        isin: ISIN string to validate

    Returns:
        Tuple of (is_valid, error_message)

    Validation Rules:
        - Must be 12 characters
        - First 2 chars: Country code (IN for India)
        - Next 9 chars: Alphanumeric security identifier
        - Last char: Check digit (Luhn algorithm)

    Example:
        is_valid, error = validate_isin("INE467B01029")
        if is_valid:
            print("Valid ISIN")
        else:
            print(f"Invalid: {error}")
    """
    if not isin:
        return False, "ISIN is empty"

    if len(isin) != 12:
        return False, f"ISIN must be 12 characters (got {len(isin)})"

    if not isin[:2].isalpha():
        return False, "First 2 characters must be country code (e.g., 'IN')"

    if not isin[2:11].isalnum():
        return False, "Characters 3-11 must be alphanumeric"

    if not isin[11].isdigit():
        return False, "Last character must be check digit"

    # For Indian stocks, should start with IN
    if not isin.startswith("IN"):
        return False, f"Indian ISIN should start with 'IN' (got '{isin[:2]}')"

    # TODO: Implement full Luhn checksum validation if needed
    # For now, format validation is sufficient

    return True, None


def get_isin_stats(records: List[Dict]) -> Dict[str, any]:
    """
    Get statistics about ISIN coverage in a dataset.

    Args:
        records: List of stock records with optional "isin" field

    Returns:
        Dictionary with coverage statistics

    Example:
        stats = get_isin_stats(bse_records)
        print(f"ISIN coverage: {stats['coverage_pct']:.1f}%")
    """
    total_records = len(records)
    valid_isins = 0
    invalid_isins = 0
    missing_isins = 0

    isin_set: Set[str] = set()

    for record in records:
        isin = record.get("isin", "").strip()

        if not isin:
            missing_isins += 1
            continue

        is_valid, error = validate_isin(isin)

        if is_valid:
            valid_isins += 1
            isin_set.add(isin)
        else:
            invalid_isins += 1
            logger.debug(f"Invalid ISIN '{isin}': {error}")

    coverage_pct = (valid_isins / max(total_records, 1)) * 100
    unique_isins = len(isin_set)

    stats = {
        "total_records": total_records,
        "valid_isins": valid_isins,
        "invalid_isins": invalid_isins,
        "missing_isins": missing_isins,
        "unique_isins": unique_isins,
        "coverage_pct": coverage_pct,
        "duplicate_isins": valid_isins - unique_isins
    }

    logger.info(
        f"ISIN Stats: {valid_isins}/{total_records} valid ({coverage_pct:.1f}%), "
        f"{unique_isins} unique ISINs"
    )

    return stats


if __name__ == "__main__":
    # Demo: ISIN matching
    logging.basicConfig(level=logging.INFO)

    print("=== ISIN Matching Demo ===")

    # Sample data
    bse_data = [
        {"isin": "INE467B01029", "symbol": "500570", "name": "TCS Ltd", "exchange": "BSE"},
        {"isin": "INE009A01021", "symbol": "500209", "name": "Infosys Ltd", "exchange": "BSE"},
        {"isin": "INE040A01034", "symbol": "500180", "name": "HDFC Bank", "exchange": "BSE"},
        {"isin": "", "symbol": "500999", "name": "Unknown Co", "exchange": "BSE"},  # Missing ISIN
    ]

    nse_data = [
        {"isin": "INE467B01029", "symbol": "TCS", "name": "Tata Consultancy", "exchange": "NSE"},
        {"isin": "INE040A01034", "symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "exchange": "NSE"},
        {"isin": "INE002A01018", "symbol": "RELIANCE", "name": "Reliance Ind", "exchange": "NSE"},  # No BSE match
    ]

    # Match by ISIN
    matched, unmatched_bse, unmatched_nse = match_by_isin(bse_data, nse_data)

    print(f"\nMatched pairs: {len(matched)}")
    for pair in matched:
        print(f"  {pair['bse_code']} (BSE) <-> {pair['nse_symbol']} (NSE) via {pair['isin']}")

    print(f"\nUnmatched BSE codes: {unmatched_bse}")
    print(f"Unmatched NSE symbols: {unmatched_nse}")

    # Get stats
    print("\n=== BSE ISIN Stats ===")
    bse_stats = get_isin_stats(bse_data)
    print(f"Coverage: {bse_stats['coverage_pct']:.1f}%")
    print(f"Valid ISINs: {bse_stats['valid_isins']}/{bse_stats['total_records']}")

    print("\n=== NSE ISIN Stats ===")
    nse_stats = get_isin_stats(nse_data)
    print(f"Coverage: {nse_stats['coverage_pct']:.1f}%")
    print(f"Valid ISINs: {nse_stats['valid_isins']}/{nse_stats['total_records']}")
