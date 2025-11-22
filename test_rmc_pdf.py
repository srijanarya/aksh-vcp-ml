#!/usr/bin/env python3
"""
Test extraction on RMC Switchgears Order Win PDF
"""

from src.intelligence.intelligence_extractor import IntelligenceExtractor
import logging

logging.basicConfig(level=logging.INFO)

extractor = IntelligenceExtractor()

# Test the specific PDF
pdf_path = "data/cache/pdfs/6ee2e0ce-e9ab-498e-9191-61b786eb57c0.pdf"

# Get text
text = extractor._get_pdf_text(pdf_path)

print("=" * 80)
print("EXTRACTED TEXT FROM RMC SWITCHGEARS PDF:")
print("=" * 80)
print(text[:2000])  # First 2000 chars
print("\n" + "=" * 80)
print("PARSED DATA:")
print("=" * 80)

data = extractor._extract_order_details(text)
print(data)
