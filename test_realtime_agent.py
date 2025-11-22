import logging
from agents.ml.realtime_earnings_agent import RealtimeEarningsAgent

# Configure logging
logging.basicConfig(level=logging.INFO)

import asyncio

async def run_test_async():
    agent = RealtimeEarningsAgent()
    
    # Sample Alert (Reliance Industries - Blockbuster)
    pdf_url = "mock://reliance_q3.pdf" # Example URL
    
    alert = {
        'bse_code': '500325',
        'pdf_url': pdf_url,
        'subject': 'Financial Results for Q3 FY24'
    }
    
    print(f"Processing alert for {alert['bse_code']}...")
    result = await agent.process_alert(alert)
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(run_test_async())
