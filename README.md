# EVO:LUTION Tutor Bot

[Русский](#русский) | [English](#english)

## Русский

### О проекте

EVO:LUTION Tutor Bot - учебный AI-репетитор для школьников. Проект объединяет Telegram-бота, HTTP API для VK Mini App, React/Vite фронтенд, PostgreSQL-хранилище, поиск по базе задач и интеграцию с OpenRouter.

Это публичная портфолио-версия проекта: без секретов, локальных баз данных, `node_modules`, frontend-сборки и служебных файлов разработки.

### Что демонстрирует проект

- Асинхронный Python backend на `aiogram`, `aiohttp`, `asyncpg` и `asyncio`.
- Архитектуру Telegram-бота с роутерами, middleware, FSM-сценариями и callback-меню.
- Общий tutoring engine, который переиспользуется Telegram-ботом и HTTP API.
- Интеграцию с OpenRouter/LiteLLM-compatible API.
- Маршрутизацию AI-моделей, fallback-логику, LRU-кеш и контроль конкурентных AI-запросов.
- Tutor-RAG слой поверх PostgreSQL-базы задач.
- Учебную память, историю диалогов, профиль ученика и персонализацию ответов.
- Практику задач, проверку ответов, достижения, активность и статистику.
- React/Vite VK Mini App с чатом, практикой, профилем, достижениями и темами оформления.
- Docker Compose окружение для bot/API/PostgreSQL.
- Парсеры и maintenance tools для образовательных данных ФИПИ/Sdamgia/Math100.

### Архитектура

```text
Telegram user
  -> tutor-bot
  -> TutorEngine
  -> Memory + Tutor-RAG
  -> AI Gateway
  -> OpenRouter
  -> Telegram response

VK Mini App user
  -> React/Vite frontend
  -> tutor-api
  -> TutorEngine
  -> same Memory, RAG, AI and PostgreSQL layers
```

### Структура репозитория

```text
.
|-- backend/                  # Python backend: bot, API, tutor engine, RAG, database
|   |-- src/
|   |   |-- bot.py            # Telegram entrypoint
|   |   |-- web_api.py        # HTTP API entrypoint
|   |   |-- api/              # aiohttp routes and auth
|   |   |-- modules/          # shared AI/tutor/business logic
|   |   |-- rag/              # retrieval and query analysis
|   |   |-- routers/          # Telegram handlers
|   |   `-- parsers/          # educational task parsers
|   |-- database/init.sql
|   |-- Dockerfile
|   `-- requirements.txt
|-- frontend/vk-mini-app/     # React/Vite VK Mini App
|-- docs/                     # architecture, project structure, legal/deploy notes
|-- tools/                    # data and database maintenance scripts
|-- docker-compose.yml
`-- .env.example
```

### Стек

Backend:

- Python 3.11
- aiogram 3
- aiohttp
- asyncpg
- httpx
- PostgreSQL / pgvector image
- OpenRouter или LiteLLM-compatible endpoint
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
- GitHub Actions CI

### Переменные окружения

Скопируйте шаблон:

```bash
cp .env.example .env
```

Заполните свои значения:

```env
TG_BOT_TOKEN=
OPENROUTER_API_KEY=
DATABASE_URL=
POSTGRES_PASSWORD=
VK_APP_SECRET=
```

Не коммитьте `.env`, дампы баз данных, `node_modules`, `dist`, логи и локальную диагностику.

### Запуск через Docker

```bash
docker compose up -d --build
docker compose logs -f --tail=100 tutor-bot
curl http://localhost:8080/health
```

Сервисы:

- `tutor-bot` запускает `python -m src.bot`.
- `tutor-api` запускает `python -m src.web_api`.
- `postgres` хранит пользователей, задачи, память, прогресс и достижения.

### Локальная проверка backend

```bash
python -m compileall -q backend/src
```

### Локальный запуск VK Mini App

```bash
cd frontend/vk-mini-app
npm install
npm run dev
```

Vite dev server проксирует `/api` и `/health` на `http://localhost:8080`.

### Сборка frontend

```bash
cd frontend/vk-mini-app
npm run build
```

### Документация

- `docs/bot_architecture.html` - визуальная архитектура для портфолио.
- `docs/bot_architecture.md` - краткое описание архитектуры.
- `docs/project_structure.md` - структура проекта.
- `docs/nginx_tutor_api.conf` - пример Nginx reverse proxy.

---

## English

### About

EVO:LUTION Tutor Bot is an educational AI tutor for school students. The project combines a Telegram bot, an HTTP API for VK Mini App, a React/Vite frontend, PostgreSQL storage, task search/RAG and OpenRouter integration.

This is a public portfolio version of the project: no secrets, local database dumps, `node_modules`, frontend build output or local development artifacts are included.

### What The Project Demonstrates

- Async Python backend with `aiogram`, `aiohttp`, `asyncpg` and `asyncio`.
- Telegram bot architecture with routers, middleware, FSM flows and callback menus.
- Shared tutoring engine reused by the Telegram bot and HTTP API.
- OpenRouter/LiteLLM-compatible AI integration.
- AI model routing, fallback logic, LRU cache and guarded AI concurrency.
- Tutor-RAG layer over a PostgreSQL task bank.
- Learning memory, dialog history, student profile and personalized answers.
- Practice tasks, answer checking, achievements, activity tracking and statistics.
- React/Vite VK Mini App with chat, practice, profile, achievements and theme support.
- Docker Compose runtime for bot/API/PostgreSQL.
- Parsers and maintenance tools for FIPI/Sdamgia/Math100 educational data.

### Architecture

```text
Telegram user
  -> tutor-bot
  -> TutorEngine
  -> Memory + Tutor-RAG
  -> AI Gateway
  -> OpenRouter
  -> Telegram response

VK Mini App user
  -> React/Vite frontend
  -> tutor-api
  -> TutorEngine
  -> same Memory, RAG, AI and PostgreSQL layers
```

### Repository Structure

```text
.
|-- backend/                  # Python backend: bot, API, tutor engine, RAG, database
|   |-- src/
|   |   |-- bot.py            # Telegram entrypoint
|   |   |-- web_api.py        # HTTP API entrypoint
|   |   |-- api/              # aiohttp routes and auth
|   |   |-- modules/          # shared AI/tutor/business logic
|   |   |-- rag/              # retrieval and query analysis
|   |   |-- routers/          # Telegram handlers
|   |   `-- parsers/          # educational task parsers
|   |-- database/init.sql
|   |-- Dockerfile
|   `-- requirements.txt
|-- frontend/vk-mini-app/     # React/Vite VK Mini App
|-- docs/                     # architecture, project structure, legal/deploy notes
|-- tools/                    # data and database maintenance scripts
|-- docker-compose.yml
`-- .env.example
```

### Tech Stack

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
- Responsive CSS with light/dark themes

Infrastructure:

- Docker
- Docker Compose
- Nginx reverse proxy example
- GitHub Actions CI

### Environment

Copy the template:

```bash
cp .env.example .env
```

Fill in your own values:

```env
TG_BOT_TOKEN=
OPENROUTER_API_KEY=
DATABASE_URL=
POSTGRES_PASSWORD=
VK_APP_SECRET=
```

Never commit `.env`, database dumps, `node_modules`, `dist`, logs or local diagnostics.

### Run With Docker

```bash
docker compose up -d --build
docker compose logs -f --tail=100 tutor-bot
curl http://localhost:8080/health
```

Services:

- `tutor-bot` runs `python -m src.bot`.
- `tutor-api` runs `python -m src.web_api`.
- `postgres` stores users, tasks, memory, progress and achievements.

### Backend Check

```bash
python -m compileall -q backend/src
```

### Run VK Mini App Locally

```bash
cd frontend/vk-mini-app
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/health` to `http://localhost:8080`.

### Frontend Build

```bash
cd frontend/vk-mini-app
npm run build
```

### Documentation

- `docs/bot_architecture.html` - visual portfolio architecture.
- `docs/bot_architecture.md` - short architecture description.
- `docs/project_structure.md` - project structure.
- `docs/nginx_tutor_api.conf` - Nginx reverse proxy example.
