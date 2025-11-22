from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.ml.realtime_earnings_agent import RealtimeEarningsAgent
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class EarningsAlert(BaseModel):
    bse_code: str
    pdf_url: str
    subject: str

@router.post("/analyze-earnings")
async def analyze_earnings(alert: EarningsAlert):
    """
    Analyze an earnings alert PDF for blockbuster results.
    """
    try:
        agent = RealtimeEarningsAgent()
        result = await agent.process_alert(alert.dict())
        
        if not result:
            return {"status": "no_data", "message": "Could not extract data"}
            
        return {
            "status": "success",
            "data": result,
            "is_blockbuster": result.get("is_blockbuster", False)
        }
    except Exception as e:
        logger.error(f"Error analyzing earnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
