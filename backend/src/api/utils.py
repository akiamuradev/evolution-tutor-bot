"""Shared helpers for HTTP API handlers."""
from typing import Any

from aiohttp import web

from ..core.config import env_bool, env_str


def json_response(data: dict[str, Any], status: int = 200) -> web.Response:
    return web.json_response(data, status=status, headers={
        "Access-Control-Allow-Origin": env_str("WEB_API_CORS_ORIGIN", "*"),
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    })


def error_response(message: str, status: int = 400, **extra: Any) -> web.Response:
    return json_response({"ok": False, "error": message, **extra}, status=status)
