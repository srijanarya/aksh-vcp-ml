"""
Fuzzy Name Matcher - Match company names using fuzzy string matching

For BSE-NSE mapping when ISIN is missing (~20% of cases). Uses multiple
algorithms: Levenshtein distance, token sort ratio, and partial ratio.

Critical for improving BSE-NSE mapping from 33.9% to 80% target.

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def clean_company_name(name: str) -> str:
    """
    Clean and normalize company name for matching.

    Normalization steps:
    1. Convert to lowercase
    2. Remove legal suffixes (Ltd, Limited, Corp, etc.)
    3. Remove special characters
    4. Remove extra whitespace
    5. Standardize common abbreviations

    Args:
        name: Raw company name

    Returns:
        Cleaned company name

    Example:
        >>> clean_company_name("Tata Consultancy Services Ltd.")
        "tata consultancy services"

        >>> clean_company_name("HDFC Bank Limited")
        "hdfc bank"
    """
    if not name:
        return ""

    # Convert to lowercase
    cleaned = name.lower()

    # Remove common legal suffixes
    legal_suffixes = [
        r"\blimited\b",
        r"\bltd\.?\b",
        r"\bcorporation\b",
        r"\bcorp\.?\b",
        r"\bincorporated\b",
        r"\binc\.?\b",
        r"\bprivate\b",
        r"\bpvt\.?\b",
        r"\bpublic\b",
        r"\bcompany\b",
        r"\bco\.?\b",
    ]

    for suffix in legal_suffixes:
        cleaned = re.sub(suffix, "", cleaned)

    # Standardize common abbreviations
    abbreviations = {
        r"\bintl\b": "international",
        r"\btech\b": "technology",
        r"\binfo\b": "information",
        r"\bmfg\b": "manufacturing",
        r"\bpharma\b": "pharmaceutical",
        r"\bcomm\b": "communication",
        r"\btelec\b": "telecommunications",
        r"\binds\b": "industries",
        r"\bend\b": "enterprises",
    }

    for pattern, replacement in abbreviations.items():
        cleaned = re.sub(pattern, replacement, cleaned)

    # Remove special characters (keep alphanumeric and spaces)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)

    # Remove extra whitespace
    cleaned = " ".join(cleaned.split())

    return cleaned.strip()


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate Levenshtein (edit) distance between two strings.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Minimum number of single-character edits (insertions, deletions, substitutions)

    Example:
        >>> levenshtein_distance("tata", "tota")
        1  # One substitution: a->o
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, or substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def fuzzy_ratio(s1: str, s2: str) -> float:
    """
    Calculate fuzzy similarity ratio using SequenceMatcher.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity ratio between 0.0 (no match) and 1.0 (perfect match)

    Example:
        >>> fuzzy_ratio("tata consultancy", "tata consulting")
        0.85
    """
    return SequenceMatcher(None, s1, s2).ratio()


def token_sort_ratio(s1: str, s2: str) -> float:
    """
    Calculate similarity after sorting tokens alphabetically.
    Handles word order differences.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity ratio between 0.0 and 1.0

    Example:
        >>> token_sort_ratio("consultancy tata", "tata consultancy")
        1.0  # Perfect match after sorting
    """
    # Sort tokens alphabetically
    tokens1 = sorted(s1.split())
    tokens2 = sorted(s2.split())

    sorted1 = " ".join(tokens1)
    sorted2 = " ".join(tokens2)

    return fuzzy_ratio(sorted1, sorted2)


def partial_ratio(s1: str, s2: str) -> float:
    """
    Calculate best partial match ratio (substring matching).
    Useful when one name is abbreviated.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Best partial similarity ratio between 0.0 and 1.0

    Example:
        >>> partial_ratio("hdfc bank", "hdfc bank limited")
        1.0  # "hdfc bank" fully matches substring
    """
    if len(s1) < len(s2):
        shorter = s1
        longer = s2
    else:
        shorter = s2
        longer = s1

    # Try to find best matching substring
    best_ratio = 0.0

    for i in range(len(longer) - len(shorter) + 1):
        substring = longer[i:i + len(shorter)]
        ratio = fuzzy_ratio(shorter, substring)
        best_ratio = max(best_ratio, ratio)

    return best_ratio


def fuzzy_match_companies(
    name1: str,
    name2: str,
    threshold: float = 0.85
) -> Tuple[bool, float, Dict[str, float]]:
    """
    Match two company names using multiple fuzzy algorithms.

    Args:
        name1: First company name
        name2: Second company name
        threshold: Minimum combined score to consider a match (default: 0.85)

    Returns:
        Tuple of:
        - is_match: Boolean indicating if names match above threshold
        - combined_score: Weighted average of all algorithms (0.0 - 1.0)
        - scores: Dictionary with individual algorithm scores

    Algorithm Weights:
        - token_sort_ratio: 40% (handles word order)
        - partial_ratio: 30% (handles abbreviations)
        - fuzzy_ratio: 30% (overall similarity)

    Example:
        is_match, score, details = fuzzy_match_companies(
            "Tata Consultancy Services Ltd",
            "TCS Limited"
        )
        print(f"Match: {is_match}, Score: {score:.2f}")
        print(f"Details: {details}")
    """
    # Clean names
    clean1 = clean_company_name(name1)
    clean2 = clean_company_name(name2)

    # Early exit if either name is empty
    if not clean1 or not clean2:
        return False, 0.0, {}

    # Calculate individual scores
    token_score = token_sort_ratio(clean1, clean2)
    partial_score = partial_ratio(clean1, clean2)
    overall_score = fuzzy_ratio(clean1, clean2)

    # Weighted combination
    combined_score = (
        token_score * 0.40 +
        partial_score * 0.30 +
        overall_score * 0.30
    )

    scores = {
        "token_sort_ratio": token_score,
        "partial_ratio": partial_score,
        "fuzzy_ratio": overall_score,
        "combined_score": combined_score,
        "clean_name1": clean1,
        "clean_name2": clean2
    }

    is_match = combined_score >= threshold

    logger.debug(
        f"Fuzzy match: '{name1}' vs '{name2}' -> "
        f"Score: {combined_score:.3f}, Match: {is_match}"
    )

    return is_match, combined_score, scores


def find_best_matches(
    source_name: str,
    candidate_names: List[str],
    top_k: int = 3,
    min_threshold: float = 0.70
) -> List[Tuple[str, float]]:
    """
    Find best matching names from a list of candidates.

    Args:
        source_name: Name to match
        candidate_names: List of candidate names to match against
        top_k: Number of top matches to return (default: 3)
        min_threshold: Minimum score to include in results (default: 0.70)

    Returns:
        List of (candidate_name, score) tuples, sorted by score descending

    Example:
        candidates = [
            "Tata Consultancy Services",
            "Tata Motors Limited",
            "Infosys Technologies",
            "TCS Limited"
        ]

        matches = find_best_matches("TCS Ltd", candidates, top_k=2)
        # Returns:
        # [
        #     ("TCS Limited", 0.95),
        #     ("Tata Consultancy Services", 0.88)
        # ]
    """
    scored_matches = []

    for candidate in candidate_names:
        is_match, score, details = fuzzy_match_companies(
            source_name,
            candidate,
            threshold=min_threshold
        )

        if is_match:
            scored_matches.append((candidate, score))

    # Sort by score descending
    scored_matches.sort(key=lambda x: x[1], reverse=True)

    # Return top K
    return scored_matches[:top_k]


def batch_fuzzy_match(
    source_records: List[Dict],
    target_records: List[Dict],
    source_name_key: str = "name",
    target_name_key: str = "name",
    threshold: float = 0.85
) -> List[Dict]:
    """
    Batch fuzzy match two lists of company records.

    Args:
        source_records: List of source records (e.g., BSE companies)
        target_records: List of target records (e.g., NSE companies)
        source_name_key: Key for company name in source records
        target_name_key: Key for company name in target records
        threshold: Minimum match score (default: 0.85)

    Returns:
        List of match dictionaries with source and target records + match score

    Example:
        bse_records = [
            {"code": "500570", "name": "Tata Consultancy Services Ltd"},
            {"code": "500209", "name": "Infosys Ltd"}
        ]

        nse_records = [
            {"symbol": "TCS", "name": "Tata Consultancy"},
            {"symbol": "INFY", "name": "Infosys Limited"}
        ]

        matches = batch_fuzzy_match(bse_records, nse_records)
        print(f"Found {len(matches)} matches")
    """
    matches = []

    for source_rec in source_records:
        source_name = source_rec.get(source_name_key, "")
        if not source_name:
            continue

        best_match = None
        best_score = 0.0

        for target_rec in target_records:
            target_name = target_rec.get(target_name_key, "")
            if not target_name:
                continue

            is_match, score, details = fuzzy_match_companies(
                source_name,
                target_name,
                threshold=threshold
            )

            if is_match and score > best_score:
                best_match = target_rec
                best_score = score

        if best_match:
            match_record = {
                "source": source_rec,
                "target": best_match,
                "match_score": best_score,
                "match_method": "fuzzy_name",
                "source_name": source_name,
                "target_name": best_match.get(target_name_key, "")
            }
            matches.append(match_record)

    logger.info(
        f"Batch fuzzy matching complete: {len(matches)} matches from "
        f"{len(source_records)} source records ({len(matches)/max(len(source_records), 1)*100:.1f}%)"
    )

    return matches


if __name__ == "__main__":
    # Demo: Fuzzy name matching
    logging.basicConfig(level=logging.INFO)

    print("=== Fuzzy Name Matching Demo ===\n")

    # Test 1: Direct matching
    print("1. Direct name matching:")
    test_pairs = [
        ("Tata Consultancy Services Ltd", "TCS Limited"),
        ("HDFC Bank Limited", "HDFC Bank Ltd"),
        ("Infosys Technologies", "Infosys Limited"),
        ("Reliance Industries", "Reliance Petroleum")  # Should NOT match
    ]

    for name1, name2 in test_pairs:
        is_match, score, details = fuzzy_match_companies(name1, name2)
        print(f"  {name1} <-> {name2}")
        print(f"    Match: {is_match}, Score: {score:.3f}")
        print(f"    Clean: '{details['clean_name1']}' vs '{details['clean_name2']}'")
        print()

    # Test 2: Find best matches
    print("2. Find best matches from candidates:")
    candidates = [
        "Tata Consultancy Services Limited",
        "Tata Motors Limited",
        "Tata Steel Limited",
        "Infosys Technologies",
        "TCS Limited"
    ]

    matches = find_best_matches("TCS Ltd", candidates, top_k=3)
    print("  Query: TCS Ltd")
    for name, score in matches:
        print(f"    {name}: {score:.3f}")