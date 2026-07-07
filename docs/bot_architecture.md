# EVO:LUTION Tutor Bot Architecture

This document summarizes the public portfolio architecture of the bot.
The full visual version is available in `docs/bot_architecture.html`.

## Product Shape

EVO:LUTION is a multi-platform educational AI tutor:

- Telegram bot for chat, practice, achievements, settings and generated study materials.
- HTTP API for VK Mini App and future web clients.
- React/Vite VK Mini App for chat, practice, achievements and profile views.
- PostgreSQL storage for users, tasks, progress, achievements, memory and activity.
- Tutor-RAG layer over the task bank.
- OpenRouter/LiteLLM-compatible AI integration with routing, cache and guarded concurrency.

## High-Level Flow

```text
Telegram / VK Mini App
-> platform adapter: router or API route
-> anti-spam and auth checks
-> shared TutorEngine
-> dialog memory + RAG task context
-> AI Gateway
-> OpenRouter model
-> response cleanup
-> save memory/progress/activity
-> return answer to user
```

## Runtime Services

| Service | Entrypoint | Purpose |
|---|---|---|
| `tutor-bot` | `python -m src.bot` | Telegram polling, routers, FSM flows and bot UI. |
| `tutor-api` | `python -m src.web_api` | aiohttp API for VK/Web clients. |
| `postgres` | `pgvector/pgvector:pg16` | Users, tasks, progress, memory, achievements and sessions. |

## Backend Layers

| Layer | Files | Responsibility |
|---|---|---|
| Entrypoints | `backend/src/bot.py`, `backend/src/web_api.py` | Start Telegram bot and HTTP API. |
| API | `backend/src/api/` | Health, profile, chat, achievements, activity and practice endpoints. |
| Telegram routers | `backend/src/routers/` | Commands, callbacks, FSM, messages, practice and settings. |
| Shared modules | `backend/src/modules/` | AI client, tutor engine, memory, anti-spam, model routing and utilities. |
| RAG | `backend/src/rag/` | Query analysis, ranked task search and compact task context. |
| Database | `backend/src/database.py`, `backend/database/init.sql` | Schema and async data access. |
| Parsers | `backend/src/parsers/`, `tools/fipi/` | Educational data loading and maintenance. |

## Shared Tutor Engine

`backend/src/modules/tutor_engine.py` is the platform-neutral core.
Telegram and API clients both call `generate_tutor_response()`.

The engine:

- loads recent dialog context;
- builds long-term memory context;
- applies guided-solving policy;
- retrieves RAG task context when useful;
- calls the guarded AI gateway;
- cleans the answer;
- saves user and assistant messages;
- schedules memory profile updates.

## AI Layer

| Component | Responsibility |
|---|---|
| `model_router.py` | Selects fast, standard or reasoning model based on question complexity. |
| `ai_client.py` | Calls OpenRouter, normalizes messages, retries fallback models and caches responses. |
| `request_guard.py` | Limits global AI concurrency and rejects duplicate active requests per user. |
| `ai_gateway.py` | Wraps AI calls with queue admission, metrics and busy responses. |
| `generation_control.py` | Tracks cancellable long-running generation tasks per user. |
| `cache.py` | LRU cache for repeated model responses. |

## Database Model

| Table | Purpose |
|---|---|
| `users` | User profile, consent, grade, subscriptions, limits and settings. |
| `subjects` | School subject catalog. |
| `fipi_tasks` | Educational task bank with condition, solution, answer and explanation. |
| `student_progress` | Practice attempts, correctness and explanation usage. |
| `achievements` | Unlocked achievement records. |
| `user_events` | Request/activity events for achievement metrics. |
| `ai_dialog_messages` | Recent and searchable dialog history. |
| `ai_memory_profiles` | Long-term summary and learning profile. |
| `user_sessions`, `user_time_stats` | Active time tracking and aggregated activity. |

## Frontend/API

The VK Mini App uses:

- `GET /health`
- `POST /api/chat`
- `GET /api/profile`
- `GET /api/achievements`
- `GET /api/activity`
- `GET /api/practice/task`
- `POST /api/practice/answer`

VK launch parameters are verified through HMAC SHA-256 in `modules/vk_auth.py`.

## Demonstrated Engineering Skills

- Async Python service architecture.
- Telegram bot development with aiogram.
- HTTP API design with aiohttp.
- LLM integration and prompt orchestration.
- Request throttling and concurrency control.
- RAG/search over PostgreSQL data.
- Database schema and index design.
- React/Vite frontend development.
- Docker-based deployment.
- Data parsing and ETL tooling for educational content.
