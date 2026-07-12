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

**Портфолио-проект, показывающий разработку с AI-assisted подходом, async Python backend, Telegram bot, aiohttp HTTP API, PostgreSQL, task-based RAG, React/Vite, VK Bridge и Docker.**

## О проекте

EVO:LUTION Tutor Bot предназначен для школьников, которым нужен помощник по учебным темам, домашним заданиям и подготовке к экзаменам. Основной пользовательский сценарий: ученик открывает Telegram-бота или VK Mini App, задает вопрос или берет тренировочное задание, получает пошаговое объяснение, отправляет ответ, а система сохраняет прогресс и использует историю дальше.

Проект показывает, как собрать образовательного AI-ассистента как полноценную backend-систему: с API, базой данных, памятью, поиском по учебным материалам, клиентским интерфейсом и инфраструктурой запуска.

## Ключевые возможности

### AI и RAG

- LLM-интеграция через OpenRouter-compatible endpoint; также поддерживается LiteLLM-compatible proxy через `LITELLM_BASE_URL` и `LITELLM_API_KEY`.
- Model routing в `backend/src/modules/model_router.py`: выбор fast/standard/reasoning модели по эвристике сложности вопроса.
- Fallback-попытки в `backend/src/modules/ai_client.py`: повторные запросы к альтернативным моделям и уменьшение `max_tokens` для retryable HTTP-статусов.
- Общий AI Gateway в `backend/src/modules/ai_gateway.py`: guarded-вызовы модели, статистика, busy-response и контроль активных генераций.
- In-memory LRU cache для повторяющихся AI-ответов.
- TutorEngine в `backend/src/modules/tutor_engine.py`: общий слой генерации ответов для Telegram и HTTP API.
- Память пользователя: последние сообщения, searchable dialog memory, долгосрочный summary и learning profile в таблицах `ai_dialog_messages` и `ai_memory_profiles`.
- RAG-пайплайн в `backend/src/rag/`: анализ запроса, определение предмета/номера задания, поиск кандидатов в PostgreSQL, локальный reranking и добавление компактного контекста в prompt.
- Важно: текущий production RAG в публичном коде использует текстовый/метаданный поиск и локальный reranking по базе заданий. Векторный embedding search не является подтвержденной рабочей частью текущей схемы.

### Учебный опыт

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

### Платформы и интерфейсы

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

### Инженерная часть

- Async Python stack: `aiogram`, `aiohttp`, `asyncpg`, `httpx`.
- PostgreSQL как основное хранилище пользователей, заданий, прогресса, достижений, памяти и активности.
- Индексы базы данных для поиска заданий, прогресса, достижений, сессий и памяти диалога.
- Docker Compose runtime с тремя сервисами: `tutor-bot`, `tutor-api`, `postgres`.
- PostgreSQL image: `pgvector/pgvector:pg16`; текущий публичный retrieval code не использует vector embeddings.
- Anti-spam и rate limiting в `backend/src/modules/anti_spam.py`.
- AI concurrency guard в `backend/src/modules/request_guard.py`.
- Реестр отмены генераций по пользователям в `backend/src/modules/generation_control.py`.
- GitHub Actions CI:
  - compile check backend на Python 3.11;
  - сборка frontend на Node 22 через `npm run build`.
- Гигиена публичного репозитория: `.env` игнорируется, `.env.example` включен, сборочные артефакты и локальные файлы базы не попадают в Git.

## Пример пользовательского сценария

1. Пользователь открывает Telegram bot или VK Mini App.
2. В Telegram пользователь принимает обработку данных и выбирает диапазон класса; в VK Mini App пользователь определяется через launch params.
3. Пользователь задает учебный вопрос или запрашивает практическое задание.
4. Backend выполняет проверки авторизации и лимитов, затем передает запрос в TutorEngine.
5. TutorEngine собирает контекст из system prompt, недавнего диалога, долгосрочной памяти и, когда это полезно, RAG-поиска по `fipi_tasks`.
6. AI Gateway отправляет guarded-запрос в настроенную OpenRouter/LiteLLM-compatible model.
7. Ответ возвращается пользователю; память диалога, активность, прогресс и достижения обновляются в PostgreSQL.

## Архитектура

Подробные документы по архитектуре:

- [docs/bot_architecture.md](docs/bot_architecture.md)
- [docs/bot_architecture.html](docs/bot_architecture.html)
- [docs/project_structure.md](docs/project_structure.md)

