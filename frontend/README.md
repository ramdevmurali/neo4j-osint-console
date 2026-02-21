# Frontend (Project Gotham)

Next.js app for the Project Gotham intelligence console.

## Scope
- Mission console UI, graph preview, competitor/mood views.
- Backend proxy routes under `src/app/api/*`.
- Shared limits with backend via `frontend/src/lib/constants.ts`.

## Prerequisites
- Node 20+
- Backend API available on port `8000` (local) or service `backend:8000` (compose)

## Local Development
```bash
cd frontend
npm install
npm run dev -- --hostname 0.0.0.0 --port 3000
```

Open `http://localhost:3000`.

## API Base Resolution
`frontend/src/lib/config.ts` resolves backend base URL in this order:
1. `API_BASE` (preferred in docker compose)
2. `NEXT_PUBLIC_API_BASE`
3. `http://localhost:8000` (fallback)

## Build and Run
```bash
cd frontend
npm run build
npm start
```

## Docker
```bash
docker build -t gotham-frontend ./frontend
docker run --rm -p 3000:3000 -e API_BASE=http://host.docker.internal:8000 gotham-frontend
```

## Useful Paths
- Page entry: `src/app/page.tsx`
- Graph preview: `src/components/ui/graph-preview.tsx`
- Proxy routes: `src/app/api/*`
- Shared fetch helper: `src/lib/fetcher.ts`
