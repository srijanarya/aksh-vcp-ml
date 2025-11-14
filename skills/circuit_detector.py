"""
Circuit Detector - Detect upper/lower circuit hits in Indian market

Circuit breakers are price limits (5-20%) set by SEBI to prevent excessive
volatility. When a stock hits upper circuit, it cannot trade higher that day.

This is our PRIMARY LABEL for the ML classification task.

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def detect_upper_circuit(
    open_price: float,
    close_price: float,
    high_price: float,
    volume: int,
    prev_close: Optional[float] = None,
    circuit_threshold: float = 5.0,
    volume_surge_threshold: float = 2.0
) -> Tuple[bool, Dict]:
    """
    Detect if stock hit upper circuit.

    Args:
        open_price: Opening price
        close_price: Closing price
        high_price: High price of the day
        volume: Trading volume
        prev_close: Previous day's close (if available)
        circuit_threshold: Minimum % gain to qualify (default: 5%)
        volume_surge_threshold: Volume surge multiplier (default: 2x)

    Returns:
        Tuple of:
        - is_upper_circuit: Boolean indicating circuit hit
        - details: Dictionary with diagnostic information

    Detection Criteria:
        1. Close >= Open + circuit_threshold% (gain threshold)
        2. Close == High (locked at upper limit)
        3. Volume surge (optional, for confirmation)

    Example:
        is_circuit, details = detect_upper_circuit(
            open_price=100.0,
            close_price=107.0,  # +7% gain
            high_price=107.0,   # Locked at high
            volume=5_000_000,
            prev_close=100.0
        )
        print(f"Upper circuit: {is_circuit}, Gain: {details['gain_pct']:.1f}%")
    """
    details = {
        "open": open_price,
        "close": close_price,
        "high": high_price,
        "gain_pct": 0.0,
        "locked_at_high": False,
        "volume_surge": False,
        "circuit_type": None
    }

    # Calculate percentage gain
    if prev_close:
        reference_price = prev_close
    else:
        reference_price = open_price

    gain_pct = ((close_price - reference_price) / reference_price) * 100
    details["gain_pct"] = gain_pct

    # Check if locked at high (close == high within 0.1% tolerance)
    price_tolerance = close_price * 0.001  # 0.1% tolerance
    locked_at_high = abs(close_price - high_price) <= price_tolerance
    details["locked_at_high"] = locked_at_high

    # Check if gain meets threshold
    meets_threshold = gain_pct >= circuit_threshold

    # Determine circuit type based on gain percentage
    if gain_pct >= 20.0:
        details["circuit_type"] = "20%"
    elif gain_pct >= 10.0:
        details["circuit_type"] = "10%"
    elif gain_pct >= 5.0:
        details["circuit_type"] = "5%"

    # Primary detection: gain + locked at high
    is_upper_circuit = meets_threshold and locked_at_high

    # Optional: Check volume surge (not required but adds confidence)
    # Note: Need previous day's volume to calculate surge - skipped for now
    details["volume_surge"] = False  # Placeholder

    logger.debug(
        f"Upper circuit check: gain={gain_pct:.2f}%, locked={locked_at_high}, "
        f"result={is_upper_circuit}"
    )

    return is_upper_circuit, details


def detect_lower_circuit(
    open_price: float,
    close_price: float,
    low_price: float,
    volume: int,
    prev_close: Optional[float] = None,
    circuit_threshold: float = -5.0
) -> Tuple[bool, Dict]:
    """
    Detect if stock hit lower circuit (opposite of upper circuit).

    Args:
        open_price: Opening price
        close_price: Closing price
        low_price: Low price of the day
        volume: Trading volume
        prev_close: Previous day's close
        circuit_threshold: Maximum % loss to qualify (default: -5%)

    Returns:
        Tuple of (is_lower_circuit, details)

    Example:
        is_circuit, details = detect_lower_circuit(
            open_price=100.0,
            close_price=93.0,   # -7% loss
            low_price=93.0,     # Locked at low
            volume=10_000_000,
            prev_close=100.0
        )
    """
    details = {
        "open": open_price,
        "close": close_price,
        "low": low_price,
        "loss_pct": 0.0,
        "locked_at_low": False,
        "circuit_type": None
    }

    # Calculate percentage loss
    if prev_close:
        reference_price = prev_close
    else:
        reference_price = open_price

    loss_pct = ((close_price - reference_price) / reference_price) * 100
    details["loss_pct"] = loss_pct

    # Check if locked at low
    price_tolerance = close_price * 0.001
    locked_at_low = abs(close_price - low_price) <= price_tolerance
    details["locked_at_low"] = locked_at_low

    # Check if loss meets threshold
    meets_threshold = loss_pct <= circuit_threshold

    # Determine circuit type
    if loss_pct <= -20.0:
        details["circuit_type"] = "-20%"
    elif loss_pct <= -10.0:
        details["circuit_type"] = "-10%"
    elif loss_pct <= -5.0:
        details["circuit_type"] = "-5%"

    is_lower_circuit = meets_threshold and locked_at_low

    logger.debug(
        f"Lower circuit check: loss={loss_pct:.2f}%, locked={locked_at_low}, "
        f"result={is_lower_circuit}"
    )

    return is_lower_circuit, details


def is_circuit_hit(
    ohlc_data: Dict,
    prev_close: Optional[float] = None,
    upper_threshold: float = 5.0,
    lower_threshold: float = -5.0
) -> Tuple[str, Dict]:
    """
    Unified circuit detection (checks both upper and lower).

    Args:
        ohlc_data: Dictionary with keys: open, high, low, close, volume
        prev_close: Previous day's close
        upper_threshold: Upper circuit threshold (default: 5%)
        lower_threshold: Lower circuit threshold (default: -5%)

    Returns:
        Tuple of:
        - circuit_status: "UPPER" | "LOWER" | "NONE"
        - details: Diagnostic information

    Example:
        ohlc = {
            "open": 100.0,
            "high": 107.0,
            "low": 99.0,
            "close": 107.0,
            "volume": 5_000_000
        }

        status, details = is_circuit_hit(ohlc, prev_close=100.0)
        if status == "UPPER":
            print(f"Hit upper circuit: +{details['gain_pct']:.1f}%")
    """
    # Extract OHLC
    open_price = ohlc_data.get("open", 0)
    high_price = ohlc_data.get("high", 0)
    low_price = ohlc_data.get("low", 0)
    close_price = ohlc_data.get("close", 0)
    volume = ohlc_data.get("volume", 0)

    # Check upper circuit
    is_upper, upper_details = detect_upper_circuit(
        open_price, close_price, high_price, volume,
        prev_close, upper_threshold
    )

    if is_upper:
        return "UPPER", upper_details

    # Check lower circuit
    is_lower, lower_details = detect_lower_circuit(
        open_price, close_price, low_price, volume,
        prev_close, lower_threshold
    )

    if is_lower:
        return "LOWER", lower_details

    # No circuit hit
    return "NONE", {"status": "normal", "close": close_price}


def find_circuit_hits_in_dataset(
    price_data: List[Dict],
    date_key: str = "date",
    upper_threshold: float = 5.0,
    lower_threshold: float = -5.0
) -> List[Dict]:
    """
    Scan a dataset for circuit hits (batch processing).

    Args:
        price_data: List of OHLC records (must be sorted by date ascending)
        date_key: Key for date field (default: "date")
        upper_threshold: Upper circuit threshold (default: 5%)
        lower_threshold: Lower circuit threshold (default: -5%)

    Returns:
        List of circuit hit records with additional fields:
        - circuit_status: "UPPER" or "LOWER"
        - circuit_details: Diagnostic information
        - original_record: Original OHLC data

    Example:
        price_history = [
            {"date": "2024-11-01", "open": 100, "high": 105, "low": 99, "close": 105, "volume": 1M},
            {"date": "2024-11-02", "open": 105, "high": 112, "low": 104, "close": 112, "volume": 5M},  # Upper circuit
            {"date": "2024-11-03", "open": 112, "high": 115, "low": 110, "close": 113, "volume": 2M},
        ]

        circuits = find_circuit_hits_in_dataset(price_history)
        print(f"Found {len(circuits)} circuit hits")
    """
    circuit_hits = []
    prev_close = None

    for i, record in enumerate(price_data):
        # Check for circuit
        status, details = is_circuit_hit(
            record,
            prev_close=prev_close,
            upper_threshold=upper_threshold,
            lower_threshold=lower_threshold
        )

        if status in ("UPPER", "LOWER"):
            circuit_record = {
                "date": record.get(date_key, ""),
                "circuit_status": status,
                "circuit_details": details,
                "original_record": record,
                "record_index": i
            }
            circuit_hits.append(circuit_record)

            logger.info(
                f"Circuit hit detected: {record.get(date_key)} - {status} "
                f"({details.get('gain_pct', details.get('loss_pct', 0)):.2f}%)"
            )

        # Update prev_close for next iteration
        prev_close = record.get("close", prev_close)

    logger.info(
        f"Circuit scan complete: {len(circuit_hits)} hits from {len(price_data)} records "
        f"({len(circuit_hits)/max(len(price_data), 1)*100:.2f}%)"
    )

    return circuit_hits


def calculate_circuit_statistics(circuit_hits: List[Dict]) -> Dict:
    """
    Calculate statistics on circuit hits.

    Args:
        circuit_hits: List of circuit hit records from find_circuit_hits_in_dataset()

    Returns:
        Dictionary with statistics:
        - total_circuits: Total circuit hits
        - upper_circuits: Count of upper circuits
        - lower_circuits: Count of lower circuits
        - avg_upper_gain: Average gain % for upper circuits
        - avg_lower_loss: Average loss % for lower circuits
        - circuit_type_distribution: Count by circuit type (5%, 10%, 20%)

    Example:
        stats = calculate_circuit_statistics(circuit_hits)
        print(f"Upper circuits: {stats['upper_circuits']}")
        print(f"Avg gain: {stats['avg_upper_gain']:.2f}%")
    """
    upper_circuits = [c for c in circuit_hits if c["circuit_status"] == "UPPER"]
    lower_circuits = [c for c in circuit_hits if c["circuit_status"] == "LOWER"]

    # Calculate average gains/losses
    if upper_circuits:
        upper_gains = [c["circuit_details"]["gain_pct"] for c in upper_circuits]
        avg_upper_gain = sum(upper_gains) / len(upper_gains)
    else:
        avg_upper_gain = 0.0

    if lower_circuits:
        lower_losses = [c["circuit_details"]["loss_pct"] for c in lower_circuits]
        avg_lower_loss = sum(lower_losses) / len(lower_losses)
    else:
        avg_lower_loss = 0.0

    # Circuit type distribution
    circuit_types = {}
    for hit in circuit_hits:
        circuit_type = hit["circuit_details"].get("circuit_type", "unknown")
        circuit_types[circuit_type] = circuit_types.get(circuit_type, 0) + 1

    stats = {
        "total_circuits": len(circuit_hits),
        "upper_circuits": len(upper_circuits),
        "lower_circuits": len(lower_circuits),
        "avg_upper_gain": avg_upper_gain,
        "avg_lower_loss": avg_lower_loss,
        "circuit_type_distribution": circuit_types
    }

    logger.info(
        f"Circuit statistics: {stats['upper_circuits']} upper, "
        f"{stats['lower_circuits']} lower, "
        f"avg gain: {avg_upper_gain:.2f}%"
    )

    return stats


if __name__ == "__main__":
    # Demo: Circuit detection
    logging.basicConfig(level=logging.INFO)

    print("=== Circuit Detector Demo ===\n")

    # Test 1: Upper circuit detection
    print("1. Upper circuit (TCS +7%):")
    is_circuit, details = detect_upper_circuit(
        open_price=3500.0,
        close_price=3745.0,  # +7%
        high_price=3745.0,
        volume=5_000_000,
        prev_close=3500.0
    )
    print(f"  Result: {is_circuit}")
    print(f"  Gain: {details['gain_pct']:.2f}%")
    print(f"  Locked at high: {details['locked_at_high']}")

    # Test 2: Not a circuit (price below high)
    print("\n2. NOT a circuit (closed below high):")
    is_circuit, details = detect_upper_circuit(
        open_price=3500.0,
        close_price=3700.0,  # +5.7% but not locked
        high_price=3750.0,   # High is above close
        volume=3_000_000,
        prev_close=3500.0
    )
    print(f"  Result: {is_circuit}")
    print(f"  Gain: {details['gain_pct']:.2f}%")
    print(f"  Locked at high: {details['locked_at_high']}")

    # Test 3: Batch processing
    print("\n3. Batch circuit detection:")
    price_data = [
        {"date": "2024-11-01", "open": 100, "high": 105, "low": 99, "close": 105, "volume": 1000000},
        {"date": "2024-11-04", "open": 105, "high": 113, "low": 104, "close": 113, "volume": 5000000},  # Upper circuit
        {"date": "2024-11-05", "open": 113, "high": 115, "low": 110, "close": 112, "volume": 2000000},
    ]

    circuits = find_circuit_hits_in_dataset(price_data)
    print(f"  Found {len(circuits)} circuit hits")

    if circuits:
        stats = calculate_circuit_statistics(circuits)
        print(f"  Upper circuits: {stats['upper_circuits']}")
        print(f"  Avg gain: {stats['avg_upper_gain']:.2f}%")
