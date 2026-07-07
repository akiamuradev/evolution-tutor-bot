from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
from ..states import DocStates
from ..services import db
from ..helpers import UNLIMITED_USERS, check_subscription, get_user_grade, is_admin
from ..modules import (
    ai_cache,
    get_doc_format_keyboard,
    get_grade_keyboard,
    get_main_menu_keyboard,
    get_start_keyboard,
    get_subscribe_keyboard,
)
from ..modules.request_guard import ai_request_guard
from ..modules.anti_spam import anti_spam_guard
from ..modules.ai_gateway import ai_gateway_stats
from ..modules.generation_control import generation_registry

router = Router()


# ============ ОСНОВНЫЕ ХЕНДЛЕРЫ ============

@router.message(CommandStart())
async def cmd_start(m: types.Message):
    u = await db.get_user(m.from_user.id)
    
    WELCOME_TEXT = """🎓 <b>ЭВО:ЛЮЦИЯ</b>
━━━━━━━━━━━━━━━━━━━━━━━

👋 Привет! Я — твой умный помощник в учёбе.

✨ <b>Чем я могу помочь:</b>

📚 <b>Учёба</b>
• Помогу с домашним заданием по любому предмету
• Объясню сложную тему простыми словами
• Подготовлю к ОГЭ и ЕГЭ (разберём каждую задачу)
• Дам потренироваться на реальных заданиях

🛠️ <b>Инструменты</b>
• Построю график любой функции
• Решу уравнение или пример с формулами
• Создам красивый документ (DOCX или PDF)
• Распознаю текст с фотографии

📊 <b>Прогресс</b>
• Покажу, сколько ты уже знаешь
• Составлю план подготовки к экзаменам
• Дам рекомендации, над чем поработать

━━━━━━━━━━━━━━━━━━━━━━━

👇 Для начала выбери свой класс:"""

    if not u.get("consent_pd"):
        await m.answer(
            WELCOME_TEXT + "\n\n📋 <i>И ещё — нужно принять соглашение о обработке данных:</i>",
            reply_markup=get_start_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Пользователь уже регистрировался — сразу показываем меню
        grade = u.get("grade", "5_9")
        await m.answer(
            f"👋 С возвращением!\n\n📋 <b>Главное меню:</b>",
            reply_markup=get_main_menu_keyboard(grade),
            parse_mode="HTML"
        )

@router.message(Command("me"))
async def cmd_me(m: types.Message):
    u = await db.get_user(m.from_user.id)
    has_sub = check_subscription(u)
    sub_status = "✅ Активна" if has_sub else "❌ Неактивна"
    is_unlimited = m.from_user.id in UNLIMITED_USERS
    unlimited_text = " (♾️ Безлимит)" if is_unlimited else ""
    
    cache_stats = ai_cache.stats()
    
    await m.answer(
        f"🔍 Статус:\n"
        f"ID: {m.from_user.id}\n"
        f"Класс: {get_user_grade(u)}\n"
        f"Голос: {'🔊 Вкл' if u.get('voice_enabled') else '🔇 Выкл'}\n"
        f"Подписка: {sub_status}{unlimited_text}\n\n"
        f"⚡ Кэш ИИ: {cache_stats['size']}/{cache_stats['max_size']} записей",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("health"))
async def cmd_health(m: types.Message):
    if not is_admin(m.from_user.id):
        return

    cache_stats = ai_cache.stats()
    guard_stats = ai_request_guard.stats()
    spam_stats = anti_spam_guard.stats()
    gateway_stats = ai_gateway_stats.stats()
    generation_stats = generation_registry.stats()
    message_profile = spam_stats["profiles"]["message"]
    api_chat_profile = spam_stats["profiles"]["api_chat"]
    db_status = "ok"
    try:
        await db.pool.fetchval("SELECT 1")
    except Exception as exc:
        db_status = f"error: {str(exc)[:80]}"
    gateway_kind_text = ", ".join(
        f"{kind}:a{item['model_active']}/s{item['started']}/b{item['busy']}/c{item['cancelled']}"
        for kind, item in gateway_stats["by_kind"].items()
    ) or "-"

    await m.answer(
        "<b>Health</b>\n\n"
        f"DB: <code>{db_status}</code>\n"
        f"AI active: <code>{guard_stats['active_ai_requests']}/"
        f"{guard_stats['max_concurrent_ai_requests']}</code>\n"
        f"AI waiting: <code>{guard_stats['waiting_ai_requests']}/"
        f"{guard_stats['max_waiting_ai_requests']}</code>\n"
        f"AI queued total: <code>{guard_stats['queued_total']}</code>\n"
        f"AI queue timeouts: <code>{guard_stats['queue_timeout_total']}</code>\n"
        f"AI duplicate user: <code>{guard_stats['duplicate_user_total']}</code>\n"
        f"AI active users: <code>{guard_stats['active_users']}</code>\n"
        f"AI known locks: <code>{guard_stats['known_user_locks']}</code>\n"
        f"AI gateway active: <code>{gateway_stats['model_active_total']}</code>\n"
        f"AI gateway inflight: <code>{gateway_stats['inflight_total']}</code>\n"
        f"AI gateway busy: <code>{gateway_stats['busy_total']}</code>\n"
        f"AI gateway cancelled: <code>{gateway_stats['cancelled_total']}</code>\n"
        f"AI gateway failed: <code>{gateway_stats['failed_total']}</code>\n"
        f"AI gateway kinds: <code>{gateway_kind_text}</code>\n"
        f"Generations active: <code>{generation_stats['active_generations']}</code>\n"
        f"Generations cancelled: <code>{generation_stats['cancelled_total']}</code>\n"
        f"Generations replaced: <code>{generation_stats['replaced_total']}</code>\n"
        f"Updates active: <code>{spam_stats['active_updates']}/"
        f"{spam_stats['max_concurrent_updates']}</code>\n"
        f"Anti-spam blocked: <code>{spam_stats['blocked_total']}</code>\n"
        f"Blocked by reason: <code>{spam_stats['blocked_by_reason']}</code>\n"
        f"Blocked by action: <code>{spam_stats['blocked_by_action']}</code>\n"
        f"Cooldowns: <code>{spam_stats['active_cooldowns']}</code>\n"
        f"Message limit: <code>{message_profile['max_events_per_window']}/"
        f"{message_profile['window_seconds']}s</code>\n"
        f"API chat limit: <code>{api_chat_profile['max_events_per_window']}/"
        f"{api_chat_profile['window_seconds']}s</code>\n"
        f"Cache: <code>{cache_stats['size']}/{cache_stats['max_size']}</code>",
        parse_mode="HTML",
    )


@router.message(Command("menu"))
async def cmd_menu(m: types.Message):
    u = await db.get_user(m.from_user.id)
    if not u.get("consent_pd"):
        await m.answer("⚠️ Сначала /start")
        return
    grade = u.get("grade", "5_9")
    await m.answer(
        "📋 <b>Главное меню</b>\n\nВыбери, что хочешь сделать:",
        reply_markup=get_main_menu_keyboard(grade),
        parse_mode="HTML"
    )

@router.message(Command("features"))
async def cmd_features(m: types.Message):
    """Показать возможности бота"""
    try:
        with open('/opt/tutor-bot/backend/src/bot_features.txt', 'r', encoding='utf-8') as f:
            features = f.read()
        await m.answer(features)
    except:
        await m.answer("📊 Отчёт о возможностях временно недоступен")

# ============ CALLBACK ХЕНДЛЕРЫ ============

@router.callback_query(F.data == "consent_accept")
async def on_consent(c: CallbackQuery):
    await db.set_consent(c.from_user.id)
    await c.message.edit_text("📚 Выбери свой класс:", reply_markup=get_grade_keyboard())
    await c.answer()

@router.callback_query(F.data.startswith("grade_"))
async def save_grade(c: CallbackQuery):
    gmap = {"grade_1_4": "1-4", "grade_5_9": "5-9", "grade_10_11": "10-11"}
    g = gmap.get(c.data)
    await db.update_user(c.from_user.id, active_mode="schoolboy")
    await db.set_grade_range(c.from_user.id, g)
    await c.message.edit_text(f"✅ Класс {g} выбран!\n\n💡 Пиши вопросы — я помогу разобраться!")
    await c.answer()

@router.callback_query(F.data == "show_subscribe")
async def show_sub(c: CallbackQuery):
    await c.message.answer("💎 Тарифы для школьников:\n🔹 Базовый — 299₽/мес\n🔹 Расширенный (ОГЭ/ЕГЭ) — 499₽/мес\n🔹 Премиум (персональный план) — 990₽/мес", reply_markup=get_subscribe_keyboard())
    await c.answer()

@router.callback_query(F.data.startswith("buy_"))
async def buy_sub(c: CallbackQuery):
    mode = c.data.split("_")[1]
    mode_map = {"basic": "student", "extended": "standard", "premium": "business"}
    await db.activate_subscription(c.from_user.id, mode_map.get(mode, "student"), 30)
    await c.message.edit_text(f"✅ Подписка активирована на 30 дней!")
    from .achievements import check_achievements

    achievements = await check_achievements(c.from_user.id)
    if achievements:
        await c.message.answer(achievements)
    await c.answer()

@router.callback_query(F.data == "toggle_voice")
async def toggle_voice(c: CallbackQuery):
    u = await db.get_user(c.from_user.id)
    new_state = not u.get('voice_enabled', False)
    await db.set_voice_enabled(c.from_user.id, new_state)
    try:
        await c.message.edit_reply_markup(reply_markup=get_main_menu_keyboard())
    except:
        pass
    await c.answer(f"Голос: {'🔊 Включён' if new_state else '🔇 Выключен'}", show_alert=True)

@router.callback_query(F.data == "create_doc_menu")
async def create_doc_menu(c: CallbackQuery, state: FSMContext):
    await c.message.answer("📄 Выберите формат:", reply_markup=get_doc_format_keyboard())
    await state.set_state(DocStates.waiting_for_format)
    await c.answer()

@router.callback_query(F.data == "change_grade")
async def change_grade(c: CallbackQuery):
    await c.message.edit_text("📚 Выбери свой класс:", reply_markup=get_grade_keyboard())
    await c.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(c: CallbackQuery):
    try:
        await c.message.edit_text("📊 Меню", reply_markup=get_main_menu_keyboard())
    except:
        pass
    await c.answer()
