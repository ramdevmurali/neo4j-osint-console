import asyncio
import logging
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from src.agent import run_agent
from src.config import Config
from src.services.insight import (
    build_profile_prompt,
    run_company_insight,
    run_competitor_flow,
)
from src.services.mood import get_company_mood

logger = logging.getLogger("agents")
router = APIRouter()

def _require_company(company: str | None) -> str:
    if not company:
        raise HTTPException(status_code=400, detail="company is required")
    return company


class MissionRequest(BaseModel):
    task: str
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class CompanyRequest(BaseModel):
    company: str
    thread_id: str | None = None


class MoodRequest(BaseModel):
    company: str
    timeframe: str | None = "90d"


@router.post("/run-mission")
async def run_mission(req: MissionRequest):
    logger.info(f"Task: {req.task} | Thread: {req.thread_id}")
    try:
        content = await asyncio.wait_for(
            run_in_threadpool(run_agent, req.task, req.thread_id),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        return {"result": content, "thread_id": req.thread_id, "status": "success"}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Mission timed out")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/profile-company")
async def profile_company(req: CompanyRequest):
    company = _require_company(req.company)
    task = build_profile_prompt(company)

    try:
        content = await asyncio.wait_for(
            run_in_threadpool(run_agent, task, req.thread_id or str(uuid.uuid4())),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        return {"result": content, "status": "success"}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Profiler timed out")
    except Exception as e:
        logger.error(f"Profiler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/competitors")
async def competitor_scout(req: CompanyRequest):
    company = _require_company(req.company)

    try:
        result, competitors = await run_competitor_flow(company, req.thread_id)
        return {"result": result, "status": "success", "competitors": competitors}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Competitor scout timed out")
    except Exception as e:
        logger.error(f"Competitor scout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/company-insight")
async def company_insight(req: CompanyRequest):
    """
    One-shot company insight: profile + competitors, then return current graph view.
    """
    company = _require_company(req.company)

    try:
        data = await run_company_insight(company, req.thread_id)
        return {"status": "success", **data}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Company insight timed out")
    except Exception as e:
        logger.error(f"Company insight error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/company-mood")
async def company_mood(req: MoodRequest):
    company = _require_company(req.company)
    timeframe = req.timeframe or "90d"

    try:
        data = await asyncio.wait_for(
            run_in_threadpool(get_company_mood, company, timeframe),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        return {"status": "success", **data}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Company mood timed out")
    except Exception as e:
        logger.error(f"Company mood error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
