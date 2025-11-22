
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, "/Users/srijan/Desktop/aksh")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    print("Testing Master Validation Orchestrator...")
    from agents.master_validation_orchestrator import validate_company
    
    # Test with TCS (532540)
    print("Validating TCS (532540)...")
    result = validate_company("532540", "TCS")
    print(f"Validation Result: {result}")
    
    print("\nTesting ML Data Quality Filter...")
    from agents.ml.ml_data_quality_filter import MLDataQualityFilter
    print("MLDataQualityFilter imported successfully.")
    
    print("\nTesting Data Quality Report Generator...")
    from reports.data_quality_report_generator import DataQualityReportGenerator
    print("DataQualityReportGenerator imported successfully.")
    
    print("\n✅ SYSTEM VERIFICATION SUCCESSFUL")
    
except Exception as e:
    print(f"\n❌ SYSTEM VERIFICATION FAILED: {e}")
    import traceback
    traceback.print_exc()
