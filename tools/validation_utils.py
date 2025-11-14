"""
Validation Utilities - Data quality checks for financial data

Validates OHLC prices, financial statements, date ranges, and other critical data.
All validators return (is_valid: bool, errors: List[str]) for detailed feedback.

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


def validate_ohlc(
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: Optional[int] = None,
    min_price: float = 0.01,
    max_price: float = 1_000_000.0
) -> Tuple[bool, List[str]]:
    """
    Validate OHLC (Open, High, Low, Close) price data.

    Args:
        open_price: Opening price
        high: High price of the day
        low: Low price of the day
        close: Closing price
        volume: Trading volume (optional)
        min_price: Minimum valid price (default: 0.01)
        max_price: Maximum valid price (default: 1,000,000)

    Returns:
        (is_valid, errors): Tuple of validation result and list of error messages

    Validation Rules:
        - All prices must be positive and within min/max range
        - high >= open, close, low
        - low <= open, close, high
        - Volume (if provided) must be non-negative

    Example:
        is_valid, errors = validate_ohlc(
            open_price=100.0,
            high=105.0,
            low=98.0,
            close=103.0,
            volume=1_000_000
        )
        if not is_valid:
            print(f"Validation failed: {errors}")
    """
    errors = []

    # Check for None values
    if any(x is None for x in [open_price, high, low, close]):
        errors.append("OHLC values cannot be None")
        return False, errors

    # Range validation
    for price_name, price_value in [
        ("open", open_price),
        ("high", high),
        ("low", low),
        ("close", close)
    ]:
        if price_value < min_price:
            errors.append(f"{price_name.capitalize()} price {price_value} below minimum {min_price}")
        if price_value > max_price:
            errors.append(f"{price_name.capitalize()} price {price_value} above maximum {max_price}")

    # OHLC relationship validation
    if high < low:
        errors.append(f"High ({high}) cannot be less than Low ({low})")

    if high < open_price:
        errors.append(f"High ({high}) cannot be less than Open ({open_price})")

    if high < close:
        errors.append(f"High ({high}) cannot be less than Close ({close})")

    if low > open_price:
        errors.append(f"Low ({low}) cannot be greater than Open ({open_price})")

    if low > close:
        errors.append(f"Low ({low}) cannot be greater than Close ({close})")

    # Volume validation
    if volume is not None:
        if volume < 0:
            errors.append(f"Volume ({volume}) cannot be negative")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"OHLC validation failed: {errors}")

    return is_valid, errors


def validate_financials(
    revenue: Optional[float],
    net_profit: Optional[float],
    eps: Optional[float],
    allow_negative_profit: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate financial statement data.

    Args:
        revenue: Total revenue/sales
        net_profit: Net profit after tax (PAT)
        eps: Earnings per share
        allow_negative_profit: If True, allow negative profit (losses)

    Returns:
        (is_valid, errors): Tuple of validation result and list of error messages

    Validation Rules:
        - Revenue must be positive (can't be negative)
        - Net profit can be negative (losses) if allow_negative_profit=True
        - EPS magnitude should be reasonable relative to profit
        - All values must be finite (not NaN or Inf)

    Example:
        is_valid, errors = validate_financials(
            revenue=1000.0,  # Crores
            net_profit=150.0,
            eps=12.5
        )
    """
    errors = []

    # Revenue validation
    if revenue is not None:
        if not isinstance(revenue, (int, float)) or not (-1e15 < revenue < 1e15):
            errors.append(f"Revenue {revenue} is not a valid finite number")
        elif revenue < 0:
            errors.append(f"Revenue ({revenue}) cannot be negative")
        elif revenue == 0:
            errors.append("Revenue cannot be zero")

    # Net profit validation
    if net_profit is not None:
        if not isinstance(net_profit, (int, float)) or not (-1e15 < net_profit < 1e15):
            errors.append(f"Net profit {net_profit} is not a valid finite number")
        elif not allow_negative_profit and net_profit < 0:
            errors.append(f"Net profit ({net_profit}) cannot be negative")

    # EPS validation
    if eps is not None:
        if not isinstance(eps, (int, float)) or not (-1e6 < eps < 1e6):
            errors.append(f"EPS {eps} is not a valid finite number")

    # Cross-validation: EPS vs Net Profit
    if net_profit is not None and eps is not None and revenue is not None:
        # Sanity check: EPS shouldn't wildly exceed net profit
        # (assuming reasonable share count between 1M and 10B shares)
        min_shares = 1_000_000  # 1 million shares
        max_shares = 10_000_000_000  # 10 billion shares

        implied_net_profit_min = eps * min_shares
        implied_net_profit_max = eps * max_shares

        # Check if net profit falls within plausible range
        if net_profit > 0:  # Only check for profitable companies
            if implied_net_profit_min > net_profit * 1000:  # EPS way too high
                errors.append(
                    f"EPS ({eps}) inconsistent with net profit ({net_profit}): "
                    f"implies unreasonably low share count"
                )

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"Financial validation failed: {errors}")

    return is_valid, errors


