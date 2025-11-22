from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
from pydantic import BaseModel
from agents.intelligent_earnings_collector import IntelligentEarningsCollector, DataGap

router = APIRouter(prefix="/api/intelligent-collector", tags=["Intelligent Collector"])

class CollectRequest(BaseModel):
    max_companies: int = 5
    priority_filter: str = "high"

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "intelligent-earnings-collector"}

@router.get("/gaps")
async def get_gaps():
    collector = IntelligentEarningsCollector()
    gaps = collector.identify_data_gaps()
    return {
        "total_gaps": len(gaps),
        "gaps": [
            {
                "company_name": g.company_name,
                "code": g.code,
                "priority": g.priority,
                "missing_quarters": g.missing_quarters
            } for g in gaps
        ]
    }

@router.post("/collect")
async def collect_data(request: CollectRequest):
    collector = IntelligentEarningsCollector(enable_web_search=True, enable_ai_inference=True)
    stats = await collector.collect_missing_data(
        max_companies=request.max_companies,
        priority_filter=request.priority_filter
    )
    return stats

@router.post("/collect/quick")
async def collect_quick():
    collector = IntelligentEarningsCollector(enable_web_search=False, enable_ai_inference=False)
    stats = await collector.collect_missing_data(max_companies=5, priority_filter="high")
    return stats
