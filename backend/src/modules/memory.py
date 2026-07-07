import logging

from ..services import db
from .ai_gateway import call_openrouter_guarded


logger = logging.getLogger(__name__)

SUMMARY_EVERY_MESSAGES = 12


def _format_retrieved_memory(items: list[dict]) -> str:
    if not items:
        return ""
    lines = []
    for item in items:
        role = "Ученик" if item["role"] == "user" else "Бот"
        content = item["content"].replace("\n", " ").strip()
        lines.append(f"- {role}: {content[:500]}")
    return "\n".join(lines)


async def build_memory_context(user_id: int, query: str) -> str:
    profile = await db.get_memory_profile(user_id)
    retrieved = await db.search_dialog_memory(user_id, query, limit=4)

    blocks = []
    if profile["learning_profile"]:
        blocks.append(f"Профиль ученика:\n{profile['learning_profile']}")
    if profile["summary"]:
        blocks.append(f"Краткая долговременная память:\n{profile['summary']}")

    retrieved_text = _format_retrieved_memory(retrieved)
    if retrieved_text:
        blocks.append(f"Релевантные прошлые фрагменты:\n{retrieved_text}")

    if not blocks:
        return ""

    return (
        "Память о пользователе. Используй только если это помогает ответу, "
        "не упоминай внутреннюю память напрямую:\n\n"
        + "\n\n".join(blocks)
    )


async def maybe_update_memory_profile(user_id: int, grade: str) -> None:
    current = await db.get_memory_profile(user_id)
    latest_message_id = await db.get_latest_dialog_message_id(user_id)
    if latest_message_id <= 0:
        return
    if latest_message_id - current["last_message_id"] < SUMMARY_EVERY_MESSAGES:
        return

    recent_dialog = await db.get_recent_dialog_text(user_id, limit=20)
    if not recent_dialog:
        return

    prompt = f"""
Обнови долговременную память учебного бота.

Текущий класс/уровень: {grade}

Старая краткая память:
{current['summary'] or 'Пока пусто.'}

Старый профиль ученика:
{current['learning_profile'] or 'Пока пусто.'}

Последний диалог:
{recent_dialog}

Верни строго в таком формате:
SUMMARY:
- 3-8 коротких пунктов: что проходили, какие задания давались, какие ответы ученик уже писал.

PROFILE:
- 3-6 коротких пунктов: уровень, стиль объяснений, типичные ошибки, интересы, что важно помнить.

Не добавляй чувствительные данные, секреты, ключи, телефоны, адреса. Не выдумывай.
""".strip()

    try:
        guarded_response = await call_openrouter_guarded(
            -abs(user_id),
            [{"role": "user", "content": prompt}],
            kind="memory_summary",
            wait_timeout=0,
            busy_message="",
            max_tokens=900,
            question="memory_summary",
        )
        if guarded_response.busy:
            logger.info("Skipped memory profile update because AI queue is busy")
            return
        result = guarded_response.text
    except Exception:
        logger.exception("Failed to update memory profile")
        return

    summary = current["summary"]
    profile = current["learning_profile"]
    if "PROFILE:" in result:
        summary_part, profile_part = result.split("PROFILE:", 1)
        summary = summary_part.replace("SUMMARY:", "").strip()
        profile = profile_part.strip()
    else:
        summary = result.strip()

    await db.update_memory_profile(user_id, summary, profile, latest_message_id)
