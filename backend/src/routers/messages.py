import asyncio
import contextlib
import html
import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from ..services import db
from ..helpers import (
    UNLIMITED_USERS,
    check_subscription,
    get_user_grade,
    is_admin,
)
from ..modules import (
    get_main_menu_keyboard,
    get_start_keyboard,
    split_text_for_telegram,
)
from ..modules.generation_control import generation_registry
from ..modules.tutor_engine import generate_tutor_response

router = Router()
logger = logging.getLogger(__name__)


# ============ ОБРАБОТЧИК СООБЩЕНИЙ ============


# ═══════════════════════════════════════════════════════════
#  ОБРАБОТЧИК ГРАФИКОВ
# ═══════════════════════════════════════════════════════════

@router.message(Command("reset_context"))
async def reset_context(m: types.Message):
    await db.clear_dialog_context(m.from_user.id)
    await m.answer("✅ Контекст диалога очищен. Начинаем с чистого листа.")


@router.message(Command("memory"))
async def show_memory(m: types.Message):
    profile = await db.get_memory_profile(m.from_user.id)
    if not profile["summary"] and not profile["learning_profile"]:
        await m.answer("Память пока пустая. Она появится после нескольких учебных сообщений.")
        return

    text = "🧠 <b>Память бота</b>\n\n"
    if profile["learning_profile"]:
        text += f"<b>Профиль:</b>\n{html.escape(profile['learning_profile'])}\n\n"
    if profile["summary"]:
        text += f"<b>Краткий контекст:</b>\n{html.escape(profile['summary'])}"
    await m.answer(text, parse_mode="HTML")


async def animate_thinking(thinking_msg: types.Message, reply_markup) -> None:
    frames = ["🤔 Думаю", "🤔 Думаю.", "🤔 Думаю..", "🤔 Думаю...", "💭 Думаю", "💭 Думаю.", "💭 Думаю..", "💭 Думаю..."]
    index = 0
    while True:
        try:
            await thinking_msg.edit_text(frames[index % len(frames)], reply_markup=reply_markup)
        except Exception:
            pass
        index += 1
        await asyncio.sleep(1.2)

@router.message(F.text.regexp(r"(?i)(построй|построить|график).*"))
async def handle_graph_request(m: types.Message):
    """Обрабатывает запросы на построение графиков"""
    import re
    from ..modules.graph_builder import build_graph
    from aiogram.types import BufferedInputFile
    
    # Извлекаем функцию из текста
    text = m.text
    match = re.search(r'(?:y\s*=\s*|функци[яюи]\s+)?([a-zA-Z0-9\+\-\*\/\^\(\)\s\.\,]+)', text, re.IGNORECASE)
    
    if not match:
        await m.answer(
            "📈 <b>Построение графика</b>\n\n"
            "Напиши функцию в формате:\n"
            "• <code>y = x²</code>\n"
            "• <code>y = sin(x)</code>\n"
            "• <code>y = 2x + 1</code>",
            parse_mode="HTML"
        )
        return
    
    expression = match.group(1).strip()
    
    # Строим график
    graph_bytes = build_graph(expression)
    
    if graph_bytes:
        await m.answer_photo(
            BufferedInputFile(graph_bytes, filename="graph.png"),
            caption=f"📈 График функции <code>y = {expression}</code>",
            parse_mode="HTML"
        )
    else:
        await m.answer(
            "❌ Не удалось построить график.\n"
            "Проверь правильность функции."
        )

@router.message()
async def handle(m: types.Message):
    tg_id = m.from_user.id
    text = m.text.strip() if m.text else ""
    if not text:
        return
    
    u = await db.get_user(tg_id)
    if not u.get("consent_pd"):
        await m.answer("⚠️ Сначала /start", reply_markup=get_start_keyboard())
        return
    
    if not is_admin(tg_id) and tg_id not in UNLIMITED_USERS and not check_subscription(u) and u.get("free_requests", 0) <= 0:
        await m.answer("⚠️ Лимит исчерпан. /menu", reply_markup=get_main_menu_keyboard())
        return

    # Показываем анимацию "Думаю"
    # Показываем анимацию с кнопкой отмены
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏹️ Остановить", callback_data="cancel_generation")]
    ])
    thinking_msg = await m.answer("🤔 Думаю", reply_markup=cancel_keyboard)
    animation_task = asyncio.create_task(animate_thinking(thinking_msg, cancel_keyboard))
    generation_task = None
    
    try:
        generation_task = asyncio.create_task(
            generate_tutor_response(tg_id, text, grade=get_user_grade(u))
        )
        await generation_registry.register(
            tg_id,
            generation_task,
            chat_id=thinking_msg.chat.id,
            message_id=thinking_msg.message_id,
        )
        result = await generation_task
    except asyncio.CancelledError:
        await m.answer("⏹️ Генерация остановлена.")
        return
    except Exception:
        logger.exception("Failed to generate tutor response")
        await m.answer("❌ Не удалось получить ответ. Попробуй еще раз.")
        return
    finally:
        if generation_task:
            await generation_registry.unregister(tg_id, generation_task)
        animation_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await animation_task
        try:
            await thinking_msg.delete()
        except Exception:
            pass

    if not result.busy:
        await db.record_request(tg_id)

    for part in split_text_for_telegram(result.text):
        await m.answer(part)
        await asyncio.sleep(0.3)

    if result.busy:
        return

    await db.record_activity(tg_id)

    from .achievements import check_achievements

    achievements = await check_achievements(tg_id)
    if achievements:
        await m.answer(achievements)
