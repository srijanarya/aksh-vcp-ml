#!/usr/bin/env python3
"""
Test Data Verification System
Demonstrates the complete data accuracy and validation pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.fiscal_year_utils import IndianFiscalYear, DataTimestamp
from data_sources.data_accuracy_validator import DataAccuracyValidator
from datetime import datetime

def test_fiscal_year_utils():
    """Test fiscal year utilities"""
    print("\n" + "="*60)
    print("TESTING FISCAL YEAR UTILITIES")
    print("="*60)

    test_dates = [
        datetime(2024, 4, 15),   # Q1 FY2025
        datetime(2024, 7, 15),   # Q2 FY2025
        datetime(2024, 10, 15),  # Q3 FY2025
        datetime(2025, 1, 15),   # Q4 FY2025
    ]

    for date in test_dates:
        fy = IndianFiscalYear.get_fiscal_year(date)
        quarter, fy = IndianFiscalYear.get_fiscal_quarter(date)
        label = IndianFiscalYear.format_quarter_label(quarter, fy)

        print(f"\nDate: {date.strftime('%Y-%m-%d')}")
        print(f"  Fiscal Year: FY{fy}")
        print(f"  Quarter: {quarter}")
        print(f"  Label: {label}")

    # Test timestamp
    ts = DataTimestamp.create_timestamp()
    print(f"\nCurrent Timestamp:")
    print(f"  Date/Time: {ts['timestamp']}")
    print(f"  Fiscal: {ts['fiscal_quarter']} FY{ts['fiscal_year']}")
    print(f"  Calendar: {ts['calendar_quarter']} {ts['calendar_year']}")

def test_data_validation():
    """Test data validation with real companies"""
    print("\n" + "="*60)
    print("TESTING DATA VALIDATION SYSTEM")
    print("="*60)

    validator = DataAccuracyValidator()

    # Test companies
    test_companies = [
        ("532540", "TCS", "Tata Consultancy Services"),
        ("500325", "RELIANCE", "Reliance Industries"),
        ("506401", "DEEPAKNTR", "Deepak Nitrite"),
    ]

    for bse_code, nse_symbol, name in test_companies:
        print(f"\n{'='*40}")
        print(f"Validating: {name}")
        print(f"BSE: {bse_code} | NSE: {nse_symbol}")
        print('='*40)

        # Validate data
        report = validator.validate_company_data(bse_code, nse_symbol)

        # Display results
        print(f"\n📊 DATA QUALITY REPORT")
        print(f"  Overall Confidence: {report['overall_confidence']:.1f}%")
        print(f"  Data Quality: {report['data_quality']}")
        print(f"  Sources Found: {list(report['data_sources'].keys())}")

        print(f"\n📈 VALIDATION RESULTS:")
        for validation in report['validation_results']:
            print(f"\n  {validation.metric}:")

            # Show source values
            if validation.sources:
                print(f"    Source Values:")
                for source, value in validation.sources.items():
                    if value is not None:
                        print(f"      {source}: {value:.2f}")

            print(f"    Discrepancy: {validation.discrepancy_pct:.1f}%")
            print(f"    Confidence: {validation.confidence_score:.1f}%")

            if validation.recommended_value is not None:
                print(f"    ✅ Recommended: {validation.recommended_value:.2f}")
            else:
                print(f"    ❌ No reliable value")

            print(f"    Reason: {validation.reason}")

        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")

def demonstrate_complete_flow():
    """Demonstrate the complete verification flow"""
    print("\n" + "="*60)
    print("COMPLETE DATA VERIFICATION DEMONSTRATION")
    print("="*60)

    print("""
This system provides:

1. **Multiple Data Sources**:
   - BSE Direct API
   - NSE Direct API
   - Yahoo Finance
   - Screener.in

2. **Data Validation**:
   - Cross-source comparison
   - Discrepancy detection
   - Confidence scoring
   - Sanity checks (e.g., revenue can't drop 790%)

3. **Fiscal Year Handling**:
   - Indian FY (Apr-Mar) vs Calendar Year
   - Quarter mapping (Q2 FY2025 = Jul-Sep 2024)
   - YoY and QoQ calculations

4. **Timestamp Tracking**:
   - Every data point timestamped
   - Shows data age
   - Identifies stale data

5. **Market Dashboard**:
   - Real-time market status
   - Sector performance
   - Data quality indicators
   - Investment recommendations
    """)

if __name__ == "__main__":
    print("\n" + "🔍 DATA VERIFICATION SYSTEM TEST" + "\n")

    # Test fiscal year utilities
    test_fiscal_year_utils()

    # Test data validation
    print("\n⏳ Testing data validation (this may take a moment)...")
    test_data_validation()

    # Show complete flow
    demonstrate_complete_flow()

    print("\n" + "="*60)
    print("✅ Data Verification System Test Complete!")
    print("="*60)
    print("""
Next Steps:
1. Run 'python market_status_dashboard.py' for full market analysis
2. Integrate with your ML pipeline for quality filtering
3. Use confidence scores to weight trading signals
4. Monitor data quality trends over time
    """)