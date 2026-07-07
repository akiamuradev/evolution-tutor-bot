"""Shared tutoring engine for Telegram, VK Mini App, and web clients."""
import asyncio
import logging
from dataclasses import dataclass

from ..helpers import get_user_grade
from ..services import db, task_search
from ..rag import build_tutor_rag_context
from .ai_gateway import call_openrouter_guarded
from .memory import build_memory_context, maybe_update_memory_profile
from .prompts import get_schoolboy_system_prompt
from .tutor_intent import (
    build_guided_task_response,
    build_tutor_policy_context,
    should_force_guided_mode,
)
from .utils import force_clean_text

logger = logging.getLogger(__name__)


@dataclass
class TutorEngineResult:
    text: str
    guided: bool = False
    used_rag: bool = False
    rag_confidence: float = 0.0
    rag_tasks: int = 0
    busy: bool = False


async def build_dialog_messages(user_id: int, grade: str, user_text: str, extra_context: str = "") -> list[dict]:
    history = await db.get_dialog_context(user_id, limit=8)
    memory_context = await build_memory_context(user_id, user_text)
    tutor_policy_context = build_tutor_policy_context(user_text, history)
    user_content = user_text
    if extra_context:
        user_content = (
            f"{user_text}\n\n"
            "Контекст из базы задач, если он полезен для ответа:\n"
            f"{extra_context}"
        )

    messages = [{"role": "system", "content": get_schoolboy_system_prompt(grade)}]
    if memory_context:
        messages.append({"role": "system", "content": memory_context})
    if tutor_policy_context:
        messages.append({"role": "system", "content": tutor_policy_context})
    messages.extend(history)
    messages.append({"role": "user", "content": user_content})
    return messages


async def generate_tutor_response(user_id: int, user_text: str, grade: str | None = None) -> TutorEngineResult:
    """Generate a tutor response without binding to a specific platform."""
    user_text = (user_text or "").strip()
    if not user_text:
        return TutorEngineResult(text="", guided=False, used_rag=False)

    if grade is None:
        user = await db.get_user(user_id)
        grade = get_user_grade(user)

    history = await db.get_dialog_context(user_id, limit=8)
    if should_force_guided_mode(user_text, history):
        response = build_guided_task_response(user_text)
        await db.add_dialog_message(user_id, "user", user_text)
        await db.add_dialog_message(user_id, "assistant", response)
        asyncio.create_task(_update_memory_profile_safely(user_id, grade))
        return TutorEngineResult(text=response, guided=True, used_rag=False)

    rag_result = await build_tutor_rag_context(task_search, user_text)
    messages = await build_dialog_messages(user_id, grade, user_text, rag_result.text)
    guarded_response = await call_openrouter_guarded(
        user_id,
        messages,
        kind="tutor_chat",
        question=user_text,
    )
    if guarded_response.busy:
        return TutorEngineResult(
            text=guarded_response.text,
            guided=False,
            used_rag=False,
            rag_confidence=rag_result.confidence,
            rag_tasks=len(rag_result.tasks),
            busy=True,
        )

    response = force_clean_text(guarded_response.text)

    await db.add_dialog_message(user_id, "user", user_text)
    await db.add_dialog_message(user_id, "assistant", response)
    asyncio.create_task(_update_memory_profile_safely(user_id, grade))

    return TutorEngineResult(
        text=response,
        guided=False,
        used_rag=rag_result.used,
        rag_confidence=rag_result.confidence,
        rag_tasks=len(rag_result.tasks),
    )


async def _update_memory_profile_safely(user_id: int, grade: str) -> None:
    try:
        await maybe_update_memory_profile(user_id, grade)
    except Exception:
        logger.exception("Failed to update dialog memory")
