# Project Structure

This repository is organized for team work: backend, frontend, operations and documentation are separated, while the root keeps only shared entrypoints.

## Root

```text
.
+-- backend/              # Python runtime: bot, API, database schema, RAG
+-- frontend/             # User interfaces
+-- docs/                 # Architecture, deploy notes and legal docs
+-- tools/                # Manual maintenance scripts, not normal runtime code
+-- docker-compose.yml    # Runtime services: Telegram bot, API, PostgreSQL
+-- .env.example          # Environment variable template
`-- README.md             # Quick start and deploy commands
```

Root should stay small. New product code should not be added directly to the root.

## Backend: `backend/`

```text
backend/
+-- src/                  # Importable Python package used as `src`
+-- database/             # SQL init files and local database artifacts
+-- Dockerfile            # Python app image
+-- requirements.txt      # Python dependencies
`-- .dockerignore         # Backend Docker build ignore rules
```

The Docker image still runs Python modules as `src.*`, because inside the container `backend/src` is mounted/copied to `/app/src`.

## Backend Package: `backend/src/`

```text
backend/src/
+-- bot.py                # Telegram entrypoint
+-- web_api.py            # HTTP API entrypoint
+-- database.py           # Database schema and data access methods
+-- services.py           # Runtime service registry
+-- helpers.py            # Shared helper functions
+-- core/                 # Cross-cutting backend helpers: config
+-- api/                  # HTTP API application, routes and auth
+-- routers/              # Telegram command/callback/message routers
+-- modules/              # Shared tutoring/business modules
+-- rag/                  # Retrieval, task search and trend analysis
`-- parsers/              # Educational task parsers/loaders
```

## Shared Modules: `backend/src/modules/`

Important files:

- `tutor_engine.py` - shared tutoring response engine for Telegram, VK and web.
- `ai_client.py` - OpenRouter calls, model routing and fallback behavior.
- `ai_gateway.py` - guarded OpenRouter entrypoint with queue admission and per-kind stats.
- `model_router.py` - selects fast/reasoning/fallback models.
- `anti_spam.py` - per-user and global request throttling.
- `request_guard.py` - AI concurrency guard.
- `vk_auth.py` - VK Mini App launch parameter handling.
- `memory.py` - dialog memory and profile summarization.
- `prompts.py` - system prompts and tutoring policy.
- `tutor_intent.py` - detects concept questions, task solving and guided mode.

Rule: reusable learning logic belongs in `backend/src/modules/`, not inside Telegram routers or frontend code.
Ordinary Telegram, VK and Web chat responses should go through `backend/src/modules/tutor_engine.py`.

## Core Helpers: `backend/src/core/`

```text
backend/src/core/
+-- config.py             # Environment variable parsing helpers
`-- __init__.py
```

Rule: `core/` is for small cross-cutting helpers used by many layers. It should not depend on Telegram, VK, OpenRouter, database models or feature-specific modules.

## Telegram Layer: `backend/src/routers/`

Telegram-specific code belongs here:

- commands
- callback buttons
- Telegram keyboards
- Telegram message formatting
- Telegram-only flows

Routers may call shared modules, but shared modules should not depend on Telegram objects.

## HTTP API: `backend/src/api/`

```text
backend/src/api/
+-- app.py                # aiohttp app factory and API service lifecycle
+-- routes.py             # API route handlers
+-- auth.py               # VK/dev authentication helpers
+-- utils.py              # JSON/CORS/env helpers
`-- __init__.py
```

`backend/src/web_api.py` remains as the Docker entrypoint:

```bash
python -m src.web_api
```

Current API endpoints:

- `GET /health`
- `POST /api/chat`
- `GET /api/profile`
- `GET /api/achievements`
- `GET /api/activity`
- `GET /api/practice/task`
- `POST /api/practice/answer`

Rule: VK Mini App and future web clients must talk to backend only through API endpoints.

## RAG Area: `backend/src/rag/`

This folder contains platform-neutral Tutor-RAG code:

- retrieval/search code
- analyzers and ranking helpers
- topic/task context extraction

Current production baseline:

- `search.py` retrieves and locally reranks tasks by metadata, topic, condition and answer.
- `pipeline.py` analyzes the student query, infers subject/task number, filters weak context and formats compact task context for the tutor engine.

Keep RAG code platform-neutral. Telegram, VK and Web should call it through shared services.

## Frontend: `frontend/vk-mini-app/`

```text
frontend/vk-mini-app/
+-- src/
|   +-- App.jsx           # Current Mini App UI
|   +-- main.jsx          # React entrypoint
|   `-- styles.css        # App styling
+-- public/               # Static public assets
+-- package.json          # Frontend dependencies and scripts
+-- package-lock.json     # Locked frontend dependencies
+-- vite.config.js        # Vite config
`-- .env.example          # Frontend env template
```

Rule: frontend must not contain API keys, OpenRouter keys, database credentials or bot tokens.

## Documentation: `docs/`

- `bot_architecture.md` - detailed bot architecture.
- `bot_architecture.html` - readable HTML version.
- `nginx_tutor_api.conf` - Nginx API proxy template.
- `project_structure.md` - this file.
- Legal/user-facing docs: offer, privacy, refund.

## Maintenance Scripts: `tools/`

```text
tools/
+-- fipi/                 # FIPI download/extraction/answer generation scripts
`-- db/                   # Database maintenance scripts
```

These scripts are useful for manual data operations, but they are not part of the normal bot/API runtime.

## Deploy Map

Server path:

```text
/opt/tutor-bot
```

Main backend deploy:

```bash
cd /opt/tutor-bot
git pull
python -m compileall -q backend/src
docker compose -f docker-compose.yml up -d --build tutor-bot tutor-api
docker compose -f docker-compose.yml logs -f --tail=100 tutor-api
curl https://api.evo-lution96.ru/health
```

VK Mini App local run:

```powershell
cd C:\Users\admin\Documents\Codex\bot\frontend\vk-mini-app
npm run dev
```

## Clean Structure Rules

- Put Telegram-specific behavior in `backend/src/routers/`.
- Put cross-cutting helpers in `backend/src/core/`.
- Put reusable learning/business logic in `backend/src/modules/`.
- Put public HTTP behavior in `backend/src/api/`.
- Put RAG retrieval code in `backend/src/rag/`.
- Put frontend code only in `frontend/vk-mini-app/`.
- Put operational notes and configs in `docs/`.
- Do not commit `.env`, `node_modules/`, `dist/`, `.vsix` files or local diagnostics.
