"""
Backtest Validation Framework

Prevents common backtesting errors like look-ahead bias, survivorship bias,
and data integrity issues.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class BacktestValidator:
    """
    Validates backtest integrity to prevent common errors
    """

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_no_look_ahead_bias(
        self,
        signal_date: datetime,
        data_end_date: datetime,
        entry_price: float,
        data: pd.DataFrame
    ) -> bool:
        """
        Ensure signals don't use future data

        Args:
            signal_date: Date when signal was generated
            data_end_date: Last date that should be in the data
            entry_price: Price at which entry is planned
            data: DataFrame with price data

        Returns:
            True if valid, False if look-ahead bias detected
        """
        # Check 1: Signal date must be <= data end date
        if signal_date > data_end_date:
            self.errors.append(
                f"Look-ahead bias: Signal date {signal_date} is after "
                f"backtest end date {data_end_date}"
            )
            return False

        # Check 2: Entry price must exist in historical data before end date
        if not data.empty:
            valid_data = data[data.index <= data_end_date]

            # Check if entry price matches any price in valid data
            price_columns = ['close', 'open', 'high', 'low']
            price_exists = False

            for col in price_columns:
                if col in valid_data.columns:
                    if entry_price in valid_data[col].values:
                        price_exists = True
                        break

            if not price_exists:
                # Check if price is close to any valid price (within 0.1%)
                last_close = valid_data['close'].iloc[-1] if 'close' in valid_data.columns else None
                if last_close:
                    price_diff = abs((entry_price - last_close) / last_close)
                    if price_diff > 0.001:  # More than 0.1% difference
                        self.warnings.append(
                            f"Entry price {entry_price} doesn't match historical data. "
                            f"Last valid close: {last_close} (diff: {price_diff:.2%})"
                        )

        return True

    def validate_data_integrity(
        self,
        data: pd.DataFrame,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> bool:
        """
        Validate data quality and completeness
        """
        if data.empty:
            self.errors.append(f"No data for {symbol}")
            return False

        # Check date range
        actual_start = data.index.min()
        actual_end = data.index.max()

        # Data should not extend beyond end_date
        if actual_end > end_date:
            self.errors.append(
                f"Data leak: {symbol} data extends to {actual_end}, "
                f"but backtest ends {end_date}"
            )
            return False

        # Check for impossible prices
        if 'close' in data.columns:
            if (data['close'] <= 0).any():
                self.errors.append(f"Invalid prices: {symbol} has zero or negative prices")
                return False

            # Check for extreme price jumps (>50% in one day)
            price_changes = data['close'].pct_change()
            extreme_moves = price_changes[abs(price_changes) > 0.5]
            if not extreme_moves.empty:
                self.warnings.append(
                    f"Extreme price moves in {symbol}: "
                    f"{len(extreme_moves)} days with >50% change"
                )

        return True

    def validate_signal_timing(
        self,
        signal_date: datetime,
        entry_date: datetime,
        data_end_date: datetime
    ) -> bool:
        """
        Ensure proper signal generation and entry timing
        """
        # Entry must be after signal generation
        if entry_date <= signal_date:
            self.errors.append(
                f"Invalid timing: Entry date {entry_date} must be after "
                f"signal date {signal_date}"
            )
            return False

        # Signal must be generated before data ends
        if signal_date > data_end_date:
            self.errors.append(
                f"Future signal: Signal generated {signal_date} after "
                f"data ends {data_end_date}"
            )
            return False

        return True

    def validate_price_sanity(
        self,
        entry_price: float,
        stop_loss: float,
        target: float,
        current_price: float
    ) -> bool:
        """
        Validate that prices make logical sense
        """
        # Stop loss should be below entry for long positions
        if stop_loss >= entry_price:
            self.warnings.append(
                f"Stop loss {stop_loss} >= entry {entry_price} for long position"
            )

        # Target should be above entry for long positions
        if target <= entry_price:
            self.warnings.append(
                f"Target {target} <= entry {entry_price} for long position"
            )

        # Entry should be close to current price (within 10%)
        price_diff = abs((entry_price - current_price) / current_price)
        if price_diff > 0.1:
            self.warnings.append(
                f"Entry price {entry_price} is {price_diff:.1%} away from "
                f"current price {current_price}"
            )

        return len(self.errors) == 0

    def validate_backtest_params(
        self,
        start_date: str,
        end_date: str,
        symbols: List[str]
    ) -> bool:
        """
        Validate backtest parameters before running
        """
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            self.errors.append(f"Invalid date format: {e}")
            return False

        # End date should be before today to avoid incomplete data
        if end_dt >= datetime.now():
            self.warnings.append(
                f"End date {end_date} includes incomplete current day data"
            )

        # Start should be before end
        if start_dt >= end_dt:
            self.errors.append(
                f"Start date {start_date} must be before end date {end_date}"
            )
            return False

        # Check for reasonable date range (not too long)
        days_diff = (end_dt - start_dt).days
        if days_diff > 3650:  # 10 years
            self.warnings.append(
                f"Very long backtest period: {days_diff} days"
            )

        # Validate symbols
        if not symbols:
            self.errors.append("No symbols provided for backtest")
            return False

        # Check for duplicate symbols
        if len(symbols) != len(set(symbols)):
            self.warnings.append("Duplicate symbols in backtest universe")

        return len(self.errors) == 0

    def get_report(self) -> str:
        """
        Generate validation report
        """
        report = []

        if self.errors:
            report.append("❌ ERRORS (Must Fix):")
            for error in self.errors:
                report.append(f"  - {error}")

        if self.warnings:
            report.append("\n⚠️ WARNINGS (Should Review):")
            for warning in self.warnings:
                report.append(f"  - {warning}")

        if not self.errors and not self.warnings:
            report.append("✅ All validations passed!")

        return "\n".join(report)

    def clear(self):
        """Clear errors and warnings for next validation"""
        self.errors = []
        self.warnings = []


# Utility functions for common validation tasks

def ensure_exclusive_end_date(
    data: pd.DataFrame,
    end_date: datetime
) -> pd.DataFrame:
    """
    Ensure data doesn't include the end date (exclusive end)

    This prevents look-ahead bias by removing any data on or after end_date
    """
    if data.empty:
        return data

    # Filter to exclude end date
    filtered = data[data.index < end_date]

    if len(filtered) < len(data):
        logger.info(
            f"Removed {len(data) - len(filtered)} rows on or after {end_date}"
        )

    return filtered


def validate_signal_generation(
    signal: Dict[str, Any],
    backtest_end: datetime
) -> bool:
    """
    Quick validation that a signal doesn't use future data
    """
    if 'timestamp' in signal:
        signal_time = pd.to_datetime(signal['timestamp'])
        if signal_time > backtest_end:
            logger.error(
                f"Signal timestamp {signal_time} is after "
                f"backtest end {backtest_end}"
            )
            return False

    if 'entry_date' in signal:
        entry_date = pd.to_datetime(signal['entry_date'])
        if entry_date > backtest_end:
            logger.error(
                f"Entry date {entry_date} is after "
                f"backtest end {backtest_end}"
            )
            return False

    return True


def add_safety_buffer(end_date: str, buffer_days: int = 1) -> str:
    """
    Subtract buffer days from end date to ensure no look-ahead

    Args:
        end_date: Date string in YYYY-MM-DD format
        buffer_days: Number of days to subtract (default 1)

    Returns:
        New end date string with buffer applied
    """
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    safe_end_dt = end_dt - timedelta(days=buffer_days)
    return safe_end_dt.strftime("%Y-%m-%d")