```mermaid
flowchart LR
    TG["Telegram Bot<br/>aiogram"] --> TE["TutorEngine<br/>общее учебное ядро"]
    VK["VK Mini App<br/>React/Vite/VK Bridge"] --> API["HTTP API<br/>aiohttp"]
    API --> TE
    TE --> MEM["Память диалога<br/>ai_dialog_messages<br/>ai_memory_profiles"]
    TE --> RAG["Tutor-RAG<br/>анализ запроса + reranking задач"]
    RAG --> DB[(PostgreSQL)]
    MEM --> DB
    TE --> GATE["AI Gateway<br/>queue + guarded calls"]
    GATE --> LLM["OpenRouter / LiteLLM-compatible LLM"]
    API --> DB
    TG --> DB
```

### Основные компоненты

| Компонент | Путь | Назначение |
|---|---|---|
| Telegram entrypoint | `backend/src/bot.py` | Запускает bot polling, инициализирует DB/RAG-сервисы, подключает routers и anti-spam middleware. |
| HTTP API entrypoint | `backend/src/web_api.py` | Запускает aiohttp API для VK Mini App и будущих web-клиентов. |
| API routes | `backend/src/api/routes.py` | Endpoints для health, profile, achievements, activity, chat и practice. |
| TutorEngine | `backend/src/modules/tutor_engine.py` | Платформенно-независимая генерация ответов репетитора. |
| AI client | `backend/src/modules/ai_client.py` | Вызовы OpenRouter/LiteLLM-compatible API, выбор модели, повторные попытки и cache. |
| RAG | `backend/src/rag/` | Анализ учебного запроса, поиск и reranking заданий по данным PostgreSQL. |
| Memory | `backend/src/modules/memory.py` | Контекст памяти пользователя и периодическая суммаризация профиля. |
| Database | `backend/src/database.py`, `backend/database/init.sql` | Runtime schema, migrations-by-code и начальная SQL-схема. |
| VK Mini App | `frontend/vk-mini-app/` | React/Vite frontend с вкладками чата, практики, достижений и профиля. |
| Docs | `docs/` | Архитектура, структура проекта, Nginx config и юридические документы. |

## Технологический стек

| Область | Технологии |
|---|---|
| Backend | Python 3.11, aiogram, aiohttp, asyncpg, httpx |
| AI | OpenRouter-compatible API, опциональный LiteLLM-compatible proxy, prompt orchestration |
| RAG/Search | Банк заданий в PostgreSQL, text/metadata search, локальный reranking |
| Database | PostgreSQL, pgvector image, SQL schema, async data access |
| Frontend | React 18, Vite, VK Bridge |
| DevOps | Docker Compose, GitHub Actions, Nginx config |
| Обработка данных | FIPI/Sdamgia/Math100 parsers и maintenance scripts |
| Documents/Math tools | python-docx, reportlab, SymPy, NumPy, Matplotlib |

## Структура репозитория

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

## Локальный запуск

### Требования

- Git
- Docker и Docker Compose
- Node.js 22+ для локальной разработки VK Mini App
- Telegram bot token для Telegram-интерфейса
- OpenRouter API key или доступный LiteLLM-compatible proxy

### 1. Клонировать репозиторий и настроить окружение

```bash
git clone https://github.com/akiamuradev/evolution-tutor-bot.git
cd evolution-tutor-bot
cp .env.example .env
```

Альтернатива для PowerShell:

```powershell
Copy-Item .env.example .env
```

Отредактируйте `.env` и задайте минимум:

```env
TG_BOT_TOKEN=...
BOT_USERNAME=@your_bot_username
OPENROUTER_API_KEY=...
POSTGRES_PASSWORD=...
DATABASE_URL=postgresql://tutor_user:your_password@postgres:5432/tutor_db
WEB_API_PORT=8080
```

Для прямого использования OpenRouter удалите или закомментируйте `LITELLM_BASE_URL` и `LITELLM_API_KEY` в `.env`. Код использует `https://openrouter.ai/api/v1` только если `LITELLM_BASE_URL` не задан, а `OPENROUTER_API_KEY` используется только если не задан `LITELLM_API_KEY`.

Если используется LiteLLM-compatible proxy, задайте `LITELLM_BASE_URL` и `LITELLM_API_KEY`. Текущий `docker-compose.yml` не поднимает отдельный LiteLLM service.

