# EVO:LUTION Tutor Bot

<p align="center">
  <img src="frontend/vk-mini-app/public/logo-light-theme.png" alt="EVO:LUTION Tutor Bot" width="180">
</p>

<p align="center">
  Мультиплатформенный AI-репетитор для школьников: Telegram-бот, HTTP API и VK Mini App с общим учебным ядром.<br>
  A multi-platform AI tutor with shared backend logic for Telegram and VK Mini App.
</p>

<p align="center">
  <a href="https://github.com/akiamuradev/evolution-tutor-bot/actions/workflows/ci.yml"><img src="https://github.com/akiamuradev/evolution-tutor-bot/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/aiogram-3.4.1-2CA5E0?logo=telegram&logoColor=white" alt="aiogram 3.4.1">
  <img src="https://img.shields.io/badge/aiohttp-3.9.1-2C5BB4" alt="aiohttp 3.9.1">
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" alt="React 18">
  <img src="https://img.shields.io/badge/VK_Bridge-3.0.2-0077FF?logo=vk&logoColor=white" alt="VK Bridge 3.0.2">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL 16">
  <img src="https://img.shields.io/badge/OpenRouter-LLM-111827" alt="OpenRouter">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker Compose">
</p>

<p align="center">
  <a href="#русский">Русский</a> | <a href="#english">English</a>
</p>

## Русский

### TL;DR

- EVO:LUTION Tutor Bot — AI-репетитор для Telegram и VK Mini App, а не простой wrapper вокруг чат-модели.
- Общий `TutorEngine` объединяет LLM, память ученика, RAG по базе заданий, прогресс и достижения.
- Backend построен на асинхронном Python, aiohttp и PostgreSQL; frontend — на React/Vite и VK Bridge.
- Проект запускается через Docker Compose и проверяется в GitHub Actions; production dump заданий и отдельный test suite в публичную версию не входят.

## О проекте

EVO:LUTION Tutor Bot помогает школьникам разбирать учебные вопросы, тренироваться на заданиях и отслеживать прогресс. Пользователь может общаться с репетитором в Telegram или VK Mini App, а оба интерфейса работают через единый `TutorEngine`.

Это не только оболочка над LLM. В проекте реализованы асинхронный Python backend, PostgreSQL, поиск по базе учебных заданий, память диалога, маршрутизация моделей, защита от спама и перегрузки, HTTP API и отдельный React-интерфейс.

## Возможности

- AI-репетитор с пошаговыми объяснениями и режимом подсказок.
- Telegram-бот на `aiogram` и VK Mini App на React/Vite.
- Практические задания с проверкой ответов и сохранением результатов.
- RAG-поиск по банку заданий в PostgreSQL с локальным reranking.
- Краткосрочная история диалога и долгосрочный профиль ученика.
- Статистика активности, прогресс, достижения и учебный план.
- Выбор fast, standard или reasoning модели по сложности запроса.
- OpenRouter API или совместимый LiteLLM proxy.
- Кэширование повторяющихся AI-ответов, rate limiting и контроль параллельных генераций.
- Построение графиков функций через SymPy, NumPy и Matplotlib.

## Архитектура

```mermaid
flowchart LR
    TG["Telegram Bot<br/>aiogram"] --> ENGINE["TutorEngine<br/>учебное ядро"]
    VK["VK Mini App<br/>React + VK Bridge"] --> API["HTTP API<br/>aiohttp"]
    API --> ENGINE
    ENGINE --> MEMORY["Память<br/>история + профиль"]
    ENGINE --> RAG["RAG<br/>поиск + reranking"]
    ENGINE --> GATEWAY["AI Gateway<br/>лимиты + model routing"]
    MEMORY --> DB[("PostgreSQL<br/>пользователи и прогресс")]
    RAG --> DB
    GATEWAY --> LLM["OpenRouter / LiteLLM"]
```

Основные компоненты:

