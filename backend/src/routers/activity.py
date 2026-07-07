from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from ..modules import get_back_keyboard
from ..services import db


router = Router()


def format_duration(seconds: int) -> str:
    seconds = max(0, int(seconds or 0))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def activity_bar(seconds: int, target_seconds: int = 3600, width: int = 12) -> str:
    filled = round(width * min(seconds, target_seconds) / target_seconds)
    return "█" * filled + "░" * (width - filled)


async def render_activity(user_id: int) -> str:
    stats = await db.get_activity_stats(user_id)
    active_text = "активна" if stats["has_active_session"] else "закрыта"

    return "\n".join([
        "⏱ <b>Активность</b>",
        "",
        f"Всего активного времени: <b>{format_duration(stats['total_seconds'])}</b>",
        f"Сегодня: <b>{format_duration(stats['today_seconds'])}</b>",
        f"Сессий завершено: <b>{stats['session_count']}</b>",
        f"Лучшая сессия: <b>{format_duration(stats['longest_session_seconds'])}</b>",
        f"Текущая сессия: <b>{format_duration(stats['active_seconds'])}</b> ({active_text})",
        "",
        f"{activity_bar(stats['today_seconds'])} цель дня: 1 ч",
        "",
        "Время считается только между действиями в боте. Если активности нет больше часа, сессия закрывается без начисления пустого ожидания.",
    ])


@router.message(Command("activity"))
async def cmd_activity(m: types.Message):
    await db.record_activity(m.from_user.id)
    await m.answer(
        await render_activity(m.from_user.id),
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )


@router.callback_query(F.data == "show_activity")
async def show_activity_callback(cq: CallbackQuery):
    await db.record_activity(cq.from_user.id)
    await cq.message.edit_text(
        await render_activity(cq.from_user.id),
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )
    await cq.answer()
