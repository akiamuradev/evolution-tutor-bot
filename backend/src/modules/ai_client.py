"""OpenRouter client with model routing, cache, and fallbacks."""
import logging
import os

import httpx

from .cache import ai_cache
from .model_router import (
    classify_question_complexity,
    get_fallback_models,
    get_max_tokens_for_complexity,
    get_timeout_for_complexity,
    select_model,
)

logger = logging.getLogger(__name__)

OPENROUTER_URL = os.getenv("LITELLM_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_KEY = os.getenv("LITELLM_API_KEY", os.getenv("OPENROUTER_API_KEY"))
RETRYABLE_STATUSES = {400, 408, 429, 500, 502, 503, 504}


def _normalize_messages(messages: list) -> list:
    allowed_roles = {"system", "user", "assistant"}
    normalized = []
    for message in messages:
        role = message.get("role", "user")
        content = str(message.get("content", "")).strip()
        if role not in allowed_roles:
            role = "user"
        if content:
            normalized.append({"role": role, "content": content})
    return normalized or [{"role": "user", "content": "Привет"}]


async def call_openrouter(
    messages: list,
    model: str = None,
    mode: str = "standard",
    question: str = "",
    timeout: int = None,
    max_tokens: int = None,
) -> str:
    """Call OpenRouter with automatic model selection and fallback retries."""
    messages = _normalize_messages(messages)
    if not question:
        question = next(
            (item["content"] for item in reversed(messages) if item["role"] == "user"),
            "",
        )

    complexity = classify_question_complexity(question)
    explicit_model = model is not None
    if model is None:
        model = select_model(mode, question)

    if timeout is None:
        timeout = get_timeout_for_complexity(complexity)
    if max_tokens is None:
        max_tokens = get_max_tokens_for_complexity(complexity)

    cached_response = ai_cache.get(messages, model)
    if cached_response:
        logger.info("AI cache hit: model=%s", model)
        return cached_response

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://evo-lution96.ru",
        "X-Title": "EVO:LUTION",
    }

    token_attempts = [max_tokens]
    if max_tokens > 2000:
        token_attempts.append(2000)

    model_attempts = [model]
    if not explicit_model:
        model_attempts.extend(get_fallback_models(model))

    client_timeout = httpx.Timeout(timeout, connect=30, read=max(30, timeout - 30))
    async with httpx.AsyncClient(timeout=client_timeout) as client:
        response = None
        last_error = ""
        used_model = model

        try:
            for attempt_model in model_attempts:
                used_model = attempt_model
                for attempt_tokens in token_attempts:
                    payload = {
                        "model": attempt_model,
                        "messages": messages,
                        "max_tokens": attempt_tokens,
                        "temperature": 0.7,
                    }
                    logger.info(
                        "OpenRouter request: model=%s complexity=%s max_tokens=%s messages=%s",
                        attempt_model,
                        complexity,
                        attempt_tokens,
                        len(messages),
                    )
                    response = await client.post(
                        f"{OPENROUTER_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                    if response.status_code == 200:
                        break

                    last_error = response.text[:500]
                    logger.error(
                        "OpenRouter error: status=%s model=%s body=%s",
                        response.status_code,
                        attempt_model,
                        last_error,
                    )
                    if response.status_code not in RETRYABLE_STATUSES:
                        return f"❌ Ошибка OpenRouter ({response.status_code})."

                if response is not None and response.status_code == 200:
                    break

            if response is None or response.status_code != 200:
                return f"❌ Ошибка OpenRouter: {last_error[:180]}"

            data = response.json()
            content = (
                data["choices"][0].get("message", {}).get("content", "").strip()
                if data.get("choices")
                else "❌ Пустой ответ."
            )
            ai_cache.set(messages, used_model, content)
            return content
        except Exception as e:
            logger.exception("OpenRouter exception")
            return f"❌ {str(e)[:100]}"
