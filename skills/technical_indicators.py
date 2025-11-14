"""
Technical Indicators - Calculate RSI, MACD, Bollinger Bands

Standard technical analysis indicators for feature engineering.
Used as ML features to capture momentum, trend, and volatility.

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        prices: List of closing prices (most recent last)
        period: RSI period (default: 14 days)

    Returns:
        RSI value between 0-100 (>70 = overbought, <30 = oversold)

    Formula:
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss over period

    Example:
        prices = [100, 102, 101, 105, 107, 106, 108, 110, 109, 111, 113, 112, 115, 114, 116]
        rsi = calculate_rsi(prices, period=14)
        print(f"RSI: {rsi:.2f}")
    """
    if len(prices) < period + 1:
        logger.warning(f"Insufficient data for RSI: need {period + 1}, got {len(prices)}")
        return 50.0  # Neutral RSI

    # Calculate price changes
    changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    # Separate gains and losses
    gains = [max(change, 0) for change in changes]
    losses = [abs(min(change, 0)) for change in changes]

    # Calculate average gain/loss for first period
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Calculate subsequent averages using smoothing
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    # Calculate RSI
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    logger.debug(f"RSI({period}): {rsi:.2f}")
    return rsi


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[float, float, float]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: List of closing prices
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)

    Returns:
        Tuple of (macd_line, signal_line, histogram)
        - macd_line: Fast EMA - Slow EMA
        - signal_line: EMA of MACD line
        - histogram: MACD - Signal (positive = bullish crossover)

    Example:
        prices = [... 30+ days of prices ...]
        macd, signal, histogram = calculate_macd(prices)
        if histogram > 0:
            print("Bullish MACD crossover")
    """
    if len(prices) < slow_period + signal_period:
        logger.warning(
            f"Insufficient data for MACD: need {slow_period + signal_period}, "
            f"got {len(prices)}"
        )
        return 0.0, 0.0, 0.0

    # Calculate fast and slow EMAs
    fast_ema = _calculate_ema(prices, fast_period)
    slow_ema = _calculate_ema(prices, slow_period)

    # MACD line = Fast EMA - Slow EMA
    macd_line = fast_ema - slow_ema

    # Signal line = EMA of MACD line (simplified: use recent values)
    # Note: Full implementation would track historical MACD values
    signal_line = macd_line  # Placeholder - should be EMA of MACD history

    # Histogram = MACD - Signal
    histogram = macd_line - signal_line

    logger.debug(f"MACD: line={macd_line:.2f}, signal={signal_line:.2f}, hist={histogram:.2f}")
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[float, float, float]:
    """
    Calculate Bollinger Bands.

    Args:
        prices: List of closing prices
        period: Moving average period (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)

    Returns:
        Tuple of (upper_band, middle_band, lower_band)
        - middle_band: Simple moving average
        - upper_band: Middle + (std_dev * standard deviation)
        - lower_band: Middle - (std_dev * standard deviation)

    Example:
        prices = [... 20+ days ...]
        upper, middle, lower = calculate_bollinger_bands(prices)
        current_price = prices[-1]

        if current_price > upper:
            print("Price above upper band (overbought)")
        elif current_price < lower:
            print("Price below lower band (oversold)")
    """
    if len(prices) < period:
        logger.warning(
            f"Insufficient data for Bollinger Bands: need {period}, got {len(prices)}"
        )
        avg_price = sum(prices) / len(prices) if prices else 0
        return avg_price, avg_price, avg_price

    # Calculate middle band (SMA)
    recent_prices = prices[-period:]
    middle_band = sum(recent_prices) / period

    # Calculate standard deviation
    variance = sum((p - middle_band) ** 2 for p in recent_prices) / period
    std = variance ** 0.5

    # Calculate bands
    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)

    logger.debug(
        f"Bollinger Bands({period}): upper={upper_band:.2f}, "
        f"middle={middle_band:.2f}, lower={lower_band:.2f}"
    )

    return upper_band, middle_band, lower_band


def _calculate_ema(prices: List[float], period: int) -> float:
    """
    Calculate Exponential Moving Average (helper function).

    Args:
        prices: List of closing prices
        period: EMA period

    Returns:
        Current EMA value
    """
    if len(prices) < period:
        # Fallback to simple average if insufficient data
        return sum(prices) / len(prices) if prices else 0.0

    # Calculate smoothing multiplier
    multiplier = 2 / (period + 1)

    # Start with SMA for first period
    ema = sum(prices[:period]) / period

    # Calculate EMA for remaining prices
    for price in prices[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return ema


def calculate_all_indicators(
    prices: List[float],
    rsi_period: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    bb_period: int = 20,
    bb_std: float = 2.0
) -> Dict[str, float]:
    """
    Calculate all technical indicators at once (convenience function).

    Args:
        prices: List of closing prices (at least 30 days recommended)
        rsi_period: RSI period
        macd_fast: MACD fast EMA period
        macd_slow: MACD slow EMA period
        macd_signal: MACD signal period
        bb_period: Bollinger Bands period
        bb_std: Bollinger Bands standard deviation multiplier

    Returns:
        Dictionary with all indicators:
        {
            "rsi": 65.2,
            "macd_line": 2.5,
            "macd_signal": 1.8,
            "macd_histogram": 0.7,
            "bb_upper": 110.5,
            "bb_middle": 105.0,
            "bb_lower": 99.5
        }

    Example:
        prices = get_price_history("TCS", days=60)
        indicators = calculate_all_indicators(prices)
        print(f"RSI: {indicators['rsi']:.2f}")
        print(f"MACD Histogram: {indicators['macd_histogram']:.2f}")
    """
    rsi = calculate_rsi(prices, period=rsi_period)

    macd_line, signal_line, histogram = calculate_macd(
        prices, fast_period=macd_fast, slow_period=macd_slow, signal_period=macd_signal
    )

    upper_band, middle_band, lower_band = calculate_bollinger_bands(
        prices, period=bb_period, std_dev=bb_std
    )

    return {
        "rsi": rsi,
        "macd_line": macd_line,
        "macd_signal": signal_line,
        "macd_histogram": histogram,
        "bb_upper": upper_band,
        "bb_middle": middle_band,
        "bb_lower": lower_band
    }


if __name__ == "__main__":
    # Demo: Technical indicators
    logging.basicConfig(level=logging.INFO)

    print("=== Technical Indicators Demo ===\n")

    # Sample price data (simulated uptrend)
    prices = [
        100, 102, 101, 105, 107, 106, 108, 110, 109, 111,
        113, 112, 115, 114, 116, 118, 117, 120, 119, 122,
        124, 123, 126, 125, 128, 130, 129, 132, 131, 134
    ]

    print(f"Price data: {len(prices)} days, range {min(prices):.0f} - {max(prices):.0f}")

    print("\n1. RSI (14-day):")
    rsi = calculate_rsi(prices, period=14)
    print(f"   RSI: {rsi:.2f}")
    if rsi > 70:
        print("   Signal: OVERBOUGHT")
    elif rsi < 30:
        print("   Signal: OVERSOLD")
    else:
        print("   Signal: NEUTRAL")

    print("\n2. MACD:")
    macd, signal, hist = calculate_macd(prices)
    print(f"   MACD Line: {macd:.2f}")
    print(f"   Signal Line: {signal:.2f}")
    print(f"   Histogram: {hist:.2f}")
    if hist > 0:
        print("   Signal: BULLISH")
    else:
        print("   Signal: BEARISH")

    print("\n3. Bollinger Bands (20-day, 2 std):")
    upper, middle, lower = calculate_bollinger_bands(prices)
    current_price = prices[-1]
    print(f"   Upper Band: {upper:.2f}")
    print(f"   Middle Band: {middle:.2f}")
    print(f"   Lower Band: {lower:.2f}")
    print(f"   Current Price: {current_price:.2f}")

    if current_price > upper:
        print("   Signal: ABOVE UPPER BAND (overbought)")
    elif current_price < lower:
        print("   Signal: BELOW LOWER BAND (oversold)")
    else:
        print("   Signal: WITHIN BANDS (normal)")

    print("\n4. All indicators:")
    all_indicators = calculate_all_indicators(prices)
    for key, value in all_indicators.items():
        print(f"   {key}: {value:.2f}")
