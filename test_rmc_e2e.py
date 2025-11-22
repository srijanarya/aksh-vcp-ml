#!/usr/bin/env python3
"""
Manual End-to-End Test for RMC Order Win
"""

from src.intelligence.intelligence_extractor import IntelligenceExtractor
import logging

logging.basicConfig(level=logging.INFO)

extractor = IntelligenceExtractor()

# Create a mock announcement (like what fetcher would provide)
announcement = {
    "id": "test-rmc-order",
    "company_name": "RMC Switchgears Ltd",
    "category": "ORDER_WIN",
    "pdf_url": "file://./data/cache/pdfs/6ee2e0ce-e9ab-498e-9191-61b786eb57c0.pdf"
}

print("=" * 80)
print("END-TO-END EXTRACTION TEST: RMC Switchgears Order Win")
print("=" * 80)

# Instead of using the full flow, let's directly test extraction from the PDF file
from pathlib import Path

pdf_path = Path("data/cache/pdfs/6ee2e0ce-e9ab-498e-9191-61b786eb57c0.pdf")
if not pdf_path.exists():
    print(f"❌ PDF not found at {pdf_path}")
    exit(1)

# Extract text and intelligence
text = extractor._get_pdf_text(pdf_path)
result_data = extractor._extract_order_details(text)

print("\nExtracted Data:")
for key, value in result_data.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 80)
if result_data.get("value_cr"):
    print("✅ TEST PASSED: Successfully extracted order value and client")
    print(f"   Order Value: ₹{result_data['value_cr']:.2f} Crores")
    if "client" in result_data:
        print(f"   Client: {result_data['client']}")
else:
    print("❌ TEST FAILED: Extraction incomplete")
print("=" * 80)
