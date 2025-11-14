"""
PDF Text Extractor - Extract text and tables from financial PDFs

Extracts quarterly earnings data from BSE corporate filing PDFs:
- Revenue, Net Profit, EPS from financial statements
- YoY/QoQ growth rates
- Key financial ratios

Uses PyPDF2 for text extraction + regex patterns for table parsing.

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Optional dependency - will use if available
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 not available. Install with: pip install PyPDF2")


def extract_text_from_pdf(pdf_path: Path, max_pages: Optional[int] = None) -> str:
    """
    Extract raw text from PDF file.

    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to extract (None = all pages)

    Returns:
        Extracted text as string

    Raises:
        FileNotFoundError: If PDF doesn't exist
        RuntimeError: If PyPDF2 not installed

    Example:
        text = extract_text_from_pdf(Path("/tmp/q1_fy25_results.pdf"), max_pages=5)
        print(f"Extracted {len(text)} characters")
    """
    if not PYPDF2_AVAILABLE:
        raise RuntimeError(
            "PyPDF2 is required for PDF extraction. "
            "Install with: pip install PyPDF2"
        )

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)

            if max_pages:
                pages_to_extract = min(max_pages, total_pages)
            else:
                pages_to_extract = total_pages

            extracted_text = []

            for page_num in range(pages_to_extract):
                page = reader.pages[page_num]
                text = page.extract_text()
                extracted_text.append(text)

            full_text = "\n".join(extracted_text)

            logger.info(
                f"Extracted {len(full_text)} chars from {pages_to_extract} pages: {pdf_path.name}"
            )

            return full_text

    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def extract_financial_tables(
    pdf_text: str,
    company_name: Optional[str] = None
) -> Dict[str, Optional[float]]:
    """
    Extract financial metrics from PDF text using regex patterns.

    Args:
        pdf_text: Raw text extracted from PDF
        company_name: Company name for logging (optional)

    Returns:
        Dictionary with extracted financials:
        {
            "revenue": 1234.5,           # in Crores
            "net_profit": 234.5,         # in Crores
            "eps": 12.5,                 # Rupees
            "revenue_yoy_growth": 15.3,  # Percentage
            "profit_yoy_growth": 18.2,   # Percentage
            "quarter": "Q1",
            "fy_year": "FY25"
        }

    Extraction Strategy:
        1. Look for common table headers (Revenue, Net Profit, EPS)
        2. Extract numbers in Crores/Lakhs (normalize to Crores)
        3. Calculate YoY growth if previous year data present
        4. Handle multiple formats (BSE filings vary significantly)

    Example:
        pdf_text = extract_text_from_pdf(Path("q1_fy25.pdf"))
        financials = extract_financial_tables(pdf_text, company_name="TCS")
        print(f"Revenue: ₹{financials['revenue']} Cr")
    """
    financials = {
        "revenue": None,
        "net_profit": None,
        "eps": None,
        "revenue_yoy_growth": None,
        "profit_yoy_growth": None,
        "quarter": None,
        "fy_year": None
    }

    # Clean text for parsing
    text = pdf_text.replace("\n", " ").replace("\t", " ")
    text = " ".join(text.split())  # Normalize whitespace

    # Pattern 1: Revenue (Total Income / Total Revenue / Income from Operations)
    revenue_patterns = [
        r"(?:Total\s+Income|Total\s+Revenue|Income\s+from\s+Operations).*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:Cr|Crores)",
        r"Revenue.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:Cr|Crores)",
    ]

    for pattern in revenue_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            revenue_str = match.group(1).replace(",", "")
            financials["revenue"] = float(revenue_str)
            logger.debug(f"Extracted revenue: ₹{financials['revenue']} Cr")
            break

    # Pattern 2: Net Profit (PAT / Profit After Tax / Net Profit)
    profit_patterns = [
        r"(?:Net\s+Profit|PAT|Profit\s+After\s+Tax).*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:Cr|Crores)",
        r"Profit.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:Cr|Crores)",
    ]

    for pattern in profit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            profit_str = match.group(1).replace(",", "")
            financials["net_profit"] = float(profit_str)
            logger.debug(f"Extracted net profit: ₹{financials['net_profit']} Cr")
            break

    # Pattern 3: EPS (Earnings Per Share)
    eps_patterns = [
        r"(?:EPS|Earnings\s+Per\s+Share).*?(\d+(?:\.\d+)?)",
        r"Basic\s+EPS.*?(\d+(?:\.\d+)?)",
    ]

    for pattern in eps_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            financials["eps"] = float(match.group(1))
            logger.debug(f"Extracted EPS: ₹{financials['eps']}")
            break

    # Pattern 4: Quarter and FY Year (Q1 FY25, Q2FY24, etc.)
    quarter_pattern = r"(Q[1-4])\s*FY\s*(\d{2})"
    match = re.search(quarter_pattern, text, re.IGNORECASE)
    if match:
        financials["quarter"] = match.group(1).upper()
        fy_year = match.group(2)
        financials["fy_year"] = f"FY{fy_year}"
        logger.debug(f"Extracted period: {financials['quarter']} {financials['fy_year']}")

    # Pattern 5: YoY Growth (if mentioned explicitly)
    growth_pattern = r"(?:growth|increase).*?(\d+(?:\.\d+)?)\s*%"
    matches = re.findall(growth_pattern, text, re.IGNORECASE)
    if len(matches) >= 1:
        # First growth % likely revenue, second likely profit
        financials["revenue_yoy_growth"] = float(matches[0])
        if len(matches) >= 2:
            financials["profit_yoy_growth"] = float(matches[1])

    # Log extraction summary
    extracted_count = sum(1 for v in financials.values() if v is not None)
    logger.info(
        f"Extracted {extracted_count}/7 fields from PDF "
        f"{f'({company_name})' if company_name else ''}"
    )

    return financials


def validate_extracted_financials(
    financials: Dict[str, Optional[float]]
) -> Tuple[bool, List[str]]:
    """
    Validate extracted financial data for completeness and sanity.

    Args:
        financials: Dictionary returned by extract_financial_tables()

    Returns:
        Tuple of (is_valid, errors)

    Validation Rules:
        - Revenue must be positive
        - Net profit should be reasonable relative to revenue (<100%)
        - EPS should be positive for profitable companies
        - Quarter and FY year should be present

    Example:
        financials = extract_financial_tables(pdf_text)
        is_valid, errors = validate_extracted_financials(financials)
        if not is_valid:
            print(f"Validation failed: {errors}")
    """
    errors = []

    # Check completeness
    if financials["revenue"] is None:
        errors.append("Missing revenue")

    if financials["net_profit"] is None:
        errors.append("Missing net profit")

    if financials["eps"] is None:
        errors.append("Missing EPS")

    if financials["quarter"] is None or financials["fy_year"] is None:
        errors.append("Missing quarter/FY year")

    # Sanity checks
    if financials["revenue"] is not None:
        if financials["revenue"] <= 0:
            errors.append(f"Invalid revenue: {financials['revenue']} (must be positive)")

    if financials["net_profit"] is not None and financials["revenue"] is not None:
        profit_margin = (financials["net_profit"] / financials["revenue"]) * 100
        if profit_margin > 100:
            errors.append(
                f"Implausible profit margin: {profit_margin:.1f}% "
                f"(profit > revenue)"
            )

    if financials["eps"] is not None:
        if financials["eps"] < 0 and financials["net_profit"] and financials["net_profit"] > 0:
            errors.append("EPS is negative but net profit is positive")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"Financial validation failed: {errors}")

    return is_valid, errors


def extract_financials_from_pdf_file(
    pdf_path: Path,
    company_name: Optional[str] = None,
    max_pages: int = 10
) -> Optional[Dict]:
    """
    End-to-end extraction: PDF file -> validated financials.

    Args:
        pdf_path: Path to PDF file
        company_name: Company name (optional, for logging)
        max_pages: Maximum pages to extract (default: 10)

    Returns:
        Dictionary with extracted financials, or None if extraction/validation failed

    Example:
        financials = extract_financials_from_pdf_file(
            Path("/tmp/tcs_q1_fy25.pdf"),
            company_name="TCS"
        )

        if financials:
            print(f"Revenue: ₹{financials['revenue']} Cr")
            print(f"EPS: ₹{financials['eps']}")
        else:
            print("Extraction failed")
    """
    try:
        # Step 1: Extract text
        pdf_text = extract_text_from_pdf(pdf_path, max_pages=max_pages)

        if not pdf_text:
            logger.error(f"No text extracted from {pdf_path}")
            return None

        # Step 2: Parse financials
        financials = extract_financial_tables(pdf_text, company_name=company_name)

        # Step 3: Validate
        is_valid, errors = validate_extracted_financials(financials)

        if not is_valid:
            logger.warning(
                f"Extracted data validation failed for {pdf_path.name}: {errors}"
            )
            # Return anyway with validation warnings (partial data is useful)

        financials["pdf_path"] = str(pdf_path)
        financials["company_name"] = company_name
        financials["extraction_errors"] = errors if not is_valid else []

        return financials

    except Exception as e:
        logger.error(f"Failed to extract financials from {pdf_path}: {e}")
        return None


if __name__ == "__main__":
    # Demo: PDF extraction (requires sample PDF)
    logging.basicConfig(level=logging.INFO)

    print("=== PDF Text Extractor Demo ===\n")

    if not PYPDF2_AVAILABLE:
        print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")
        print("Demo cannot run without PyPDF2.")
    else:
        print("✅ PyPDF2 is available\n")

        # Simulated PDF text (what would be extracted from a real PDF)
        sample_pdf_text = """
        TCS LIMITED
        Quarterly Results for Q1 FY25

        Financial Highlights:
        Total Income: 1,234.5 Crores
        Net Profit (PAT): 234.5 Crores
        Earnings Per Share (EPS): 12.50

        The company reported a growth of 15.3% in revenue and 18.2% growth in profit.
        """

        print("Sample PDF text (simulated):")
        print(sample_pdf_text)
        print("\nExtracting financials...")

        financials = extract_financial_tables(sample_pdf_text, company_name="TCS")

        print("\nExtracted data:")
        for key, value in financials.items():
            if value is not None:
                print(f"  {key}: {value}")

        print("\nValidating extraction...")
        is_valid, errors = validate_extracted_financials(financials)
        print(f"Valid: {is_valid}")
        if errors:
            print(f"Errors: {errors}")
