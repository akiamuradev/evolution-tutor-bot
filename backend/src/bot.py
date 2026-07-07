"""Telegram bot entrypoint."""
import asyncio
import contextlib
import logging
import os

import asyncpg
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession

from .rag import TaskSearch, TrendAnalyzer
from .services import dp, db, services
from .modules.anti_spam import AntiSpamMiddleware

# Keep this order close to the original monolithic bot.py.
from .routers import (
    exam,
    main,
    documents,
    legal,
    settings,
    practice,
    achievements,
    activity,
    stats,
    study_plan,
    generation,
    messages,
    menu_callbacks,
    practice_subjects,
)

logger = logging.getLogger(__name__)

ROUTERS = [
    exam.router,
    main.router,
    documents.router,
    legal.router,
    settings.router,
    practice.router,
    achievements.router,
    activity.router,
    stats.router,
    study_plan.router,
    generation.router,
    messages.router,
    menu_callbacks.router,
    practice_subjects.router,
]
_routers_included = False
_middlewares_included = False


def include_middlewares():
    global _middlewares_included
    if _middlewares_included:
        return
    anti_spam_middleware = AntiSpamMiddleware()
    dp.message.middleware(anti_spam_middleware)
    dp.callback_query.middleware(anti_spam_middleware)
    _middlewares_included = True


def include_routers():
    global _routers_included
    if _routers_included:
        return
    for router in ROUTERS:
        dp.include_router(router)
    _routers_included = True


async def cleanup_old_sessions_loop():
    while True:
        await asyncio.sleep(3600)
        try:
            await db.cleanup_old_sessions()
        except Exception:
            logger.exception("Failed to cleanup old user sessions")


async def start():
    logger.info("Starting EVO:LUTION bot v23.0 with RAG")
    if not all([os.getenv("TG_BOT_TOKEN"), os.getenv("DATABASE_URL"), os.getenv("OPENROUTER_API_KEY")]):
        logger.error("Required environment variables are missing")
        return

    await db.init()
    services.db_pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    services.task_search = TaskSearch(services.db_pool)
    services.trend_analyzer = TrendAnalyzer(services.db_pool)
    logger.info("RAG services initialized")

    session = AiohttpSession(proxy=os.getenv("TG_PROXY_URL")) if os.getenv("TG_PROXY_URL") else AiohttpSession()
    services.bot = Bot(token=os.getenv("TG_BOT_TOKEN"), session=session)
    include_middlewares()
    include_routers()
    cleanup_task = asyncio.create_task(cleanup_old_sessions_loop())
    logger.info("Polling started")

    try:
        await dp.start_polling(services.bot, skip_updates=True)
    finally:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        await db.cleanup_old_sessions()
        await session.close()
        if services.db_pool:
            await services.db_pool.close()


if __name__ == "__main__":
    asyncio.run(start())