| Компонент | Путь | Назначение |
|---|---|---|
| Telegram entrypoint | `backend/src/bot.py` | Запуск polling и подключение роутеров |
| HTTP API | `backend/src/web_api.py` | Backend для VK Mini App |
| TutorEngine | `backend/src/modules/tutor_engine.py` | Общая логика AI-репетитора |
| AI Gateway | `backend/src/modules/ai_gateway.py` | Очередь, ограничения и статистика запросов |
| AI client | `backend/src/modules/ai_client.py` | Работа с OpenRouter/LiteLLM и fallback-моделями |
| RAG | `backend/src/rag/` | Анализ запроса и поиск учебных заданий |
| Memory | `backend/src/modules/memory.py` | История диалога и профиль ученика |
| Database | `backend/src/database.py` | Асинхронный доступ к PostgreSQL |
| VK Mini App | `frontend/vk-mini-app/` | Интерфейс на React/Vite |

Подробности есть в [описании архитектуры](docs/bot_architecture.md) и [структуре проекта](docs/project_structure.md).

## Технологии

| Область | Стек |
|---|---|
| Backend | Python 3.11, aiogram, aiohttp, asyncpg, httpx |
| AI | OpenRouter-compatible API, LiteLLM-compatible proxy |
| Data | PostgreSQL 16, SQL, task-based RAG |
| Frontend | React 18, Vite, VK Bridge |
| Math | SymPy, NumPy, Matplotlib |
| Infrastructure | Docker Compose, Nginx, GitHub Actions |

## Быстрый запуск

Понадобятся Git, Docker с Docker Compose, Telegram bot token и ключ OpenRouter либо доступ к LiteLLM-compatible proxy.

### 1. Подготовьте окружение

```bash
git clone https://github.com/akiamuradev/evolution-tutor-bot.git
cd evolution-tutor-bot
cp .env.example .env
```

Для PowerShell:

```powershell
Copy-Item .env.example .env
```

Заполните в `.env` как минимум:

```env
TG_BOT_TOKEN=your-telegram-bot-token
BOT_USERNAME=@your_bot_username

OPENROUTER_API_KEY=your-openrouter-api-key

POSTGRES_USER=tutor_user
POSTGRES_PASSWORD=choose-a-password
POSTGRES_DB=tutor_db
DATABASE_URL=postgresql://tutor_user:choose-a-password@postgres:5432/tutor_db

WEB_API_PORT=8080
```

Для прямой работы с OpenRouter удалите или закомментируйте `LITELLM_BASE_URL` и `LITELLM_API_KEY`. Если они заданы, приложение считает LiteLLM основным провайдером. Сам LiteLLM в `docker-compose.yml` не запускается.

### 2. Запустите backend

```bash
docker compose up -d --build
docker compose ps
```

Будут запущены три сервиса:

- `tutor-bot` — Telegram polling;
- `tutor-api` — HTTP API на порту `8080`;
- `postgres` — PostgreSQL с постоянным volume `postgres_data`.

Проверка API:

```bash
curl http://localhost:8080/health
```

Логи:

```bash
docker compose logs -f --tail=100 tutor-bot tutor-api
```

Остановка:

```bash
docker compose down
```

### 3. Запустите VK Mini App

```bash
cd frontend/vk-mini-app
npm ci
npm run dev
```

Vite откроет приложение на `http://localhost:5173`. В режиме разработки запросы `/api` проксируются на `http://localhost:8080`.

Для внешнего API создайте `frontend/vk-mini-app/.env`:

```env
VITE_API_BASE_URL=https://api.example.com
```

