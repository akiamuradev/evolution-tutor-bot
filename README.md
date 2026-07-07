# EVO:LUTION Tutor Bot

Portfolio-ready educational AI tutor with a Telegram bot, VK Mini App frontend,
shared HTTP API, PostgreSQL storage, task search/RAG and OpenRouter integration.

## What This Project Shows

- Async Python backend with `aiogram`, `aiohttp`, `asyncpg` and `asyncio`.
- Telegram bot architecture with routers, middleware, FSM scenarios and callbacks.
- Shared tutoring engine reused by Telegram and VK/Web API clients.
- OpenRouter/LiteLLM-compatible AI client with model routing, fallback retries, LRU cache and guarded concurrency.
- Tutor-RAG pipeline over a PostgreSQL task bank with ranked retrieval and confidence gating.
- Student progress tracking, achievements, activity sessions and long-term dialog memory.
- React/Vite VK Mini App with chat, practice, profile, achievements and theme support.
- Docker Compose runtime with bot, API and PostgreSQL services.
- Parser and maintenance tools for FIPI/Sdamgia/Math100 educational data.

## Repository Structure

```text
.
├── backend/                  # Python runtime: bot, API, tutoring engine, RAG, database
│   ├── src/
│   │   ├── bot.py            # Telegram entrypoint
│   │   ├── web_api.py        # HTTP API entrypoint
│   │   ├── api/              # aiohttp routes and auth
│   │   ├── modules/          # shared AI/tutor/business logic
│   │   ├── rag/              # task retrieval and query analysis
│   │   ├── routers/          # Telegram-specific handlers
│   │   └── parsers/          # task source parsers/loaders
│   ├── database/init.sql
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/vk-mini-app/     # React/Vite VK Mini App
├── docs/                     # architecture, structure, deploy/legal notes
├── tools/                    # manual data and database maintenance scripts
├── docker-compose.yml
└── .env.example
```

## Architecture

```text
Telegram user -> tutor-bot -> TutorEngine -> AI Gateway -> OpenRouter
                               |             |
                               |             -> model routing / queue / cache
                               |
                               -> PostgreSQL memory + progress + RAG context

VK Mini App -> tutor-api -> TutorEngine -> same AI, RAG and database layers
```

Detailed portfolio architecture:

- `docs/bot_architecture.html`
- `docs/bot_architecture.md`
- `docs/project_structure.md`

## Tech Stack

Backend:

- Python 3.11
- aiogram 3
- aiohttp
- asyncpg
- httpx
- PostgreSQL / pgvector image
- OpenRouter or LiteLLM-compatible endpoint
- BeautifulSoup, pdfplumber
- python-docx, reportlab
- SymPy, NumPy, Matplotlib

Frontend:

- React 18
- Vite
- VK Bridge
- CSS light/dark responsive UI

Infrastructure:

- Docker
- Docker Compose
- Nginx reverse proxy example

## Environment

Copy the template and fill your own local values:

```bash
cp .env.example .env
```

Important variables:

```env
TG_BOT_TOKEN=
OPENROUTER_API_KEY=
DATABASE_URL=
POSTGRES_PASSWORD=
VK_APP_SECRET=
```

Never commit `.env`, real database dumps, `node_modules`, frontend `dist` or local diagnostics.

## Run With Docker

```bash
docker compose up -d --build
docker compose logs -f --tail=100 tutor-bot
curl http://localhost:8080/health
```

Services:

- `tutor-bot` runs `python -m src.bot`
- `tutor-api` runs `python -m src.web_api`
- `postgres` stores users, tasks, memory, progress and achievements

## Backend Checks

```bash
python -m compileall -q backend/src
```

## VK Mini App Local Run

```bash
cd frontend/vk-mini-app
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/health` to `http://localhost:8080`.

## Frontend Build

```bash
cd frontend/vk-mini-app
npm run build
```

## GitHub Upload

See `GITHUB_UPLOAD.md` for the exact commands to initialize a fresh repository
and push this cleaned version to GitHub.
