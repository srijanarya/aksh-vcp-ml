"""
Run Data Collection Pipeline

This script executes the full data collection pipeline using the MLDataCollectorAgent.
It orchestrates:
1. Labeling upper circuits
2. Mapping BSE-NSE symbols
3. Extracting financials
4. Collecting price movements

Usage:
    python run_data_collection.py
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.ml.ml_master_orchestrator import MLMasterOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing ML Master Orchestrator...")
    orchestrator = MLMasterOrchestrator()
    
    # Define scope - Extended to 3 years with 50+ companies
    # Mix of large caps (stable) and mid caps (more volatile = more circuits)
    bse_codes = [
        # Large Caps (Top 10)
        "500325",  # Reliance Industries
        "532540",  # TCS
        "500209",  # Infosys
        "500180",  # HDFC Bank
        "532174",  # ICICI Bank
        "500112",  # State Bank of India
        "500510",  # Larsen & Toubro
        "532555",  # NTPC
        "500696",  # Hindustan Unilever
        "532215",  # Axis Bank
        
        # Large Caps (11-20)
        "500820",  # Asian Paints
        "532281",  # HCL Technologies
        "500034",  # Bajaj Finance
        "532898",  # PowerGrid
        "500010",  # HDFC Ltd
        "532454",  # Bharti Airtel
        "532187",  # IndusInd Bank
        "532712",  # Kotak Mahindra Bank
        "500875",  # ITC
        "532755",  # Tech Mahindra
        
        # Mid Caps (More volatile, better for circuits)
        "532977",  # Bajaj Finserv
        "532648",  # Yes Bank
        "500257",  # Lupin
        "532220",  # Federal Bank
        "532461",  # Adani Ports
        "532540",  # Wipro
        "500295",  # Dabur India
        "532432",  # Bandhan Bank
        "532488",  # Piramal Enterprises
        "500440",  # Hindalco
        
        # Mid Caps (High Growth)
        "543066",  # Adani Power
        "532921",  # Adani Enterprises
        "500400",  # Tata Steel
        "532286",  # IDFC First Bank
        "532890",  # PNB
        "532650",  # Bank of Baroda
        "500570",  # Tata Motors
        "532977",  # Bajaj Auto
        "532483",  # Canara Bank
        "500900",  # UPL Ltd
        
        # Small-Mid Caps (Most volatile)
        "532394",  # RBL Bank
        "532795",  # Escorts
        "532868",  # GNFC
        "500003",  # Aegis Logistics
        "500124",  # Bank of India
        "532798",  # JK Cement
        "500470",  # Tata Consumer
        "532488",  # PI Industries
        "532947",  # Amber Enterprises
        "532281",  # Trident
    ]
    
    # Extended date range: 3 years of data
    start_date = "2022-01-01"  # 3 years back
    end_date = "2024-11-19"     # Current date
    
    logger.info(f"Starting data collection for {len(bse_codes)} companies...")
    logger.info(f"Date Range: {start_date} to {end_date}")
    
    try:
        report = orchestrator.orchestrate_historical_data_collection(
            bse_codes=bse_codes,
            start_date=start_date,
            end_date=end_date
        )
        
        print("\n" + "="*50)
        print("DATA COLLECTION REPORT")
        print("="*50)
        print(f"Run ID: {report.run_id}")
        print(f"Success Rate: {report.success_rate:.1%}")
        print(f"Tasks Completed: {report.tasks_completed}/{report.tasks_total}")
        print(f"Duration: {report.duration_seconds:.1f}s")
        print("-" * 50)
        
        for task in report.task_results:
            status_icon = "✅" if task.status == "SUCCESS" else "❌"
            print(f"{status_icon} {task.task_name}: {task.status}")
            if task.error_message:
                print(f"   Error: {task.error_message}")
                
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
