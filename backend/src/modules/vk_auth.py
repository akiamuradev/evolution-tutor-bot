"""VK Mini App launch parameters verification."""
import base64
import hashlib
import hmac
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode


@dataclass
class VkAuthResult:
    ok: bool
    user_id: int | None = None
    error: str = ""


def _normalize_launch_params(raw: str | dict | None) -> dict[str, str]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(key): str(value) for key, value in raw.items() if value is not None}

    query = str(raw).strip()
    if query.startswith("?"):
        query = query[1:]
    return dict(parse_qsl(query, keep_blank_values=True))


def get_unsigned_vk_user_id(raw_params: str | dict | None) -> int | None:
    params = _normalize_launch_params(raw_params)
    try:
        user_id = int(params.get("vk_user_id", "0"))
    except ValueError:
        return None
    return user_id if user_id > 0 else None


def _sign_vk_params(params: dict[str, str], secret: str) -> str:
    signed_params = {
        key: value
        for key, value in params.items()
        if key.startswith("vk_")
    }
    query = urlencode(sorted(signed_params.items()), doseq=True)
    digest = hmac.new(secret.encode(), query.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def verify_vk_launch_params(
    raw_params: str | dict | None,
    secret: str | None,
    max_age_seconds: int = 86400,
) -> VkAuthResult:
    params = _normalize_launch_params(raw_params)
    if not params:
        return VkAuthResult(ok=False, error="vk_launch_params_required")
    if not secret:
        return VkAuthResult(ok=False, error="vk_app_secret_required")

    received_sign = params.get("sign")
    if not received_sign:
        return VkAuthResult(ok=False, error="vk_sign_required")

    expected_sign = _sign_vk_params(params, secret)
    if not hmac.compare_digest(received_sign, expected_sign):
        return VkAuthResult(ok=False, error="vk_invalid_sign")

    try:
        user_id = int(params.get("vk_user_id", "0"))
    except ValueError:
        return VkAuthResult(ok=False, error="vk_user_id_invalid")
    if user_id <= 0:
        return VkAuthResult(ok=False, error="vk_user_id_required")

    try:
        timestamp = int(params.get("vk_ts", "0"))
    except ValueError:
        return VkAuthResult(ok=False, error="vk_ts_invalid")
    if timestamp <= 0:
        return VkAuthResult(ok=False, error="vk_ts_required")

    if max_age_seconds > 0 and abs(int(time.time()) - timestamp) > max_age_seconds:
        return VkAuthResult(ok=False, error="vk_launch_params_expired")

    return VkAuthResult(ok=True, user_id=user_id)
