import asyncio
import logging
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from src.agent import run_agent
from src.config import Config
from src.services.insight import (
    build_competitor_prompt,
    build_competitor_fallback_prompt,
    build_profile_prompt,
    filter_competitors,
    run_company_insight,
)
from src.routes.graph import get_competitors, entity_profile  # reuse for response enrichment

logger = logging.getLogger("agents")
router = APIRouter()

def _normalize_company(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum() or ch.isspace()).strip()


class MissionRequest(BaseModel):
    task: str
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class CompanyRequest(BaseModel):
    company: str
    thread_id: str | None = None


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
    if not req.company:
        raise HTTPException(status_code=400, detail="company is required")

    task = (
        f"Profile the company '{req.company}'. "
        "Return canonical name, HQ/country, founded year, and 3 key executives with roles. "
        "Cite at least 3 recent sources (title + URL) and save entities/relationships to the graph."
    )

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
    if not req.company:
        raise HTTPException(status_code=400, detail="company is required")

    task = build_competitor_prompt(req.company)

    try:
        content = await asyncio.wait_for(
            run_in_threadpool(run_agent, task, req.thread_id or str(uuid.uuid4())),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        competitors = await get_competitors(req.company)
        competitors_list = filter_competitors(competitors.get("competitors", []))
        if not competitors_list:
            fallback_task = build_competitor_fallback_prompt(req.company)
            await asyncio.wait_for(
                run_in_threadpool(run_agent, fallback_task, req.thread_id or str(uuid.uuid4())),
                timeout=Config.RUN_MISSION_TIMEOUT,
            )
            competitors = await get_competitors(req.company)
            competitors_list = filter_competitors(competitors.get("competitors", []))

        return {"result": content, "status": "success", "competitors": competitors_list}
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
    if not req.company:
        raise HTTPException(status_code=400, detail="company is required")

    profile_task = (
        f"Profile the company '{req.company}'. "
        "Return canonical name, HQ/country, founded year, and 3 key executives with roles. "
        "Cite at least 3 recent sources (title + URL) and save entities/relationships to the graph."
    )
    competitor_task = (
        build_competitor_prompt(req.company)
    )

    try:
        profile_result = await asyncio.wait_for(
            run_in_threadpool(run_agent, profile_task, req.thread_id or str(uuid.uuid4())),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        competitor_result = await asyncio.wait_for(
            run_in_threadpool(run_agent, competitor_task, req.thread_id or str(uuid.uuid4())),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        competitors = await get_competitors(req.company)
        competitors_list = filter_competitors(competitors.get("competitors", []))
        if not competitors_list:
            fallback_task = build_competitor_fallback_prompt(req.company)
            await asyncio.wait_for(
                run_in_threadpool(run_agent, fallback_task, req.thread_id or str(uuid.uuid4())),
                timeout=Config.RUN_MISSION_TIMEOUT,
            )
            competitors = await get_competitors(req.company)
            competitors_list = filter_competitors(competitors.get("competitors", []))
        try:
            profile_view = await entity_profile(req.company)
        except HTTPException:
            profile_view = None

        return {
            "status": "success",
            "profile_result": profile_result,
            "competitor_result": competitor_result,
            "profile": profile_view,
            "competitors": competitors_list,
        }
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Company insight timed out")
    except Exception as e:
        logger.error(f"Company insight error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