def validate_date_range(
    start_date: str,
    end_date: str,
    min_date: str = "2015-01-01",
    max_date: Optional[str] = None,
    date_format: str = "%Y-%m-%d"
) -> Tuple[bool, List[str]]:
    """
    Validate date range for historical data queries.

    Args:
        start_date: Start date string
        end_date: End date string
        min_date: Earliest allowed date (default: 2015-01-01)
        max_date: Latest allowed date (default: today)
        date_format: Date string format (default: ISO 8601 YYYY-MM-DD)

    Returns:
        (is_valid, errors): Tuple of validation result and list of error messages

    Validation Rules:
        - Both dates must be valid and parseable
        - start_date must be before end_date
        - Both dates must be within min_date and max_date range
        - Date range should be reasonable (<20 years)

    Example:
        is_valid, errors = validate_date_range(
            start_date="2022-01-01",
            end_date="2025-11-13"
        )
    """
    errors = []

    # Set max_date to today if not provided
    if max_date is None:
        max_date = datetime.now().strftime(date_format)

    # Parse dates
    try:
        start_dt = datetime.strptime(start_date, date_format)
    except ValueError as e:
        errors.append(f"Invalid start_date format '{start_date}': {e}")
        return False, errors

    try:
        end_dt = datetime.strptime(end_date, date_format)
    except ValueError as e:
        errors.append(f"Invalid end_date format '{end_date}': {e}")
        return False, errors

    try:
        min_dt = datetime.strptime(min_date, date_format)
    except ValueError as e:
        errors.append(f"Invalid min_date format '{min_date}': {e}")
        return False, errors

    try:
        max_dt = datetime.strptime(max_date, date_format)
    except ValueError as e:
        errors.append(f"Invalid max_date format '{max_date}': {e}")
        return False, errors

    # Validate date ordering
    if start_dt > end_dt:
        errors.append(
            f"start_date ({start_date}) must be before end_date ({end_date})"
        )

    if start_dt < min_dt:
        errors.append(
            f"start_date ({start_date}) is before minimum allowed date ({min_date})"
        )

    if end_dt > max_dt:
        errors.append(
            f"end_date ({end_date}) is after maximum allowed date ({max_date})"
        )

    # Check for reasonable range (not more than 20 years)
    date_diff_days = (end_dt - start_dt).days
    max_range_days = 20 * 365  # 20 years

    if date_diff_days > max_range_days:
        errors.append(
            f"Date range too large: {date_diff_days} days "
            f"(maximum: {max_range_days} days / 20 years)"
        )

    if date_diff_days < 0:
        errors.append(f"Date range is negative: {date_diff_days} days")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"Date range validation failed: {errors}")

    return is_valid, errors


def validate_upper_circuit_label(
    price_open: float,
    price_close: float,
    circuit_threshold: float = 5.0,
    max_circuit: float = 20.0
) -> Tuple[bool, List[str]]:
    """
    Validate if a price movement qualifies as upper circuit.

    Args:
        price_open: Opening price
        price_close: Closing price
        circuit_threshold: Minimum percentage gain to qualify (default: 5%)
        max_circuit: Maximum reasonable circuit percentage (default: 20%)

    Returns:
        (is_valid, errors): Tuple of validation result and list of error messages

    Example:
        # Check if TCS hit upper circuit (+6.5%)
        is_valid, errors = validate_upper_circuit_label(
            price_open=3500.0,
            price_close=3727.5,
            circuit_threshold=5.0
        )
    """
    errors = []

    # Basic price validation
    if price_open <= 0:
        errors.append(f"Opening price ({price_open}) must be positive")
        return False, errors

    if price_close <= 0:
        errors.append(f"Closing price ({price_close}) must be positive")
        return False, errors

    # Calculate percentage change
    pct_change = ((price_close - price_open) / price_open) * 100

    # Check if meets circuit threshold
    if pct_change < circuit_threshold:
        errors.append(
            f"Price change ({pct_change:.2f}%) below circuit threshold ({circuit_threshold}%)"
        )

    # Check if within reasonable max circuit
    if pct_change > max_circuit:
        errors.append(
            f"Price change ({pct_change:.2f}%) exceeds maximum circuit ({max_circuit}%). "
            f"May be data error or special case."
        )

    is_valid = len(errors) == 0

    return is_valid, errors


if __name__ == "__main__":
    # Demo: Test validation functions
    logging.basicConfig(level=logging.INFO)

    print("=== OHLC Validation ===")
    valid, errs = validate_ohlc(100.0, 105.0, 98.0, 103.0, volume=1_000_000)
    print(f"Valid OHLC: {valid}")

    valid, errs = validate_ohlc(100.0, 95.0, 98.0, 103.0)  # Invalid: high < close
    print(f"Invalid OHLC: {valid}, Errors: {errs}")

    print("\n=== Financial Validation ===")
    valid, errs = validate_financials(revenue=1000.0, net_profit=150.0, eps=12.5)
    print(f"Valid financials: {valid}")

    valid, errs = validate_financials(revenue=-100.0, net_profit=150.0, eps=12.5)
    print(f"Invalid financials: {valid}, Errors: {errs}")

    print("\n=== Date Range Validation ===")
    valid, errs = validate_date_range("2022-01-01", "2025-11-13")
    print(f"Valid date range: {valid}")

    valid, errs = validate_date_range("2025-11-13", "2022-01-01")  # Reversed
    print(f"Invalid date range: {valid}, Errors: {errs}")

    print("\n=== Upper Circuit Validation ===")
    valid, errs = validate_upper_circuit_label(3500.0, 3727.5)  # +6.5%
    print(f"Valid upper circuit: {valid}")

    valid, errs = validate_upper_circuit_label(3500.0, 3600.0)  # +2.9% (too low)
    print(f"Invalid upper circuit: {valid}, Errors: {errs}")
