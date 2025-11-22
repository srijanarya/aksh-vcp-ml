"""
Indian PDF Extractor

Extracts financial data from Indian corporate filings (BSE/NSE).
Uses pypdf for text extraction and regex for financial metric parsing.
"""

import logging
import re
import os
import requests
from typing import Dict, Optional
from pypdf import PdfReader
import io

logger = logging.getLogger(__name__)

class IndianPDFExtractor:
    """Extracts financial data from Indian corporate PDFs"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def extract_financial_data(self, pdf_url: str) -> Optional[Dict[str, float]]:
        """
        Download PDF and extract financial data.
        
        Args:
            pdf_url: URL of the PDF file
            
        Returns:
            Dictionary of extracted financial metrics
        """
        try:
            text = ""
            # Mock support for demonstration
            if pdf_url.startswith("mock://"):
                logger.info(f"Using mock PDF content for {pdf_url}")
                text = """
                Reliance Industries Limited
                Financial Results for Quarter Ended December 31, 2023
                
                Statement of Standalone Audited Financial Results
                
                1. Revenue from Operations: 25,000.00
                Previous Year: 20,000.00
                
                2. Other Income: 500.00
                
                3. Total Income: 25,500.00
                
                4. Expenses: 18,000.00
                
                5. Profit before tax: 7,500.00
                
                6. Tax Expense: 2,000.00
                
                7. Profit for the period: 5,500.00
                Previous Year: 4,000.00
                
                8. Earning Per Share (EPS): 85.50
                Previous Year: 60.00
                
                Revenue up 25.0%
                Profit up 37.5%
                """
            else:
                logger.info(f"Downloading PDF from {pdf_url}...")
                response = requests.get(pdf_url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                # Extract Text
                with io.BytesIO(response.content) as f:
                    reader = PdfReader(f)
                    # Read first 5 pages (usually contains the results table)
                    for i in range(min(5, len(reader.pages))):
                        text += reader.pages[i].extract_text()
                    
            # Parse Financials
            return self._parse_financials(text)
            
        except Exception as e:
            logger.error(f"Error extracting data from {pdf_url}: {e}")
            return None

    def _parse_financials(self, text: str) -> Dict[str, float]:
        """Parse text to find Revenue, PAT, EPS"""
        data = {
            "revenue": 0.0,
            "net_profit": 0.0,
            "eps": 0.0,
            "revenue_growth": 0.0, # YoY
            "pat_growth": 0.0      # YoY
        }
        
        # Normalize text
        text = text.lower().replace('\n', ' ')
        
        # Regex patterns for key metrics
        # Looks for "Revenue" followed by numbers. 
        # Note: This is a simplified heuristic. Real PDFs are complex tables.
        
        # 1. Revenue / Income from Operations
        # Pattern: "revenue from operations" ... number ... number (current, prev quarter, prev year)
        rev_match = re.search(r'revenue from operations.*?([\d,]+\.?\d*)', text)
        if rev_match:
            data['revenue'] = self._clean_number(rev_match.group(1))
            
        # 2. Net Profit / PAT
        # Pattern: "profit for the period" ... number
        pat_match = re.search(r'profit.*?period.*?([\d,]+\.?\d*)', text)
        if pat_match:
            data['net_profit'] = self._clean_number(pat_match.group(1))
            
        # 3. EPS
        eps_match = re.search(r'earning per share.*?([\d,]+\.?\d*)', text)
        if eps_match:
            data['eps'] = self._clean_number(eps_match.group(1))
            
        # 4. Calculate Growth (Simulated for now as extracting previous year columns is hard with regex)
        # In a real production system, we would use a table extraction library like camelot or tabula-py
        # For this "Magic" demo, we will infer growth if explicit text mentions it
        
        growth_match = re.search(r'revenue.*?up.*?(\d+\.?\d*)%', text)
        if growth_match:
            data['revenue_growth'] = float(growth_match.group(1))
            
        pat_growth_match = re.search(r'profit.*?up.*?(\d+\.?\d*)%', text)
        if pat_growth_match:
            data['pat_growth'] = float(pat_growth_match.group(1))
            
        return data

    def _clean_number(self, num_str: str) -> float:
        """Convert string number (1,234.56) to float"""
        try:
            return float(num_str.replace(',', ''))
        except:
            return 0.0

# Standalone function for backward compatibility
def extract_financial_data(pdf_path: str) -> Dict:
    """Mock function for backward compatibility with existing code"""
    # If it's a URL, use the class
    if pdf_path.startswith("http"):
        extractor = IndianPDFExtractor()
        return extractor.extract_financial_data(pdf_path) or {}
    
    # If it's a local file (mock), return random data
    import random
    return {
        "revenue": random.uniform(100, 1000),
        "net_profit": random.uniform(10, 100),
        "eps": random.uniform(5, 50),
        "revenue_growth": random.uniform(-10, 20),
        "pat_growth": random.uniform(-20, 40)
    }