## HTTP API

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/health` | Состояние API, базы, RAG и очереди AI |
| `POST` | `/api/chat` | Ответ AI-репетитора |
| `GET` | `/api/profile` | Профиль и сводка ученика |
| `GET` | `/api/achievements` | Достижения и прогресс |
| `GET` | `/api/activity` | Статистика активности |
| `GET` | `/api/practice/task` | Случайное практическое задание |
| `POST` | `/api/practice/answer` | Проверка и сохранение ответа |

VK-запросы могут авторизовываться через подписанные launch params. Для локальной разработки поведение настраивается переменными `WEB_API_ALLOW_UNSIGNED_VK_LAUNCH` и `WEB_API_ALLOW_INSECURE_USER_ID`.

## Учебные данные

Docker создаёт структуру базы, но публичный репозиторий не содержит production dump с готовым банком заданий. Практика и RAG требуют заполненных таблиц `subjects` и `fipi_tasks`.

Инструменты загрузки и обслуживания данных находятся в:

- `backend/src/parsers/`;
- `backend/src/download_fipi_tasks.py`;
- `backend/src/load_full_fipi_base.py`;
- `tools/fipi/` и `tools/db/`.

Перед production-использованием загрузчики следует проверить на соответствие актуальной схеме и правилам источников данных.

## Структура репозитория

```text
.
├── backend/
│   ├── database/          # начальная SQL-схема
│   └── src/
│       ├── api/           # HTTP handlers
│       ├── modules/       # AI, память, лимиты, TutorEngine
│       ├── rag/           # поиск по учебным заданиям
│       ├── routers/       # Telegram-сценарии
│       └── parsers/       # загрузка учебных данных
├── frontend/
│   └── vk-mini-app/       # React/Vite приложение
├── docs/                  # архитектура и конфигурация Nginx
├── tools/                 # служебные скрипты
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Проверки качества

Backend compile check:

```bash
python -m compileall -q backend/src
```

Frontend build:

```bash
cd frontend/vk-mini-app
npm ci
npm run build
```

Эти проверки выполняются в GitHub Actions при push в `main` и в pull request. Отдельного набора unit/integration-тестов в текущей версии репозитория нет.

## Ограничения текущей версии

- Для practice и RAG нужен отдельно подготовленный банк учебных заданий.
- Используется текстовый и метаданный поиск с локальным reranking; полноценный embedding search не подключён.
- VK Mini App запускается отдельно от backend-контейнеров.
- Перед публичным production-запуском необходимо запретить небезопасные dev-флаги авторизации, ограничить CORS и настроить HTTPS/reverse proxy.

## Лицензия

Проект распространяется по лицензии [MIT](LICENSE).

---

## English

### TL;DR

- EVO:LUTION Tutor Bot is an AI tutor for Telegram and VK Mini App, not a thin chat-model wrapper.
- A shared `TutorEngine` combines LLM calls, student memory, task-based RAG, progress tracking and achievements.
- The system uses an async Python/aiohttp/PostgreSQL backend and a React/Vite/VK Bridge frontend.
- Docker Compose and GitHub Actions are included; the public repository does not contain a production task dump or a dedicated test suite.

## About

EVO:LUTION Tutor Bot is a multi-platform educational assistant for students. Users can ask study questions, work through practice tasks and review their progress in Telegram or a VK Mini App. Both clients rely on the same backend tutoring core.

The repository goes beyond basic LLM integration. It includes an asynchronous Telegram layer, an aiohttp API, PostgreSQL persistence, dialog memory, task-based retrieval, model routing, anti-spam controls, AI concurrency limits and a separate React interface.

## Key Features

- Telegram onboarding, tutoring chat, practice flows, statistics, activity tracking and achievements.
- VK Mini App with chat, practice, achievements and profile sections.
- Shared `TutorEngine` for Telegram and HTTP API clients.
- OpenRouter-compatible LLM integration with optional LiteLLM proxy support.
- Fast, standard and reasoning model routing based on request complexity.
- Fallback models, reduced-token retries and an in-memory response cache.
- Dialog history, searchable memory and a long-term learning profile.
- RAG over a PostgreSQL task bank using query analysis, metadata search and local reranking.
- Anti-spam rules, global request limits and per-user generation control.
- Function graph generation with SymPy, NumPy and Matplotlib.

## Architecture

