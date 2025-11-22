"""
Fiscal Year Utilities for Indian Markets

Handles Indian fiscal year (Apr 1 - Mar 31) conversions and quarter comparisons.
"""

from datetime import datetime, date
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def get_fiscal_quarter(dt: datetime) -> Tuple[str, str]:
    """
    Convert calendar date to Indian fiscal quarter.
    
    Indian FY runs from Apr 1 to Mar 31.
    - Q1: Apr-Jun
    - Q2: Jul-Sep
    - Q3: Oct-Dec
    - Q4: Jan-Mar
    
    Args:
        dt: Calendar date
        
    Returns:
        Tuple of (quarter, fiscal_year)
        Example: (datetime(2024, 10, 15)) -> ("Q2", "FY25")
    
    Examples:
        >>> get_fiscal_quarter(datetime(2024, 10, 15))
        ('Q2', 'FY25')
        >>> get_fiscal_quarter(datetime(2025, 2, 1))
        ('Q4', 'FY25')
        >>> get_fiscal_quarter(datetime(2024, 5, 1))
        ('Q1', 'FY25')
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('/', '-'))
    
    month = dt.month
    year = dt.year
    
    # Determine quarter
    if 4 <= month <= 6:
        quarter = "Q1"
        fy_year = year + 1  # Apr 2024 is FY25
    elif 7 <= month <= 9:
        quarter = "Q2"
        fy_year = year + 1
    elif 10 <= month <= 12:
        quarter = "Q3"
        fy_year = year + 1
    else:  # 1 <= month <= 3
        quarter = "Q4"
        fy_year = year  # Jan 2025 is still FY25
    
    # Format as "FY25" (last 2 digits)
    fy_str = f"FY{str(fy_year)[-2:]}"
    
    return quarter, fy_str


def get_fiscal_year(dt: datetime) -> str:
    """
    Get fiscal year for a given date.
    
    Args:
        dt: Calendar date
        
    Returns:
        Fiscal year string (e.g., "FY25")
        
    Examples:
        >>> get_fiscal_year(datetime(2024, 10, 15))
        'FY25'
        >>> get_fiscal_year(datetime(2024, 2, 1))
        'FY24'
    """
    _, fy = get_fiscal_quarter(dt)
    return fy


def parse_fiscal_year(fy_str: str) -> int:
    """
    Parse fiscal year string to full year.
    
    Args:
        fy_str: Fiscal year string like "FY25" or "2025"
        
    Returns:
        Full year as integer (e.g., 2025)
        
    Examples:
        >>> parse_fiscal_year("FY25")
        2025
        >>> parse_fiscal_year("FY2025")
        2025
        >>> parse_fiscal_year("25")
        2025
    """
    fy_str = fy_str.upper().replace("FY", "").strip()
    
    # Handle 2-digit year
    if len(fy_str) == 2:
        year = int(fy_str)
        # Assume 20xx for years < 50, 19xx for years >= 50
        if year < 50:
            return 2000 + year
        else:
            return 1900 + year
    
    # Handle 4-digit year
    return int(fy_str)


def compare_quarters_yoy(q1: str, fy1: str, q2: str, fy2: str) -> bool:
    """
    Check if two quarters are exactly 1 year apart (Year-over-Year comparison).
    
    Args:
        q1: First quarter (e.g., "Q2")
        q2: Second quarter (e.g., "Q2")
        fy1: First fiscal year (e.g., "FY25")
        fy2: Second fiscal year (e.g., "FY24")
        
    Returns:
        True if quarters are 1 year apart and same quarter
        
    Examples:
        >>> compare_quarters_yoy("Q2", "FY25", "Q2", "FY24")
        True
        >>> compare_quarters_yoy("Q2", "FY25", "Q3", "FY24")
        False
        >>> compare_quarters_yoy("Q2", "FY25", "Q2", "FY23")
        False
    """
    # Quarters must match
    if q1 != q2:
        return False
    
    # Years must be exactly 1 apart
    year1 = parse_fiscal_year(fy1)
    year2 = parse_fiscal_year(fy2)
    
    return abs(year1 - year2) == 1


def compare_quarters_qoq(q1: str, fy1: str, q2: str, fy2: str) -> bool:
    """
    Check if two quarters are consecutive (Quarter-over-Quarter comparison).
    
    Args:
        q1: First quarter (e.g., "Q2")
        q2: Second quarter (e.g., "Q1")
        fy1: First fiscal year (e.g., "FY25")
        fy2: Second fiscal year (e.g., "FY25" or "FY24")
        
    Returns:
        True if quarters are consecutive
        
    Examples:
        >>> compare_quarters_qoq("Q2", "FY25", "Q1", "FY25")
        True
        >>> compare_quarters_qoq("Q1", "FY25", "Q4", "FY24")
        True
        >>> compare_quarters_qoq("Q4", "FY25", "Q1", "FY26")
        True
    """
    year1 = parse_fiscal_year(fy1)
    year2 = parse_fiscal_year(fy2)
    
    q1_num = int(q1.replace("Q", ""))
    q2_num = int(q2.replace("Q", ""))
    
    # Same fiscal year
    if year1 == year2:
        return q1_num == q2_num + 1
    
    # Cross fiscal year (Q1 FY25 follows Q4 FY24)
    if year1 == year2 + 1:
        return q1_num == 1 and q2_num == 4
    
    return False


def get_quarter_date_range(quarter: str, fiscal_year: str) -> Tuple[date, date]:
    """
    Get start and end dates for a fiscal quarter.
    
    Args:
        quarter: Quarter string (e.g., "Q2")
        fiscal_year: Fiscal year (e.g., "FY25")
        
    Returns:
        Tuple of (start_date, end_date)
        
    Examples:
        >>> get_quarter_date_range("Q2", "FY25")
        (date(2024, 7, 1), date(2024, 9, 30))
        >>> get_quarter_date_range("Q4", "FY25")
        (date(2025, 1, 1), date(2025, 3, 31))
    """
    fy = parse_fiscal_year(fiscal_year)
    q_num = int(quarter.replace("Q", ""))
    
    # Calculate calendar year for quarter start
    # FY25 starts in Apr 2024
    # Q1 (Apr-Jun): 2024
    # Q2 (Jul-Sep): 2024
    # Q3 (Oct-Dec): 2024
    # Q4 (Jan-Mar): 2025
    
    if q_num <= 3:
        year = fy - 1
    else:  # Q4
        year = fy
    
    # Define quarter months
    quarter_months = {
        1: (4, 6),   # Apr-Jun
        2: (7, 9),   # Jul-Sep
        3: (10, 12), # Oct-Dec
        4: (1, 3)    # Jan-Mar
    }
    
    start_month, end_month = quarter_months[q_num]
    
    start_date = date(year, start_month, 1)
    
    # End date is last day of end_month
    if end_month in [4, 6, 9, 11]:
        end_day = 30
    elif end_month == 2:
        # Check for leap year
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            end_day = 29
        else:
            end_day = 28
    else:
        end_day = 31
    
    end_date = date(year, end_month, end_day)
    
    return start_date, end_date


def format_quarter_display(quarter: str, fiscal_year: str) -> str:
    """
    Format quarter and fiscal year for display.
    
    Args:
        quarter: Quarter (e.g., "Q2")
        fiscal_year: Fiscal year (e.g., "FY25")
        
    Returns:
        Formatted string (e.g., "Q2 FY25 (Jul-Sep 2024)")
        
    Examples:
        >>> format_quarter_display("Q2", "FY25")
        'Q2 FY25 (Jul-Sep 2024)'
    """
    start_date, end_date = get_quarter_date_range(quarter, fiscal_year)
    
    month_abbrev = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    
    start_month = month_abbrev[start_date.month]
    end_month = month_abbrev[end_date.month]
    
    return f"{quarter} {fiscal_year} ({start_month}-{end_month} {end_date.year})"


if __name__ == "__main__":
    # Test cases
    import doctest
    doctest.testmod()
    
    # Manual tests
    print("\n=== Fiscal Year Utilities Tests ===\n")
    
    test_date = datetime(2024, 10, 15)
    q, fy = get_fiscal_quarter(test_date)
    print(f"Date: {test_date.date()}")
    print(f"Quarter: {q}, FY: {fy}")
    print(f"Display: {format_quarter_display(q, fy)}\n")
    
    # Test YoY comparison
    print("YoY Comparison Tests:")
    print(f"Q2 FY25 vs Q2 FY24: {compare_quarters_yoy('Q2', 'FY25', 'Q2', 'FY24')}")  # True
    print(f"Q2 FY25 vs Q3 FY24: {compare_quarters_yoy('Q2', 'FY25', 'Q3', 'FY24')}")  # False
    print()
    
    # Test QoQ comparison
    print("QoQ Comparison Tests:")
    print(f"Q2 FY25 vs Q1 FY25: {compare_quarters_qoq('Q2', 'FY25', 'Q1', 'FY25')}")  # True
    print(f"Q1 FY25 vs Q4 FY24: {compare_quarters_qoq('Q1', 'FY25', 'Q4', 'FY24')}")  # True
    print(f"Q2 FY25 vs Q3 FY24: {compare_quarters_qoq('Q2', 'FY25', 'Q3', 'FY24')}")  # False
