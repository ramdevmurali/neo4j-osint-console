import asyncio
import logging
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from src.agent import run_agent
from src.config import Config
from src.routes.graph import get_competitors  # reuse for response enrichment

logger = logging.getLogger("agents")
router = APIRouter()


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

    task = (
        f"Find 3-5 close competitors for '{req.company}'. "
        "For each competitor, give a one-line rationale and at least one source URL. "
        "Create Organization nodes if needed and write COMPETES_WITH relationships from the target company "
        "to each competitor, setting relationship properties reason and source_url. "
        "Use save_to_graph with entities [{name: <company>, label: 'Organization'}, {name: <competitor>, label: 'Organization'}] "
        "and relationships [{source: <company>, target: <competitor>, type: 'COMPETES_WITH', properties: {reason: <why>, source_url: <url>}}]. "
        "Pick competitors from credible recent sources."
    )

    try:
        content = await asyncio.wait_for(
            run_in_threadpool(run_agent, task, req.thread_id or str(uuid.uuid4())),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        competitors = await get_competitors(req.company)
        return {"result": content, "status": "success", "competitors": competitors["competitors"]}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Competitor scout timed out")
    except Exception as e:
        logger.error(f"Competitor scout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