```mermaid
flowchart LR
    TG["Telegram Bot<br/>aiogram"] --> ENGINE["TutorEngine<br/>shared tutoring core"]
    VK["VK Mini App<br/>React + VK Bridge"] --> API["HTTP API<br/>aiohttp"]
    API --> ENGINE
    ENGINE --> MEMORY["Dialog memory<br/>history + profile"]
    ENGINE --> RAG["Task-based RAG<br/>search + reranking"]
    ENGINE --> GATEWAY["AI Gateway<br/>limits + model routing"]
    MEMORY --> DB[("PostgreSQL<br/>users and progress")]
    RAG --> DB
    GATEWAY --> LLM["OpenRouter / LiteLLM"]
```

See [architecture details](docs/bot_architecture.md) and the [project structure guide](docs/project_structure.md).

## Technology Stack

| Area | Technologies |
|---|---|
| Backend | Python 3.11, aiogram, aiohttp, asyncpg, httpx |
| AI | OpenRouter-compatible API, optional LiteLLM-compatible proxy |
| Data | PostgreSQL 16, SQL, task-based RAG |
| Frontend | React 18, Vite, VK Bridge |
| Math | SymPy, NumPy, Matplotlib |
| Infrastructure | Docker Compose, Nginx, GitHub Actions |

## Quick Start

Requirements: Git, Docker with Docker Compose, a Telegram bot token and either an OpenRouter API key or access to a LiteLLM-compatible proxy.

```bash
git clone https://github.com/akiamuradev/evolution-tutor-bot.git
cd evolution-tutor-bot
cp .env.example .env
```

Configure at least these variables in `.env`:

```env
TG_BOT_TOKEN=your-telegram-bot-token
BOT_USERNAME=@your_bot_username

OPENROUTER_API_KEY=your-openrouter-api-key

POSTGRES_USER=tutor_user
POSTGRES_PASSWORD=choose-a-password
POSTGRES_DB=tutor_db
DATABASE_URL=postgresql://tutor_user:choose-a-password@postgres:5432/tutor_db

WEB_API_PORT=8080
```

For direct OpenRouter access, remove or comment out `LITELLM_BASE_URL` and `LITELLM_API_KEY`. The current Compose file does not start a LiteLLM service.

Start the backend services:

```bash
docker compose up -d --build
docker compose ps
curl http://localhost:8080/health
```

Run the VK Mini App locally:

```bash
cd frontend/vk-mini-app
npm ci
npm run dev
```

Vite starts on `http://localhost:5173` and proxies local `/api` requests to `http://localhost:8080`.

## HTTP API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API, database, RAG and AI queue status |
| `POST` | `/api/chat` | Generate a tutor response |
| `GET` | `/api/profile` | Student profile and summary |
| `GET` | `/api/achievements` | Achievements and progress |
| `GET` | `/api/activity` | Activity statistics |
| `GET` | `/api/practice/task` | Retrieve a practice task |
| `POST` | `/api/practice/answer` | Check and store an answer |

VK requests can be authenticated using signed launch parameters. Development fallback behavior is controlled by `WEB_API_ALLOW_UNSIGNED_VK_LAUNCH` and `WEB_API_ALLOW_INSECURE_USER_ID`.

## Educational Data

Docker initializes the database schema, but the public repository does not include a production PostgreSQL dump with a populated task bank. Practice and RAG require data in the `subjects` and `fipi_tasks` tables.

Import and maintenance tools are located in `backend/src/parsers/`, `backend/src/download_fipi_tasks.py`, `backend/src/load_full_fipi_base.py`, `tools/fipi/` and `tools/db/`.

## Quality Checks

```bash
python -m compileall -q backend/src
```

```bash
cd frontend/vk-mini-app
npm ci
npm run build
```

GitHub Actions runs the same backend compile and frontend build checks on pushes to `main` and pull requests. The current public repository does not include a dedicated unit or integration test suite.

## Current Limitations

- Practice and RAG require a separately prepared educational task bank.
- Retrieval uses text and metadata search with local reranking; embedding search is not connected.
- The VK Mini App is started separately from the backend containers.
- Production deployment requires secure VK auth flags, restricted CORS, HTTPS and a reverse proxy.

## License

This project is distributed under the [MIT License](LICENSE).
