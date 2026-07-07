"""HTTP API application factory."""
import asyncio
import contextlib
import logging

import asyncpg
from aiohttp import web

from ..core.config import env_str, env_int
from ..rag import TaskSearch, TrendAnalyzer
from ..services import db, services
from .routes import setup_routes

logger = logging.getLogger(__name__)


async def cleanup_old_sessions_loop() -> None:
    while True:
        await asyncio.sleep(3600)
        try:
            await db.cleanup_old_sessions()
        except Exception:
            logger.exception("Failed to cleanup old user sessions")


async def init_app() -> web.Application:
    logging.basicConfig(level=env_str("LOG_LEVEL", "INFO"))
    required = ["DATABASE_URL", "OPENROUTER_API_KEY"]
    missing = [name for name in required if not env_str(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    await db.init()
    services.db_pool = await asyncpg.create_pool(env_str("DATABASE_URL"))
    services.task_search = TaskSearch(services.db_pool)
    services.trend_analyzer = TrendAnalyzer(services.db_pool)

    app = web.Application(client_max_size=1024 * 1024)
    setup_routes(app)

    cleanup_task = asyncio.create_task(cleanup_old_sessions_loop())

    async def close_services(_: web.Application) -> None:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task
        await db.cleanup_old_sessions()
        await db.pool.close()
        if services.db_pool:
            await services.db_pool.close()

    app.on_cleanup.append(close_services)
    return app


def main() -> None:
    port = env_int("WEB_API_PORT", 8080, minimum=1)
    web.run_app(init_app(), host="0.0.0.0", port=port)
