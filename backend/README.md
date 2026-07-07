# Backend

Python runtime for EVO:LUTION.

## Main Areas

- `src/bot.py` - Telegram bot entrypoint.
- `src/web_api.py` - HTTP API entrypoint for VK Mini App and future Web.
- `src/api/` - API app, routes, auth and HTTP helpers.
- `src/core/` - cross-cutting helpers such as env config parsing.
- `src/routers/` - Telegram-specific routers and callback handlers.
- `src/modules/` - platform-neutral tutoring logic, AI client, anti-spam, memory and model routing.
- `src/modules/tutor_intent.py` - shared intent detection for concept explanations vs guided task solving.
- `src/rag/` - retrieval, task search and future Tutor-RAG work.
- `database/` - SQL initialization and local database artifacts.

## Local Checks

From repository root:

```powershell
python -m compileall -q backend/src
```

## Runtime

Docker still runs modules as `src.*`:

```bash
python -m src.bot
python -m src.web_api
```

This works because Docker copies/mounts `backend/src` to `/app/src`.

## Team Rules

- Keep Telegram objects inside `src/routers/`.
- Keep generic runtime helpers inside `src/core/`.
- Keep reusable learning logic inside `src/modules/`.
- Route ordinary Telegram/VK/Web chat generation through `src/modules/tutor_engine.py`.
- Keep API-only behavior inside `src/api/`.
- Keep retrieval logic inside `src/rag/`.
- Do not put frontend code, API keys or local artifacts here.
