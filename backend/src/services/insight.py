import asyncio
import uuid
from typing import Any

from fastapi.concurrency import run_in_threadpool

from src.agent import run_agent
from src.config import Config
from src.services.graph_queries import fetch_competitors, fetch_entity_profile
from src.constants import COMPETITOR_DISPLAY_CAP

def build_profile_prompt(company: str) -> str:
    return (
        f"Profile the company '{company}'. "
        "Return canonical name, HQ/country, founded year, and 3 key executives with roles. "
        "Cite at least 3 recent sources (title + URL) and save entities/relationships to the graph."
    )


def build_competitor_prompt(company: str) -> str:
    return (
        f"Find 4-6 close competitors for '{company}' (direct/adjacent peers only). "
        "For each competitor, give a one-line rationale and at least one source URL. "
        "DO NOT return blanks. If sources are thin, broaden query and retry once. "
        "Create Organization nodes if needed and write COMPETES_WITH relationships from the target company "
        "to each competitor, setting relationship properties reason and source_url. "
        "Use save_to_graph with entities [{name: <company>, label: 'Organization'}, {name: <competitor>, label: 'Organization'}] "
        "and relationships [{source: <company>, target: <competitor>, type: 'COMPETES_WITH', properties: {reason: <why>, source_url: <url>}}]. "
        "Pick competitors from credible recent sources."
    )


def build_competitor_fallback_prompt(company: str) -> str:
    return (
        f"List 4-6 direct competitors for '{company}' with reason and URL. "
        "Save COMPETES_WITH edges via save_to_graph. Do not return an empty list."
    )


def filter_competitors(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for rec in items:
        comp = rec.get("competitor")
        reason = rec.get("reason")
        if comp and reason:
            cleaned.append(
                {
                    "competitor": str(comp),
                    "reason": str(reason),
                    "source": rec.get("source"),
                }
            )
    return cleaned


async def run_competitor_flow(company: str, thread_id: str | None) -> tuple[Any, list[dict[str, Any]]]:
    """Run competitor agent with a retry and return (agent_result, competitors_from_graph)."""
    run_id = thread_id or str(uuid.uuid4())
    comp_prompt = build_competitor_prompt(company)
    fallback_prompt = build_competitor_fallback_prompt(company)

    result = await asyncio.wait_for(
        run_in_threadpool(run_agent, comp_prompt, run_id),
        timeout=Config.RUN_MISSION_TIMEOUT,
    )
    competitors = await asyncio.wait_for(
        run_in_threadpool(fetch_competitors, company),
        timeout=8,
    )
    competitors_list = filter_competitors(competitors)[:COMPETITOR_DISPLAY_CAP]

    if not competitors_list:
        await asyncio.wait_for(
            run_in_threadpool(run_agent, fallback_prompt, run_id),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        competitors = await asyncio.wait_for(
            run_in_threadpool(fetch_competitors, company),
            timeout=8,
        )
        competitors_list = filter_competitors(competitors)[:COMPETITOR_DISPLAY_CAP]

    return result, competitors_list


async def run_company_insight(company: str, thread_id: str | None):
    """End-to-end: profile + competitors + graph views."""
    run_id = thread_id or str(uuid.uuid4())
    profile_prompt = build_profile_prompt(company)

    profile_result = await asyncio.wait_for(
        run_in_threadpool(run_agent, profile_prompt, run_id),
        timeout=Config.RUN_MISSION_TIMEOUT,
    )
    competitor_result, competitors_list = await run_competitor_flow(company, run_id)

    try:
        profile_view = await asyncio.wait_for(
            run_in_threadpool(fetch_entity_profile, company),
            timeout=8,
        )
    except Exception:
        profile_view = None

    return {
        "profile_result": profile_result,
        "competitor_result": competitor_result,
        "profile": profile_view,
        "competitors": competitors_list,
    }


__all__ = [
    "build_profile_prompt",
    "build_competitor_prompt",
    "build_competitor_fallback_prompt",
    "filter_competitors",
    "run_competitor_flow",
    "run_company_insight",
]
