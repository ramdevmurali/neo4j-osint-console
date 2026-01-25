import json
import logging
import re
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import Config
from src.tools.search import perform_search

logger = logging.getLogger("company_mood")

_MOOD_LABELS = {"Positive", "Neutral", "Negative", "Mixed", "Volatile"}


def _build_query(company: str, timeframe: str) -> str:
    return (
        f"{company} earnings results financial performance guidance analyst sentiment "
        f"news last {timeframe}"
    )


def _build_prompt(company: str, timeframe: str, sources: list[dict[str, str]]) -> str:
    source_block = "\n\n".join(
        f"{idx+1}. {s.get('title','')} ({s.get('url','')})\n{s.get('content','')}"
        for idx, s in enumerate(sources)
    )
    return (
        "You are an analyst summarizing near-term company mood.\n"
        f"Company: {company}\n"
        f"Timeframe: last {timeframe}\n"
        "Use ONLY the sources below. Include financial/earnings context.\n"
        "Return ONLY valid JSON with keys:\n"
        "mood_label: one of [Positive, Neutral, Negative, Mixed, Volatile]\n"
        "confidence: number 0-1\n"
        "drivers: 3-5 short bullet strings\n"
        "sources: 2-3 items with {title, url}\n"
        "timeframe: string\n\n"
        f"SOURCES:\n{source_block}"
    )


def _parse_json(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    try:
        return json.loads(cleaned)
    except Exception:
        logger.warning("Mood JSON parse failed.")
        return None


def get_company_mood(company: str, timeframe: str = "90d", max_sources: int = 3) -> dict[str, Any]:
    """Return transient mood summary (no graph writes)."""
    results = perform_search(_build_query(company, timeframe), max_results=max_sources)
    sources = [
        {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
        for r in results
        if r.get("url")
    ][:max_sources]

    if not sources:
        return {
            "mood_label": "Mixed",
            "confidence": 0.35,
            "drivers": ["Insufficient recent sources to assess mood."],
            "sources": [],
            "timeframe": timeframe,
        }

    llm = ChatGoogleGenerativeAI(
        model=Config.MODEL_NAME,
        temperature=0.2,
        max_retries=Config.LLM_MAX_RETRIES,
        timeout=Config.LLM_TIMEOUT,
        convert_system_message_to_human=True,
    )
    prompt = _build_prompt(company, timeframe, sources)
    response = llm.invoke(prompt)
    parsed = _parse_json(response.content if hasattr(response, "content") else str(response))

    if not parsed:
        return {
            "mood_label": "Mixed",
            "confidence": 0.4,
            "drivers": ["Unable to parse model output; using fallback mood."],
            "sources": [{"title": s.get("title"), "url": s.get("url")} for s in sources[:2]],
            "timeframe": timeframe,
        }

    mood_label = parsed.get("mood_label")
    if mood_label not in _MOOD_LABELS:
        mood_label = "Mixed"
    return {
        "mood_label": mood_label,
        "confidence": parsed.get("confidence", 0.5),
        "drivers": parsed.get("drivers", []),
        "sources": parsed.get("sources", [{"title": s.get("title"), "url": s.get("url")} for s in sources[:2]]),
        "timeframe": parsed.get("timeframe", timeframe),
    }


__all__ = ["get_company_mood"]
