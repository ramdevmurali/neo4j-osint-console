# Project Gotham – Intelligence Console

Turn open-source signals into a living knowledge graph (Neo4j). Submit a company-focused mission, let the backend orchestrate search + LLM analysis, dedupe, and write entities/relationships, then explore competitors, mood, and a live graph preview with source traceability.

## Stack
- **Backend:** FastAPI, LangGraph + Google Gemini, Neo4j
- **Frontend:** Next.js (app router), design tokens/Tailwind-like utility classes, react-force-graph-2d
- **Infra:** Dockerfiles for backend and frontend; shared caps/limits in `backend/src/constants.py` and `frontend/src/lib/constants.ts`

## Architecture
```
[Next.js UI]
   ↓ (API proxies → FastAPI)
[LangGraph orchestrator] --(rate limited + sanitized writes)--> [Neo4j]
   ↑                                     ↓
 (LLM: Gemini)                  Graph views (stats/sample/competitors)
```

## Key features
- Rate-limited LLM calls with backoff; concurrency capped.
- Graph write sanitization (primitives only) to avoid Neo4j type errors.
- Shared caps/constants to keep UI/server aligned (sample doc limit, competitor cap, mood drivers).
- Skeleton loaders, concise errors, and partial-data resilience.
- MCP server (`backend/src/server.py`) exposes graph ingest and Tavily search as tools for agents.
- Quick demo flow: enter a company → dispatch mission → view competitors/mood → open sample graph.

## Running locally
Prereqs: Python 3.11+, Node 18+

Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

Frontend
```bash
cd frontend
npm install
npm run dev -- --hostname 0.0.0.0 --port 3000
```

## Docker
- Backend: `docker build -t gotham-backend ./backend` (listens on 8000)
- Frontend: `docker build -t gotham-frontend ./frontend` (runs `npm start` for prod build on 3000)
- (Add docker-compose if you want a single `docker compose up`.)

## Env
- Backend `.env`: LLM keys, Neo4j URI/user/pass.
- Frontend proxies to backend at `http://localhost:8000` by default (see `frontend/src/app/api/*`). Override via `API_BASE` in those routes if needed.
- Data sources: LLM search via Gemini + Tavily; bring your own API keys.

## Tests & lint
```bash
cd backend && source .venv/bin/activate && pytest
cd frontend && npm run lint
```

## Defaults
- SAMPLE_DOC_LIMIT: 5
- COMPETITOR_DISPLAY_CAP: 4
- MOOD_DRIVERS_DISPLAY_CAP: 2
- Mood fetch is opt-in (reduces latency).

## Demo (add your media)
- Mission console before/after: _insert screenshot/gif link_
- Graph preview: _insert screenshot/gif link_
- Optional video link (YouTube/Loom): _insert link_

## Known limitations
- Dependent on LLM output quality and network latency.
- Mood/competitor accuracy may vary; treat as assistive, not authoritative.

## How to extend
- New agents: add to `backend/src/routes/agents.py` (and services) via LangGraph.
- New graph views: add to `backend/src/routes/graph.py`.
- Frontend: reuse `frontend/src/lib/fetcher.ts` and `frontend/src/lib/constants.ts` for new calls and caps.
- Tools: `backend/src/tools/graph.py` handles sanitized graph writes; `backend/src/tools/search.py` wraps Tavily search. Typically no changes needed when adding agents unless adding new tool types.
- MCP: Add tools under `backend/src/tools/`, register them in `backend/src/server.py` (FastMCP), and wire them into `src/agent.py` and routes as needed.
