"""
Fiscal Year Utilities for Indian Markets
Handles conversion between Indian fiscal year (Apr-Mar) and calendar year
"""

from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional

class IndianFiscalYear:
    """
    Indian Fiscal Year runs from April 1 to March 31
    FY2025 = April 1, 2024 to March 31, 2025
    """

    @staticmethod
    def get_fiscal_year(date: datetime) -> int:
        """
        Get fiscal year for a given date

        Args:
            date: Date to check

        Returns:
            Fiscal year (e.g., 2025 for FY2025)
        """
        if date.month >= 4:  # April onwards
            return date.year + 1
        else:  # Jan-Mar
            return date.year

    @staticmethod
    def get_fiscal_quarter(date: datetime) -> Tuple[str, int]:
        """
        Get fiscal quarter for a given date

        Returns:
            Tuple of (quarter_string, fiscal_year)
            e.g., ("Q2", 2025) for July-Sept 2024
        """
        month = date.month

        if month in [4, 5, 6]:  # Apr-Jun
            quarter = "Q1"
        elif month in [7, 8, 9]:  # Jul-Sep
            quarter = "Q2"
        elif month in [10, 11, 12]:  # Oct-Dec
            quarter = "Q3"
        else:  # Jan-Mar
            quarter = "Q4"

        fy = IndianFiscalYear.get_fiscal_year(date)
        return quarter, fy

    @staticmethod
    def get_quarter_dates(quarter: str, fiscal_year: int) -> Tuple[datetime, datetime]:
        """
        Get start and end dates for a fiscal quarter

        Args:
            quarter: Q1, Q2, Q3, or Q4
            fiscal_year: e.g., 2025 for FY2025

        Returns:
            Tuple of (start_date, end_date)
        """
        calendar_year = fiscal_year - 1

        if quarter == "Q1":
            start = datetime(calendar_year, 4, 1)
            end = datetime(calendar_year, 6, 30)
        elif quarter == "Q2":
            start = datetime(calendar_year, 7, 1)
            end = datetime(calendar_year, 9, 30)
        elif quarter == "Q3":
            start = datetime(calendar_year, 10, 1)
            end = datetime(calendar_year, 12, 31)
        elif quarter == "Q4":
            start = datetime(fiscal_year, 1, 1)
            end = datetime(fiscal_year, 3, 31)
        else:
            raise ValueError(f"Invalid quarter: {quarter}")

        return start, end

    @staticmethod
    def get_previous_year_quarter(quarter: str, fiscal_year: int) -> Tuple[str, int]:
        """
        Get the same quarter from previous fiscal year
        For YoY comparison
        """
        return quarter, fiscal_year - 1

    @staticmethod
    def format_quarter_label(quarter: str, fiscal_year: int) -> str:
        """
        Format quarter for display
        e.g., "Q2 FY2025 (Jul-Sep 2024)"
        """
        start_date, end_date = IndianFiscalYear.get_quarter_dates(quarter, fiscal_year)

        months = {
            "Q1": "Apr-Jun",
            "Q2": "Jul-Sep",
            "Q3": "Oct-Dec",
            "Q4": "Jan-Mar"
        }

        return f"{quarter} FY{fiscal_year} ({months[quarter]} {start_date.year})"

    @staticmethod
    def parse_quarter_string(quarter_str: str) -> Tuple[str, int]:
        """
        Parse strings like "Q2FY25" or "Q2 2024-25"

        Returns:
            Tuple of (quarter, fiscal_year)
        """
        import re

        # Pattern 1: Q2FY25
        pattern1 = r"Q(\d)FY(\d{2,4})"
        match1 = re.match(pattern1, quarter_str.upper().replace(" ", ""))
        if match1:
            quarter = f"Q{match1.group(1)}"
            year = int(match1.group(2))
            if year < 100:  # Convert 25 to 2025
                year = 2000 + year
            return quarter, year

        # Pattern 2: Q2 2024-25
        pattern2 = r"Q(\d)\s*(\d{4})-(\d{2,4})"
        match2 = re.match(pattern2, quarter_str.upper())
        if match2:
            quarter = f"Q{match2.group(1)}"
            year = int(match2.group(3))
            if year < 100:
                year = 2000 + year
            return quarter, year

        raise ValueError(f"Cannot parse quarter string: {quarter_str}")


class DataTimestamp:
    """Timestamp tracking for data sources"""

    @staticmethod
    def create_timestamp() -> Dict:
        """
        Create a timestamp with full context
        """
        now = datetime.now()
        quarter, fy = IndianFiscalYear.get_fiscal_quarter(now)

        return {
            "timestamp": now.isoformat(),
            "unix_timestamp": int(now.timestamp()),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "fiscal_quarter": quarter,
            "fiscal_year": fy,
            "calendar_quarter": f"Q{(now.month-1)//3+1}",
            "calendar_year": now.year
        }

    @staticmethod
    def format_age(timestamp: datetime) -> str:
        """
        Format how old the data is
        """
        age = datetime.now() - timestamp

        if age.days > 365:
            return f"{age.days // 365} year(s) old"
        elif age.days > 30:
            return f"{age.days // 30} month(s) old"
        elif age.days > 0:
            return f"{age.days} day(s) old"
        elif age.seconds > 3600:
            return f"{age.seconds // 3600} hour(s) old"
        elif age.seconds > 60:
            return f"{age.seconds // 60} minute(s) old"
        else:
            return "Just now"


# Test utilities
if __name__ == "__main__":
    # Test fiscal year functions
    test_date = datetime(2024, 7, 15)  # July 15, 2024
    print(f"Date: {test_date.strftime('%Y-%m-%d')}")

    fy = IndianFiscalYear.get_fiscal_year(test_date)
    print(f"Fiscal Year: FY{fy}")

    quarter, fy = IndianFiscalYear.get_fiscal_quarter(test_date)
    print(f"Fiscal Quarter: {quarter} FY{fy}")

    label = IndianFiscalYear.format_quarter_label(quarter, fy)
    print(f"Quarter Label: {label}")

    # Test timestamp
    ts = DataTimestamp.create_timestamp()
    print(f"\nCurrent Timestamp:")
    for key, value in ts.items():
        print(f"  {key}: {value}")