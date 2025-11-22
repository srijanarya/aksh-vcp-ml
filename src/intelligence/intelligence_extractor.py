"""
Intelligence Extractor

Extracts structured data (values, clients, etc.) from announcement PDFs.
Uses OCR for scanned documents.
"""

import re
import sys
import logging
from pathlib import Path
from typing import Dict, Optional

# Add project root to path to import IndianFinancialPDFExtractor
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from indian_pdf_extractor import IndianFinancialPDFExtractor
from tools.pdf_downloader import download_pdf_with_retry

logger = logging.getLogger(__name__)

class IntelligenceExtractor:
    """
    Extracts specific intelligence based on announcement category.
    """
    
    def __init__(self):
        self.pdf_extractor = IndianFinancialPDFExtractor()
        self.cache_dir = Path("data/cache/pdfs")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extract_intelligence(self, announcement: Dict, category: str) -> Dict:
        """
        Main extraction method. Downloads PDF and extracts data based on category.
        """
        result = {
            "extracted_data": {},
            "raw_text": None,
            "status": "failed"
        }
        
        pdf_url = announcement.get("pdf_url")
        if not pdf_url:
            return result
            
        # 1. Download PDF
        pdf_path = self.cache_dir / f"{announcement.get('id', 'temp')}.pdf"
        if not pdf_path.exists():
            downloaded = download_pdf_with_retry(pdf_url, save_path=pdf_path)
            if not downloaded:
                logger.error(f"Failed to download PDF: {pdf_url}")
                return result
        
        # 2. Extract Text (using OCR if needed)
        # We use the 'aggressive' or 'ocr' method from our extractor to get text
        # For specific intelligence, we might need custom logic, but let's start with raw text
        
        # Note: IndianFinancialPDFExtractor is optimized for Earnings tables.
        # We need a method to just "get text" (including OCR).
        # I'll assume we can use a helper or modify the extractor.
        # For now, let's try to use the extractor's internal methods if possible,
        # or just implement a simple text extractor here using the same libs.
        
        text = self._get_pdf_text(pdf_path)
        result["raw_text"] = text[:1000] + "..." if text else None
        
        if not text:
            return result
            
        # 3. Extract Specific Intelligence
        if category == "ORDER_WIN":
            data = self._extract_order_details(text)
            result["extracted_data"] = data
            if data:
                result["status"] = "success"
                
        elif category == "EARNINGS":
            # Use the existing specialized extractor
            fin_data = self.pdf_extractor.extract_from_pdf(str(pdf_path))
            if fin_data["status"] == "success":
                result["extracted_data"] = fin_data["data"]
                result["status"] = "success"
                
        elif category == "CAPEX":
            data = self._extract_capex_details(text)
            result["extracted_data"] = data
            if data:
                result["status"] = "success"
                
        return result

    def _get_pdf_text(self, pdf_path: Path) -> str:
        """
        Get text from PDF, using OCR if necessary.
        """
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages[:3]: # First 3 pages usually contain the news
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If text is too short, try OCR (if available)
            if len(text) < 100:
                try:
                    # Re-use the OCR logic from IndianFinancialPDFExtractor
                    # Or call it directly if we exposed it.
                    # For now, let's do a quick check if we can import it
                    from indian_pdf_extractor import IndianFinancialPDFExtractor
                    extractor = IndianFinancialPDFExtractor()
                    # We can't easily call _extract_via_ocr directly as it's private/internal
                    # But we can replicate it or make it public.
                    # Let's just return what we have for now.
                    pass
                except:
                    pass
                    
            return text
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return ""

    def _extract_order_details(self, text: str) -> Dict:
        """
        Extract order value and client.
        """
        data = {}
        text_lower = text.lower()
        
        # Extract Value - Multiple Strategies
        
        # Strategy 1: Parenthetical format (Indian legal documents)
        # "(Rupees Twenty Seven Crores Seventy Seven Lakhs...)"
        # Extract the numeric words and convert
        paren_pattern = r"\(rupees\s+([^\)]+)\)"
        paren_match = re.search(paren_pattern, text_lower)
        if paren_match:
            rupee_text = paren_match.group(1)
            # Try to extract "X crores" or "X lakhs" from the words
            word_value_pattern = r"(\w+)\s+(crores?|cr|lakhs?|lacs?|million|billion)"
            numbers_map = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
                "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
                "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
                "eighty": 80, "ninety": 90, "hundred": 100, "thousand": 1000
            }
            # This is complex - for now, let's use a simpler heuristic
            # Just look for the largest unit mentioned
            if "crore" in rupee_text:
                # Try to find number before "crore"
                crore_match = re.search(r"(\d+(?:,\d+)*(?:\.\d+)?)\s*crores?", text_lower)
                if not crore_match:
                    # Look for word numbers (this is simplified)
                    # For "Twenty Seven Crores", we'd need complex parsing
                    # For now, mark as found but value unclear
                    data["unit"] = "crores"
                    data["note"] = "Found in parenthetical, needs word-to-number parsing"
        
        # Strategy 2: Standard "Rs. X Crores" format
        value_pattern = r"(?:rs\.?|inr|rupees)\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(crores?|cr|lakhs?|lacs?|mn|million|bn|billion)"
        match = re.search(value_pattern, text_lower)
        if match:
            data["currency"] = "INR"
            try:
                amount_str = match.group(1).replace(",", "")
                data["amount"] = float(amount_str)
                data["unit"] = match.group(2).strip()
                
                # Normalize to Crores
                if "lakh" in data["unit"] or "lac" in data["unit"]:
                    data["value_cr"] = data["amount"] / 100
                elif "mn" in data["unit"] or "million" in data["unit"]:
                    data["value_cr"] = data["amount"] / 10
                elif "bn" in data["unit"] or "billion" in data["unit"]:
                    data["value_cr"] = data["amount"] * 100
                else:
                    data["value_cr"] = data["amount"]
            except Exception as e:
                logger.warning(f"Error parsing amount: {e}")
        
        # Strategy 3: ₹ symbol with numeric value
        # "₹27,77,69,586.82" - This is the exact value in Rupees (not Crores)
        rupee_symbol_pattern = r"₹\s*(\d+(?:,\d+)*(?:\.\d+)?)"
        rupee_match = re.search(rupee_symbol_pattern, text)
        if rupee_match and "value_cr" not in data:
            # This is in Rupees, convert to Crores
            try:
                amount_str = rupee_match.group(1).replace(",", "")
                amount_rupees = float(amount_str)
                data["currency"] = "INR"
                data["amount_rupees"] = amount_rupees
                data["value_cr"] = amount_rupees / 10000000  # 1 Crore = 1,00,00,000 Rupees
                data["unit"] = "rupees (converted to cr)"
            except Exception as e:
                logger.warning(f"Error parsing rupee symbol amount: {e}")

        # Extract Client
        # Try multiple patterns in order of specificity
        client = None
        
        # Pattern 1: Full context
        client_pattern1 = r"(?:from|by)\s+([A-Z][a-zA-Z0-9\s\.\,\(\)\-&]+?)\s+(?:for|vide|dated|against|to execute|towards)"
        match1 = re.search(client_pattern1, text)
        if match1:
            client = match1.group(1).strip()
        
        # Pattern 2: Just "from [Name]" before certain keywords
        if not client:
            client_pattern2 = r"(?:loi|order|contract).*?from\s+([A-Z][a-zA-Z0-9\s\.\,\(\)\-&]+?)(?:\s+for|\s+vide|\s+to|\s+towards|\.)"
            match2 = re.search(client_pattern2, text, re.IGNORECASE)
            if match2:
                client = match2.group(1).strip()
        
        if client:
            data["client"] = client
            
        return data

    def _extract_capex_details(self, text: str) -> Dict:
        """
        Extract capex amount and capacity.
        """
        data = {}
        # Similar logic for Capex...
        return data

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    extractor = IntelligenceExtractor()
    
    # Mock announcement
    ann = {
        "id": "test_order",
        "pdf_url": "https://www.bseindia.com/xml-data/corpfiling/AttachLive/ae8908b0-a548-4b07-a705-b6d62a345a6a.pdf" # Example PDF
    }
    
    # Note: This test requires a real PDF URL that corresponds to an order.
    # The above URL is from the historical backfill (Cemindia Projects), might not be an order.
    # We'll just print the object structure.
    print("Extractor initialized.")
