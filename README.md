# EVO:LUTION Tutor Bot

[![CI](https://github.com/akiamuradev/evolution-tutor-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/akiamuradev/evolution-tutor-bot/actions/workflows/ci.yml)

![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![aiogram 3.4.1](https://img.shields.io/badge/aiogram-3.4.1-2CA5E0)
![aiohttp 3.9.1](https://img.shields.io/badge/aiohttp-3.9.1-2C5BB4)
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-runtime-2496ED?logo=docker&logoColor=white)
![React 18](https://img.shields.io/badge/React-18.3.1-61DAFB?logo=react&logoColor=black)
![Vite 8](https://img.shields.io/badge/Vite-8.0.0-646CFF?logo=vite&logoColor=white)
![VK Bridge](https://img.shields.io/badge/VK_Bridge-3.0.2-0077FF?logo=vk&logoColor=white)
![OpenRouter](https://img.shields.io/badge/OpenRouter-compatible-111827)

[Русский](#русский) | [English](#english)

## Русский

EVO:LUTION Tutor Bot - мультиплатформенный AI-репетитор для школьников: Telegram-бот, HTTP API и VK Mini App работают поверх общего backend-ядра. Проект помогает разбирать учебные вопросы, решать практические задания, учитывать прогресс ученика и использовать контекст из базы заданий при ответах LLM.

Это не простой wrapper вокруг чат-модели: в репозитории есть асинхронный Python backend, Telegram-слой, aiohttp API, React/Vite VK Mini App, PostgreSQL-схема, TutorEngine, RAG-пайплайн по учебным заданиям, память диалога, антиспам, ограничение AI-нагрузки, Docker Compose и GitHub Actions.

**Portfolio project showcasing AI-assisted development, async Python backend, Telegram bot, aiohttp HTTP API, PostgreSQL, task-based RAG, React/Vite, VK Bridge and Docker.**

## About

EVO:LUTION Tutor Bot предназначен для школьников, которым нужен помощник по учебным темам, домашним заданиям и подготовке к экзаменам. Основной пользовательский сценарий: ученик открывает Telegram-бота или VK Mini App, задает вопрос или берет тренировочное задание, получает пошаговое объяснение, отправляет ответ, а система сохраняет прогресс и использует историю дальше.

Проект показывает, как собрать образовательного AI-ассистента как полноценную backend-систему: с API, базой данных, памятью, поиском по учебным материалам, клиентским интерфейсом и инфраструктурой запуска.

## Key Features

### AI and RAG

- LLM-интеграция через OpenRouter-compatible endpoint; также поддерживается LiteLLM-compatible proxy через `LITELLM_BASE_URL` и `LITELLM_API_KEY`.
- Model routing в `backend/src/modules/model_router.py`: выбор fast/standard/reasoning модели по эвристике сложности вопроса.
- Fallback-попытки в `backend/src/modules/ai_client.py`: повторные запросы к альтернативным моделям и уменьшение `max_tokens` для retryable HTTP-статусов.
- Общий AI Gateway в `backend/src/modules/ai_gateway.py`: guarded-вызовы модели, статистика, busy-response и контроль активных генераций.
- In-memory LRU cache для повторяющихся AI-ответов.
- TutorEngine в `backend/src/modules/tutor_engine.py`: общий слой генерации ответов для Telegram и HTTP API.
- Память пользователя: последние сообщения, searchable dialog memory, долгосрочный summary и learning profile в таблицах `ai_dialog_messages` и `ai_memory_profiles`.
- RAG-пайплайн в `backend/src/rag/`: анализ запроса, определение предмета/номера задания, поиск кандидатов в PostgreSQL, локальный reranking и добавление компактного контекста в prompt.
- Важно: текущий production RAG в публичном коде использует текстовый/метаданный поиск и локальный reranking по базе заданий. Векторный embedding search не является подтвержденной рабочей частью текущей схемы.

### Learning Experience

- Onboarding в Telegram: согласие на обработку данных и выбор диапазона класса.
- Чат-репетитор: свободные учебные вопросы через общий TutorEngine.
- Guided mode: для части запросов система не сразу выдает готовое решение, а ведет ученика через подсказки.
- Практика по заданиям из `fipi_tasks`: получение задания, ввод ответа, проверка, сохранение попытки в `student_progress`.
- AI-объяснения для практических заданий: если объяснения нет в базе, оно генерируется и сохраняется в `fipi_tasks.explanation`.
- Статистика по решенным задачам: количество попыток, правильность, предметы, темы и использование объяснений.
- Достижения: вычисляются по активности, запросам, прогрессу и подписочным флагам.
- Activity tracking: учет пользовательских сессий и времени активности.
- Персональный недельный план в Telegram на основе статистики решенных задач, если у пользователя достаточно данных.
- Построение графиков функций в Telegram через SymPy/NumPy/Matplotlib.

### Platforms and Interfaces

- Telegram bot на `aiogram` с polling entrypoint `python -m src.bot`.
- HTTP API на `aiohttp` с entrypoint `python -m src.web_api`.
- VK Mini App на React/Vite/VK Bridge.
- API endpoints:
  - `GET /health`
  - `POST /api/chat`
  - `GET /api/profile`
  - `GET /api/achievements`
  - `GET /api/activity`
  - `GET /api/practice/task`
  - `POST /api/practice/answer`
- VK launch params verification через HMAC SHA-256 в `backend/src/modules/vk_auth.py`.
- Nginx reverse proxy template в `docs/nginx_tutor_api.conf`.

### Engineering

- Async Python stack: `aiogram`, `aiohttp`, `asyncpg`, `httpx`.
- PostgreSQL as the main storage for users, tasks, progress, achievements, memory and activity.
- Database indexes for task search, progress, achievements, sessions and dialog memory.
- Docker Compose runtime with three services: `tutor-bot`, `tutor-api`, `postgres`.
- PostgreSQL image: `pgvector/pgvector:pg16`; current public retrieval code does not rely on vector embeddings.
- Anti-spam and rate limiting in `backend/src/modules/anti_spam.py`.
- AI concurrency guard in `backend/src/modules/request_guard.py`.
- Per-user generation cancellation registry in `backend/src/modules/generation_control.py`.
- GitHub Actions CI:
  - backend compile check with Python 3.11;
  - frontend build with Node 22 and `npm run build`.
- Public repo hygiene: `.env` ignored, `.env.example` included, build artifacts and local database files ignored.

## Example User Flow

1. User opens the Telegram bot or VK Mini App.
2. Telegram user accepts data processing and selects a class range; VK Mini App user is identified by launch params.
3. User asks an educational question or requests a practice task.
4. Backend applies auth/rate checks and passes the request to TutorEngine.
5. TutorEngine builds context from system prompt, recent dialog, long-term memory and, when useful, RAG search over `fipi_tasks`.
6. AI Gateway sends a guarded request to the configured OpenRouter/LiteLLM-compatible model.
7. The response is returned to the user; dialog memory, activity, progress and achievements are updated in PostgreSQL.

## Architecture

Detailed architecture docs:

- [docs/bot_architecture.md](docs/bot_architecture.md)
- [docs/bot_architecture.html](docs/bot_architecture.html)
- [docs/project_structure.md](docs/project_structure.md)

```mermaid
flowchart LR
    TG["Telegram Bot<br/>aiogram"] --> TE["TutorEngine<br/>shared tutoring core"]
    VK["VK Mini App<br/>React/Vite/VK Bridge"] --> API["HTTP API<br/>aiohttp"]
    API --> TE
    TE --> MEM["Dialog Memory<br/>ai_dialog_messages<br/>ai_memory_profiles"]
    TE --> RAG["Tutor-RAG<br/>query analysis + task reranking"]
    RAG --> DB[(PostgreSQL)]
    MEM --> DB
    TE --> GATE["AI Gateway<br/>queue + guarded calls"]
    GATE --> LLM["OpenRouter / LiteLLM-compatible LLM"]
    API --> DB
    TG --> DB
```

### Main Components

| Component | Path | Purpose |
|---|---|---|
| Telegram entrypoint | `backend/src/bot.py` | Starts bot polling, initializes DB/RAG services, registers routers and anti-spam middleware. |
| HTTP API entrypoint | `backend/src/web_api.py` | Starts aiohttp API used by VK Mini App and future web clients. |
| API routes | `backend/src/api/routes.py` | Health, profile, achievements, activity, chat and practice endpoints. |
| TutorEngine | `backend/src/modules/tutor_engine.py` | Platform-neutral tutor response generation. |
| AI client | `backend/src/modules/ai_client.py` | OpenRouter/LiteLLM-compatible calls, model selection, retries and cache. |
| RAG | `backend/src/rag/` | Task query analysis, search and reranking over PostgreSQL task data. |
| Memory | `backend/src/modules/memory.py` | User memory context and periodic profile summarization. |
| Database | `backend/src/database.py`, `backend/database/init.sql` | Runtime schema, migrations-by-code and initial SQL schema. |
| VK Mini App | `frontend/vk-mini-app/` | React/Vite frontend with chat, practice, achievements and profile tabs. |
| Docs | `docs/` | Architecture, project structure, Nginx config and legal documents. |

## Tech Stack

| Area | Technologies |
|---|---|
| Backend | Python 3.11, aiogram, aiohttp, asyncpg, httpx |
| AI | OpenRouter-compatible API, optional LiteLLM-compatible proxy, prompt orchestration |
| RAG/Search | PostgreSQL task bank, text/metadata search, local reranking |
| Database | PostgreSQL, pgvector image, SQL schema, async data access |
| Frontend | React 18, Vite, VK Bridge |
| DevOps | Docker Compose, GitHub Actions, Nginx config |
| Data tooling | FIPI/Sdamgia/Math100 parser and maintenance scripts |
| Documents/Math tools | python-docx, reportlab, SymPy, NumPy, Matplotlib |

## Repository Structure

```text
.
+-- backend/
|   +-- Dockerfile
|   +-- requirements.txt
|   +-- database/
|   |   `-- init.sql
|   `-- src/
|       +-- bot.py
|       +-- web_api.py
|       +-- database.py
|       +-- api/
|       +-- modules/
|       +-- rag/
|       +-- routers/
|       `-- parsers/
+-- frontend/
|   `-- vk-mini-app/
|       +-- src/
|       +-- public/
|       +-- package.json
|       `-- vite.config.js
+-- docs/
+-- tools/
+-- .github/workflows/ci.yml
+-- .env.example
+-- docker-compose.yml
`-- README.md
```

## Run Locally

### Requirements

- Git
- Docker and Docker Compose
- Node.js 22+ for local VK Mini App development
- Telegram bot token for the Telegram interface
- OpenRouter API key or an available LiteLLM-compatible proxy

### 1. Clone and configure environment

```bash
git clone https://github.com/akiamuradev/evolution-tutor-bot.git
cd evolution-tutor-bot
cp .env.example .env
```

PowerShell alternative:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set at least:

```env
TG_BOT_TOKEN=...
BOT_USERNAME=@your_bot_username
OPENROUTER_API_KEY=...
POSTGRES_PASSWORD=...
DATABASE_URL=postgresql://tutor_user:your_password@postgres:5432/tutor_db
WEB_API_PORT=8080
```

For direct OpenRouter usage, remove or comment out `LITELLM_BASE_URL` and `LITELLM_API_KEY` in `.env`. The code falls back to `https://openrouter.ai/api/v1` only when `LITELLM_BASE_URL` is not set, and uses `OPENROUTER_API_KEY` only when `LITELLM_API_KEY` is not set.

If you use a LiteLLM-compatible proxy, provide `LITELLM_BASE_URL` and `LITELLM_API_KEY`. The current `docker-compose.yml` does not start a LiteLLM service.

### 2. Start backend services

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100 tutor-api
```

Health check:

```bash
curl http://localhost:8080/health
```

The Docker runtime starts:

- `tutor-bot` - Telegram polling process;
- `tutor-api` - HTTP API on `${WEB_API_PORT:-8080}`;
- `postgres` - PostgreSQL database with persistent `postgres_data` volume.

### 3. Run VK Mini App locally

```bash
cd frontend/vk-mini-app
npm ci
npm run dev
```

Vite starts on port `5173`. In local development, if `VITE_API_BASE_URL` is not set, frontend requests use relative `/api` paths and Vite proxies them to `http://localhost:8080`.

For deployment outside local Vite, set:

```env
VITE_API_BASE_URL=https://your-api-domain.example
```

### 4. Data needed for practice and RAG

Docker initializes database tables, but the public repository does not include a ready PostgreSQL dump with populated educational tasks. Practice and RAG depend on records in:

- `subjects`
- `fipi_tasks`

Related data-loading and maintenance code is present in:

- `backend/src/download_fipi_tasks.py`
- `backend/src/load_full_fipi_base.py`
- `backend/src/parsers/`
- `tools/fipi/`
- `tools/db/`

Some loaders assume the subject catalog already exists, so data loading should be verified against the current schema before using it as production seed data.

## Quality Checks

The public repository currently has CI checks, not a full automated test suite.

Local backend compile check:

```bash
python -m compileall -q backend/src
```

Local frontend build:

```bash
cd frontend/vk-mini-app
npm ci
npm run build
```

GitHub Actions runs the same kinds of checks on push to `main` and on pull requests.

## Configuration Notes

- `.env.example` documents Telegram, LLM, anti-spam, RAG, VK, PostgreSQL and YooKassa-related variables.
- `.env`, nested `.env` files, local DB files, logs, frontend builds and `node_modules` are ignored by `.gitignore`.
- API CORS is configured by `WEB_API_CORS_ORIGIN`.
- VK auth can use signed launch params via `VK_APP_SECRET`; development fallback flags are available through `WEB_API_ALLOW_UNSIGNED_VK_LAUNCH` and `WEB_API_ALLOW_INSECURE_USER_ID`.
- Nginx proxy template is in `docs/nginx_tutor_api.conf`.

## Current Repository State

- Implemented and wired as core paths: Telegram chat, HTTP API chat, VK Mini App chat/practice/profile/achievements, TutorEngine, LLM calls, RAG context builder, dialog memory, activity, achievements, PostgreSQL persistence, Docker Compose and CI checks.
- Not included in this public repo: production database dump and a dedicated unit/integration test suite.
- Some legacy or informational Telegram menu texts mention capabilities that are not promoted in this README because they are not fully wired in the current public code.

## Author Role and AI-Assisted Development

This repository is presented honestly as an AI-assisted portfolio project.

My role in the project:

- product decomposition: educational chatbot, practice flow, progress, memory, VK Mini App and API;
- backend architecture: async Python services, shared TutorEngine, API layer, Telegram layer and persistence model;
- AI orchestration: prompt context, model routing, fallbacks, guarded requests, memory and RAG integration;
- frontend integration: React/Vite VK Mini App connected to backend API;
- infrastructure: Docker Compose, environment configuration, GitHub-ready repository structure and CI checks;
- documentation and public repository preparation.

AI tools were used to accelerate implementation, refactoring and documentation. The engineering value shown here is not "manual typing speed", but the ability to design the product, decompose it into services, guide AI-generated code, verify repository facts, integrate components, identify outdated parts and package the result into a clear GitHub project.

## Skills Shown

- Async Python backend development.
- Telegram bot development with aiogram.
- HTTP API design with aiohttp.
- PostgreSQL schema design and async data access.
- LLM integration, prompt orchestration and model fallback handling.
- RAG/search pipeline over structured educational data.
- User memory and personalization patterns.
- Request throttling, AI concurrency control and cancellation handling.
- React/Vite frontend development for VK Mini App.
- Docker Compose based local/runtime setup.
- GitHub Actions CI configuration.
- Technical documentation and portfolio-oriented repository preparation.

---

## English

EVO:LUTION Tutor Bot is a multi-platform AI tutor for students. It includes a Telegram bot, an aiohttp HTTP API and a React/Vite VK Mini App backed by PostgreSQL, shared tutoring logic, LLM integration, task-based RAG, user memory, practice tasks, progress tracking and achievements.

**Portfolio project showcasing AI-assisted development, async Python backend, Telegram bot, aiohttp HTTP API, PostgreSQL, task-based RAG, React/Vite, VK Bridge and Docker.**

## What Is Implemented

- Telegram bot with onboarding, tutoring chat, practice tasks, explanations, stats, activity, achievements, study plan flow and graph generation.
- HTTP API for health, chat, profile, achievements, activity and practice.
- VK Mini App with chat, practice, achievements and profile tabs.
- Shared TutorEngine used by both Telegram and API clients.
- OpenRouter/LiteLLM-compatible AI client with model routing, fallback attempts and cache.
- RAG pipeline over a PostgreSQL task bank using query analysis, task search and local reranking.
- User memory based on recent dialog, searchable history and periodic profile summaries.
- PostgreSQL schema for users, tasks, progress, achievements, dialog memory and activity.
- Docker Compose runtime with bot, API and PostgreSQL.
- GitHub Actions CI for backend compile check and frontend build.

## Architecture

```mermaid
flowchart LR
    TG["Telegram Bot"] --> TE["TutorEngine"]
    VK["VK Mini App"] --> API["HTTP API"]
    API --> TE
    TE --> RAG["Task RAG"]
    TE --> MEM["User Memory"]
    RAG --> DB[(PostgreSQL)]
    MEM --> DB
    TE --> AI["AI Gateway"]
    AI --> LLM["OpenRouter / LiteLLM-compatible LLM"]
```

See also:

- [docs/bot_architecture.md](docs/bot_architecture.md)
- [docs/project_structure.md](docs/project_structure.md)
- [docs/nginx_tutor_api.conf](docs/nginx_tutor_api.conf)

## Quick Start

```bash
git clone https://github.com/akiamuradev/evolution-tutor-bot.git
cd evolution-tutor-bot
cp .env.example .env
```

Configure `.env`:

```env
TG_BOT_TOKEN=...
BOT_USERNAME=@your_bot_username
OPENROUTER_API_KEY=...
POSTGRES_PASSWORD=...
DATABASE_URL=postgresql://tutor_user:your_password@postgres:5432/tutor_db
WEB_API_PORT=8080
```

For direct OpenRouter usage, remove or comment out `LITELLM_BASE_URL` and `LITELLM_API_KEY`. The current Docker Compose file does not start a LiteLLM service.

Start services:

```bash
docker compose up -d --build
curl http://localhost:8080/health
```

Run VK Mini App locally:

```bash
cd frontend/vk-mini-app
npm ci
npm run dev
```

The public repository contains database schema and data-loading scripts, but does not include a ready production dump of educational tasks. Practice and RAG require populated `subjects` and `fipi_tasks` tables.

## Checks

```bash
python -m compileall -q backend/src
```

```bash
cd frontend/vk-mini-app
npm ci
npm run build
```

The current public repo has CI compile/build checks, but no dedicated unit or integration test suite.

## AI-Assisted Development

This is an AI-assisted portfolio project. AI tools helped speed up implementation, refactoring and documentation. The engineering work shown here is product decomposition, architecture decisions, integration of backend/API/frontend/database/LLM components, repository cleanup, factual documentation and GitHub-ready packaging.