### 2. Запустить backend-сервисы

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f --tail=100 tutor-api
```

Проверка health endpoint:

```bash
curl http://localhost:8080/health
```

Docker runtime запускает:

- `tutor-bot` - процесс Telegram polling;
- `tutor-api` - HTTP API на `${WEB_API_PORT:-8080}`;
- `postgres` - база PostgreSQL с постоянным volume `postgres_data`.

### 3. Запустить VK Mini App локально

```bash
cd frontend/vk-mini-app
npm ci
npm run dev
```

Vite запускается на порту `5173`. При локальной разработке, если `VITE_API_BASE_URL` не задан, frontend использует относительные пути `/api`, а Vite проксирует их на `http://localhost:8080`.

Для запуска вне локального Vite задайте:

```env
VITE_API_BASE_URL=https://your-api-domain.example
```

### 4. Данные для practice и RAG

Docker инициализирует таблицы базы данных, но публичный репозиторий не содержит готовый PostgreSQL dump с заполненными учебными заданиями. Practice и RAG зависят от записей в:

- `subjects`
- `fipi_tasks`

Связанный код для загрузки и обслуживания данных находится здесь:

- `backend/src/download_fipi_tasks.py`
- `backend/src/load_full_fipi_base.py`
- `backend/src/parsers/`
- `tools/fipi/`
- `tools/db/`

Часть loaders предполагает, что справочник предметов уже существует, поэтому загрузку данных нужно сверять с текущей схемой перед использованием как production seed data.

## Проверки качества

В публичном репозитории сейчас есть CI-проверки, но нет полноценного автоматизированного набора тестов.

Локальная compile check для backend:

```bash
python -m compileall -q backend/src
```

Локальная сборка frontend:

```bash
cd frontend/vk-mini-app
npm ci
npm run build
```

GitHub Actions запускает такие же проверки при push в `main` и pull request.

## Заметки по конфигурации

- `.env.example` описывает переменные для Telegram, LLM, anti-spam, RAG, VK, PostgreSQL и YooKassa.
- `.env`, вложенные `.env`-файлы, локальные DB-файлы, logs, frontend builds и `node_modules` игнорируются через `.gitignore`.
- API CORS настраивается через `WEB_API_CORS_ORIGIN`.
- VK auth может использовать подписанные launch params через `VK_APP_SECRET`; fallback-флаги для разработки доступны через `WEB_API_ALLOW_UNSIGNED_VK_LAUNCH` и `WEB_API_ALLOW_INSECURE_USER_ID`.
- Шаблон Nginx proxy лежит в `docs/nginx_tutor_api.conf`.

## Текущее состояние репозитория

- Реализованы и подключены как основные пути: чат в Telegram, чат через HTTP API, разделы chat/practice/profile/achievements во VK Mini App, TutorEngine, вызовы LLM, сборщик RAG-контекста, память диалога, учет активности, достижения, сохранение данных в PostgreSQL, Docker Compose и CI-проверки.
- В публичный репозиторий не включены: production-дамп базы данных и отдельный unit/integration test suite.
- Некоторые legacy или информационные тексты Telegram-меню упоминают возможности, которые не вынесены в этот README, потому что они не полностью связаны в текущем публичном коде.

## Роль автора и AI-assisted development

Этот репозиторий честно представлен как портфолио-проект с AI-assisted разработкой.

Моя роль в проекте:

- декомпозиция продукта: образовательный chatbot, сценарий практики, прогресс, память, VK Mini App и API;
- архитектура backend: async Python services, общий TutorEngine, API layer, Telegram layer и persistence model;
- AI orchestration: prompt context, model routing, fallbacks, guarded requests, память и RAG integration;
- интеграция frontend: React/Vite VK Mini App, подключенный к backend API;
- инфраструктура: Docker Compose, настройка environment, GitHub-ready структура репозитория и CI-проверки;
- документация и подготовка публичного репозитория.

AI tools использовались для ускорения реализации, рефакторинга и документации. Инженерная ценность здесь не в "скорости ручного набора кода", а в умении спроектировать продукт, разложить его на сервисы, направлять код, сгенерированный AI, проверять факты репозитория, интегрировать компоненты, находить устаревшие части и упаковывать результат в понятный GitHub-проект.

## Навыки, показанные в проекте

- Разработка async Python backend.
- Разработка Telegram bot на aiogram.
- Проектирование HTTP API на aiohttp.
- Проектирование PostgreSQL schema и async data access.
- Интеграция LLM, prompt orchestration и обработка model fallback.
- RAG/search pipeline поверх структурированных образовательных данных.
- User memory и personalization patterns.
- Request throttling, AI concurrency control и обработка отмены генераций.
- React/Vite frontend development для VK Mini App.
- Настройка local/runtime окружения на Docker Compose.
- Настройка GitHub Actions CI.
- Техническая документация и подготовка репозитория под портфолио.

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
