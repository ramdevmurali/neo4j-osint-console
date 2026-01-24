import asyncio
import logging
from typing import Any

from fastapi.concurrency import run_in_threadpool

from src.agent import run_agent
from src.config import Config
from src.routes.graph import get_competitors, entity_profile
from src.graph_db import GraphManager

logger = logging.getLogger("insight_service")


def normalize_company(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum() or ch.isspace()).strip()


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


def _strip_non_primitives(obj: Any):
    """Recursively drop non-primitive values (maps/objects) since Neo4j props must be primitives/arrays."""
    if isinstance(obj, dict):
        return {k: _strip_non_primitives(v) for k, v in obj.items() if _is_primitive_or_list(v)}
    if _is_primitive_or_list(obj):
        return obj
    return None


def _is_primitive_or_list(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, (str, int, float, bool)):
        return True
    if isinstance(v, list):
        return all(_is_primitive_or_list(x) for x in v)
    return False


async def run_competitor_flow(company: str, thread_id: str | None) -> tuple[Any, list[dict[str, Any]]]:
    """Run competitor agent with a retry and return (agent_result, competitors_from_graph)."""
    comp_prompt = build_competitor_prompt(company)
    fallback_prompt = build_competitor_fallback_prompt(company)

    result = await asyncio.wait_for(
        run_in_threadpool(run_agent, comp_prompt, thread_id or ""),
        timeout=Config.RUN_MISSION_TIMEOUT,
    )
    competitors = await get_competitors(company)
    competitors_list = filter_competitors(competitors.get("competitors", []))

    if not competitors_list:
        await asyncio.wait_for(
            run_in_threadpool(run_agent, fallback_prompt, thread_id or ""),
            timeout=Config.RUN_MISSION_TIMEOUT,
        )
        competitors = await get_competitors(company)
        competitors_list = filter_competitors(competitors.get("competitors", []))

    return result, competitors_list


async def run_company_insight(company: str, thread_id: str | None):
    """End-to-end: profile + competitors + mood, in parallel with bounded timeouts."""

    profile_prompt = build_profile_prompt(company)
    competitor_prompt = build_competitor_prompt(company)
    competitor_fallback = build_competitor_fallback_prompt(company)

    async def run_llm(prompt: str, timeout: float):
        return await asyncio.wait_for(
            run_in_threadpool(run_agent, prompt, thread_id or ""),
            timeout=timeout,
        )

    # Run profile, competitors, and mood concurrently with caps
    profile_result, competitor_result, mood_view = await asyncio.gather(
        run_llm(profile_prompt, min(Config.RUN_MISSION_TIMEOUT, 20)),
        run_llm(competitor_prompt, min(Config.RUN_MISSION_TIMEOUT, 20)),
        run_company_mood(company, thread_id),
        return_exceptions=True,
    )

    if isinstance(profile_result, Exception):
        logger.warning(f"profile skipped: {profile_result}")
        profile_result = "Profile skipped due to error."

    competitors = await get_competitors(company)
    competitors_list = filter_competitors(competitors.get("competitors", []))
    if not competitors_list:
        try:
            await run_llm(competitor_fallback, min(Config.RUN_MISSION_TIMEOUT, 15))
            competitors = await get_competitors(company)
            competitors_list = filter_competitors(competitors.get("competitors", []))
        except Exception as exc:
            logger.warning(f"competitor fallback skipped: {exc}")
            competitor_result = "Competitor scout skipped due to error."

    try:
        profile_view = await entity_profile(company)
    except Exception as exc:
        logger.warning(f"profile view skipped: {exc}")
        profile_view = None

    if isinstance(mood_view, Exception):
        logger.warning(f"mood fetch skipped: {mood_view}")
        mood_view = {"label": None, "score": None, "headlines": [], "raw": None}

    return {
        "profile_result": profile_result,
        "competitor_result": competitor_result,
        "profile": profile_view,
        "competitors": competitors_list,
        "mood": mood_view,
    }


# ---- Sentiment / mood -------------------------------------------------------


def _extract_json_block(text: str) -> dict[str, Any] | None:
    """Best-effort parse of first JSON object in a text blob."""
    import json, re

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        block = match.group(0)
        try:
            return json.loads(block)
        except Exception:
            return None
    return None


def _upsert_mood(company: str, label: str | None, score: float | None):
    if label is None and score is None:
        return
    db = GraphManager()
    with db.session() as session:
        session.run(
            """
            MATCH (o:Organization)
            WHERE toLower(o.name) = toLower($name)
            SET o.mood_label = coalesce($label, o.mood_label),
                o.mood_score = coalesce($score, o.mood_score),
                o.mood_updated_at = timestamp()
            """,
            name=company,
            label=label,
            score=score,
        )


async def run_company_mood(company: str, thread_id: str | None):
    """
    Derive company mood from recent headlines; returns dict with label, score, headlines.
    """
    prompt = (
        f"Give a quick sentiment for '{company}' from recent news (last 60 days). "
        "Return JSON only: {mood_label:'positive|neutral|negative', mood_score:-1..1, headlines:[{title, url}] up to 3}. "
        "No prose, JSON only."
    )

    mood_thread = thread_id or f"mood-{company}"
    raw = await asyncio.wait_for(
        run_in_threadpool(run_agent, prompt, mood_thread),
        timeout=min(Config.RUN_MISSION_TIMEOUT, 15),
    )

    parsed = _extract_json_block(raw if isinstance(raw, str) else str(raw))
    if not parsed or not isinstance(parsed, dict):
        return {"label": None, "score": None, "headlines": [], "raw": raw}

    label = parsed.get("mood_label") or parsed.get("label")
    score = parsed.get("mood_score") or parsed.get("score")
    headlines = parsed.get("headlines") or []
    if not isinstance(headlines, list):
        headlines = []

    # upsert to graph (best effort)
    try:
        _upsert_mood(company, label, float(score) if score is not None else None)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning(f"mood upsert skipped: {exc}")

    return {
        "label": label,
        "score": score,
        "headlines": headlines[:5],
        "raw": raw,
    }


__all__ = [
    "normalize_company",
    "build_profile_prompt",
    "build_competitor_prompt",
    "build_competitor_fallback_prompt",
    "filter_competitors",
    "run_competitor_flow",
    "run_company_insight",
]
