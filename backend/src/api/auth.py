"""Authentication helpers for HTTP API clients."""
from typing import Any

from ..core.config import env_bool, env_int, env_str
from ..modules.vk_auth import get_unsigned_vk_user_id, verify_vk_launch_params


def _get_user_id(payload: dict[str, Any]) -> int | None:
    raw_user_id = payload.get("user_id")
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return None
    return user_id if user_id > 0 else None


def get_authenticated_user_id(payload: dict[str, Any]) -> tuple[int | None, str]:
    auth = verify_vk_launch_params(
        payload.get("launch_params"),
        env_str("VK_APP_SECRET"),
        max_age_seconds=env_int("VK_LAUNCH_PARAMS_MAX_AGE_SECONDS", 86400, minimum=1),
    )
    if auth.ok:
        return auth.user_id, "vk"

    if env_bool("WEB_API_ALLOW_UNSIGNED_VK_LAUNCH", False):
        user_id = get_unsigned_vk_user_id(payload.get("launch_params"))
        if user_id is not None:
            return user_id, "vk_unsigned"

    if env_bool("WEB_API_ALLOW_INSECURE_USER_ID", False):
        user_id = _get_user_id(payload)
        if user_id is not None:
            return user_id, "dev"

    return None, auth.error
