from dataclasses import dataclass

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from ..modules import get_back_keyboard
from ..services import db


router = Router()


@dataclass(frozen=True)
class Achievement:
    id: str
    emoji: str
    name: str
    condition: str
    description: str
    metric: str | None = None
    target: int = 1
    rarity: str = "common"
    automatic: bool = True


ACHIEVEMENTS = [
    Achievement("first_request", "🐣", "Первый контакт", "1 запрос", "Добро пожаловать в матрицу!", "total_requests", 1),
    Achievement("ten_requests", "🌱", "Новичок", "10 запросов", "Ты уже не нубас!", "total_requests", 10),
    Achievement("fifty_requests", "⚡", "Активист", "50 запросов", "Бот тебя узнаёт в лицо", "total_requests", 50),
    Achievement("hundred_requests", "💪", "Я хорош в этом", "100 запросов", "Спонсор OpenRouter", "total_requests", 100, "rare"),
    Achievement("five_hundred_requests", "🧟", "Зависимый", "500 запросов", "Бот видит твои сны", "total_requests", 500, "epic"),
    Achievement("thousand_requests", "👑", "Легенда", "1000 запросов", "Ты и бот — одно целое", "total_requests", 1000, "legendary"),
    Achievement("million_requests", "🌌", "Бог промптов", "1 млн запросов", "Ты сломал сервер. Поздравляю.", "total_requests", 1_000_000, "legendary"),

    Achievement("first_task", "🎯", "Первая кровь", "1 задача", "Начало положено!", "total", 1),
    Achievement("ten_tasks", "🏃", "Разминка", "10 задач", "Как на физре, только лучше", "total", 10),
    Achievement("fifty_tasks", "📚", "Середнячок", "50 задач", "Учитель гордился бы", "total", 50, "rare"),
    Achievement("hundred_tasks", "🥊", "Боец", "100 задач", "ЕГЭ? Да я его сломаю!", "total", 100, "rare"),
    Achievement("five_hundred_tasks", "🤖", "Машина", "500 задач", "Ты не человек, ты алгоритм", "total", 500, "epic"),
    Achievement("thousand_tasks", "💀", "Терминатор", "1000 задач", "I'll be back... к следующей задаче", "total", 1000, "legendary"),
    Achievement("ten_thousand_tasks", "⚰️", "Бессмертный", "10 000 задач", "Ты решил больше, чем ФИПИ составил", "total", 10_000, "legendary"),

    Achievement("genius", "🎓", "Гений", "100% правильных ответов (50+ задач)", "Менса звонит", "accuracy_100_50", 100, "legendary"),

    Achievement("diverse", "🎨", "Разносторонний", "3 предмета", "Не только математик", "subjects", 3),
    Achievement("erudite", "🧠", "Эрудит", "5 предметов", "Википедия нервно курит", "subjects", 5, "rare"),
    Achievement("universal", "🎓", "Универсал", "8 предметов", "Тебе бы в Менделеевский", "subjects", 8, "epic"),
    Achievement("omnimatic", "🌟", "Омниматик", "Все предметы", "Ты знаешь всё. Буквально.", "subjects", 12, "legendary"),
    Achievement("math_master", "📐", "Математик", "50 задач по матеше", "Пифагор гордится тобой", "math_tasks", 50, "rare"),
    Achievement("physics_theorist", "⚛️", "Физик-теоретик", "50 задач по физике", "Эйнштейн одобряет", "physics_tasks", 50, "rare"),
    Achievement("literature_author", "📖", "Литератор", "50 задач по литературе", "Достоевский плачет от зависти", "literature_tasks", 50, "rare"),
    Achievement("polyglot", "🇬🇧", "Полиглот", "50 задач по английскому", "London is the capital of...", "english_tasks", 50, "rare"),

    Achievement("weekend_warrior", "📅", "Выходной воин", "50 задач в выходные", "Пока другие гуляют...", "weekend_tasks", 50, "rare"),
    Achievement("task_samurai", "🎯", "Серийный убийца задач", "10 задач подряд без ошибок", "Катана наточена", "max_correct_streak", 10, "epic"),
    Achievement("critical_error", "💔", "Критическая ошибка", "10 ошибок подряд", "Надо отдохнуть, бро", "max_wrong_streak", 10, "rare"),
    Achievement("helper", "💡", "Подсказчик", "50 раз попросил объяснение", "Не стыдно спросить — стыдно не знать", "used_explanation", 50, "rare"),

    Achievement("night_watch", "🌙", "Ночной дозор", "10 запросов после 23:00", "Сон для слабаков", "night_requests", 10, "rare"),
    Achievement("early_bird", "🐓", "Ранняя пташка", "10 запросов до 7:00", "Кто рано встаёт... тот не высыпается", "early_requests", 10, "rare"),
    Achievement("holiday_worker", "🎄", "Праздничный трудяга", "Запрос 31 декабря", "Оливье подождёт", "new_year_eve_requests", 1, "epic"),

    Achievement("september_marathon", "🍂", "Сентябрьский марафон", "100 задач в сентябре", "Учебный год начался!", "september_tasks", 100, "rare"),
    Achievement("new_year_marathon", "🎅", "Новогодний марафон", "50 задач за каникулы", "Подарок себе — знания", "winter_holiday_tasks", 50, "rare"),
    Achievement("february_challenge", "❤️", "Февральский челлендж", "100 задач в феврале", "Любовь к знаниям", "february_tasks", 100, "rare"),
    Achievement("may_bug", "🌸", "Майский жук", "50 задач в мае", "Готовимся к ЕГЭ в последний момент", "may_tasks", 50, "rare"),
    Achievement("summer_intellectual", "☀️", "Летний интеллектуал", "200 задач за лето", "Пока другие на море...", "summer_tasks", 200, "epic"),

    Achievement("sponsor", "💎", "Спонсор", "Купил подписку", "Капитализм одобряет", "has_subscription", 1, "rare"),
    Achievement("patron", "💰", "Меценат", "Купил Премиум", "Ты не пользователь, ты инвестор", "has_premium", 1, "epic"),

    Achievement("first_on_moon", "🚀", "Первый на Луне", "Первый пользователь бота", "Маленький шаг для человека...", automatic=False),
    Achievement("bug_hunter", "🐛", "Баг-хантер", "Нашёл и сообщил о баге", "Спасибо, что ломаешь нас лучше", automatic=False),
    Achievement("loyal_friend", "📆", "Верный друг", "365 дней в боте", "Год вместе. Это серьёзно.", automatic=False),
    Achievement("influencer", "🤝", "Инфлюенсер", "Привёл 10 друзей", "Сарафанное радио", automatic=False),
    Achievement("school_legend", "📢", "Легенда школы", "Привёл 50 друзей", "О тебе знает вся школа", automatic=False),
    Achievement("impossible_possible", "🧩", "Невозможное возможно", "Решил задачу из части 2 ЕГЭ", "Это не реально. Но ты смог.", automatic=False),
    Achievement("hidden", "🎁", "Скрытое достижение", "???", "Секретный уровень", automatic=False),
    Achievement("skeptic", "🔍", "Скептик", "20 раз попросил перепроверить", "Доверяй, но проверяй", automatic=False),
    Achievement("sloth", "🦥", "Ленивец", "Решил задачу за 5 секунд", "Спидраннер", automatic=False),
    Achievement("perfectionist", "🔄", "Перфекционист", "Переделал задачу 5 раз", "Идеал недостижим, но ты стараешься", automatic=False),
    Achievement("bunny", "🐰", "Зайка", "10 минут", "Быстрый визит", "total_active_seconds", 10 * 60),
    Achievement("guest", "☕", "Гость", "1 час", "Чай выпил и ушёл", "total_active_seconds", 60 * 60),
    Achievement("regular", "🛋️", "Завсегдатай", "5 часов", "Бот уже скучал без тебя", "total_active_seconds", 5 * 60 * 60, "rare"),
    Achievement("marathoner", "🏃‍♂️", "Марафонец", "24 часа", "Ты живёшь в боте?", "total_active_seconds", 24 * 60 * 60, "epic"),
    Achievement("sleepless_night", "🦉", "Бессонная ночь", "Запрос в 3 ночи", "Сова или просто не выспался?", "three_am_requests", 1, "rare"),
    Achievement("eternal_student", "📺", "Вечный студент", "100 часов", "Социальная жизнь? Не, не слышал", "total_active_seconds", 100 * 60 * 60, "legendary"),
    Achievement("matrix", "💊", "Матрица", "1000 часов", "Красная или синяя таблетка?", "total_active_seconds", 1000 * 60 * 60, "legendary"),
]

RARITY_LABELS = {
    "common": "обычное",
    "rare": "редкое",
    "epic": "эпическое",
    "legendary": "легендарное",
}


async def record_event(user_id: int, event_type: str) -> None:
    async with db.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_events (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            INSERT INTO user_events (user_id, event_type)
            VALUES ($1, $2)
        """, user_id, event_type)


def _max_streak(values: list[bool], expected: bool) -> int:
    best = 0
    current = 0
    for value in values:
        if value is expected:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


async def get_user_achievement_stats(user_id: int) -> dict:
    async with db.pool.acquire() as conn:
        await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_requests INT DEFAULT 0;")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_events (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_correct) as correct,
                COUNT(DISTINCT sp.subject_id) as subjects,
                COUNT(DISTINCT topic) as topics,
                COUNT(*) FILTER (WHERE used_explanation) as used_explanation,
                COUNT(*) FILTER (WHERE EXTRACT(ISODOW FROM sp.created_at) IN (6, 7)) as weekend_tasks,
                COUNT(*) FILTER (WHERE EXTRACT(MONTH FROM sp.created_at) = 9) as september_tasks,
                COUNT(*) FILTER (WHERE EXTRACT(MONTH FROM sp.created_at) = 2) as february_tasks,
                COUNT(*) FILTER (WHERE EXTRACT(MONTH FROM sp.created_at) = 5) as may_tasks,
                COUNT(*) FILTER (WHERE EXTRACT(MONTH FROM sp.created_at) IN (6, 7, 8)) as summer_tasks,
                COUNT(*) FILTER (
                    WHERE (EXTRACT(MONTH FROM sp.created_at) = 12 AND EXTRACT(DAY FROM sp.created_at) >= 25)
                       OR (EXTRACT(MONTH FROM sp.created_at) = 1 AND EXTRACT(DAY FROM sp.created_at) <= 8)
                ) as winter_holiday_tasks,
                COUNT(*) FILTER (WHERE LOWER(COALESCE(s.code, '')) LIKE '%math%' OR LOWER(COALESCE(s.name, '')) LIKE '%мат%') as math_tasks,
                COUNT(*) FILTER (WHERE LOWER(COALESCE(s.code, '')) LIKE '%physics%' OR LOWER(COALESCE(s.name, '')) LIKE '%физ%') as physics_tasks,
                COUNT(*) FILTER (WHERE LOWER(COALESCE(s.code, '')) LIKE '%literature%' OR LOWER(COALESCE(s.name, '')) LIKE '%лит%') as literature_tasks,
                COUNT(*) FILTER (WHERE LOWER(COALESCE(s.code, '')) LIKE '%english%' OR LOWER(COALESCE(s.name, '')) LIKE '%англ%') as english_tasks
            FROM student_progress sp
            LEFT JOIN subjects s ON sp.subject_id = s.id
            WHERE sp.user_id = $1
        """, user_id)

        user = await conn.fetchrow("""
            SELECT total_requests, student_sub, standard_sub, business_sub
            FROM users
            WHERE tg_id = $1
        """, user_id)

        events = await conn.fetchrow("""
            SELECT
                COUNT(*) FILTER (WHERE event_type = 'request' AND EXTRACT(HOUR FROM created_at) >= 23) as night_requests,
                COUNT(*) FILTER (WHERE event_type = 'request' AND EXTRACT(HOUR FROM created_at) < 7) as early_requests,
                COUNT(*) FILTER (WHERE event_type = 'request' AND EXTRACT(HOUR FROM created_at) = 3) as three_am_requests,
                COUNT(*) FILTER (
                    WHERE event_type = 'request'
                      AND EXTRACT(MONTH FROM created_at) = 12
                      AND EXTRACT(DAY FROM created_at) = 31
                ) as new_year_eve_requests
            FROM user_events
            WHERE user_id = $1
        """, user_id)

        progress_rows = await conn.fetch("""
            SELECT is_correct
            FROM student_progress
            WHERE user_id = $1
            ORDER BY created_at, id
        """, user_id)

        time_stats = await conn.fetchrow("""
            SELECT total_seconds
            FROM user_time_stats
            WHERE user_id = $1
        """, user_id)

        active_session = await conn.fetchrow("""
            SELECT started_at, last_activity
            FROM user_sessions
            WHERE user_id = $1 AND is_active = TRUE
            ORDER BY started_at DESC
            LIMIT 1
        """, user_id)

    total = stats["total"] or 0
    correct = stats["correct"] or 0
    is_correct_values = [row["is_correct"] for row in progress_rows]
    has_subscription = bool(user and (user["student_sub"] or user["standard_sub"] or user["business_sub"]))
    has_premium = bool(user and user["business_sub"])
    completed_seconds = (time_stats["total_seconds"] if time_stats else 0) or 0
    active_seconds = 0
    if active_session:
        active_seconds = max(0, int((active_session["last_activity"] - active_session["started_at"]).total_seconds()))

    return {
        "total": total,
        "correct": correct,
        "subjects": stats["subjects"] or 0,
        "topics": stats["topics"] or 0,
        "used_explanation": stats["used_explanation"] or 0,
        "accuracy": int(correct / total * 100) if total else 0,
        "accuracy_100_50": 100 if total >= 50 and correct == total else 0,
        "max_correct_streak": _max_streak(is_correct_values, True),
        "max_wrong_streak": _max_streak(is_correct_values, False),
        "total_requests": (user["total_requests"] if user else 0) or 0,
        "total_active_seconds": completed_seconds + active_seconds,
        "has_subscription": int(has_subscription),
        "has_premium": int(has_premium),
        **{key: stats[key] or 0 for key in (
            "weekend_tasks",
            "september_tasks",
            "february_tasks",
            "may_tasks",
            "summer_tasks",
            "winter_holiday_tasks",
            "math_tasks",
            "physics_tasks",
            "literature_tasks",
            "english_tasks",
        )},
        **{key: events[key] or 0 for key in (
            "night_requests",
            "early_requests",
            "three_am_requests",
            "new_year_eve_requests",
        )},
    }


def achievement_is_unlocked(achievement: Achievement, stats: dict) -> bool:
    if not achievement.automatic or not achievement.metric:
        return False
    return stats.get(achievement.metric, 0) >= achievement.target


def achievement_progress(achievement: Achievement, stats: dict) -> tuple[int, int]:
    if not achievement.automatic or not achievement.metric:
        return 0, achievement.target
    return min(stats.get(achievement.metric, 0), achievement.target), achievement.target


def format_metric_value(value: int, metric: str | None) -> str:
    if metric != "total_active_seconds":
        return str(value)
    hours = value // 3600
    minutes = (value % 3600) // 60
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def build_progress_bar(done: int, total: int, width: int = 12) -> str:
    if total <= 0:
        return "░" * width
    filled = round(width * done / total)
    return "█" * filled + "░" * (width - filled)


async def get_unlocked_achievement_ids(user_id: int) -> set[str]:
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT achievement_type
            FROM achievements
            WHERE user_id = $1
        """, user_id)
    return {row["achievement_type"] for row in rows}


async def check_achievements(user_id: int) -> str:
    stats = await get_user_achievement_stats(user_id)
    unlocked_ids = await get_unlocked_achievement_ids(user_id)
    new_achievements = []

    async with db.pool.acquire() as conn:
        for achievement in ACHIEVEMENTS:
            if achievement.id in unlocked_ids:
                continue
            if not achievement_is_unlocked(achievement, stats):
                continue

            await conn.execute("""
                INSERT INTO achievements (user_id, achievement_type, achievement_name)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, achievement_type) DO NOTHING
            """, user_id, achievement.id, achievement.name)
            new_achievements.append(achievement)

    if not new_achievements:
        return ""

    lines = [f"🏅 {item.emoji} {item.name}" for item in new_achievements]
    return "\n\n" + "\n".join(lines) + "\n\nПоздравляем с новыми достижениями!"


async def render_achievements(user_id: int) -> str:
    await check_achievements(user_id)

    stats = await get_user_achievement_stats(user_id)
    unlocked_ids = await get_unlocked_achievement_ids(user_id)
    unlocked = [item for item in ACHIEVEMENTS if item.id in unlocked_ids]
    locked = [item for item in ACHIEVEMENTS if item.id not in unlocked_ids]

    total_count = len(ACHIEVEMENTS)
    unlocked_count = len(unlocked)
    percent = int(unlocked_count / total_count * 100) if total_count else 0
    bar = build_progress_bar(unlocked_count, total_count)

    lines = [
        "🏆 <b>Достижения</b>",
        "",
        f"Прогресс: <b>{unlocked_count}/{total_count}</b> ({percent}%)",
        f"{bar}",
        "",
        "<b>Полученные</b>",
    ]

    if unlocked:
        for item in unlocked:
            rarity = RARITY_LABELS.get(item.rarity, item.rarity)
            lines.append(f"✅ {item.emoji} <b>{item.name}</b> ({rarity})")
    else:
        lines.append("Пока нет открытых достижений. Реши первую задачу или отправь запрос, и коллекция начнет расти.")

    lines.extend(["", "<b>Еще не открыты</b>"])
    for item in locked:
        current, target = achievement_progress(item, stats)
        if item.automatic and item.metric:
            current_text = format_metric_value(current, item.metric)
            target_text = format_metric_value(target, item.metric)
            lines.append(f"🔒 {item.emoji} <b>{item.name}</b> — {item.condition} ({current_text}/{target_text})")
        else:
            lines.append(f"🔒 {item.emoji} <b>{item.name}</b> — {item.condition}")

    return "\n".join(lines)


@router.message(Command("achievements"))
async def cmd_achievements(m: types.Message):
    await m.answer(
        await render_achievements(m.from_user.id),
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )


@router.callback_query(F.data == "show_achievements")
async def show_achievements_callback(cq: CallbackQuery):
    await cq.message.edit_text(
        await render_achievements(cq.from_user.id),
        parse_mode="HTML",
        reply_markup=get_back_keyboard(),
    )
    await cq.answer()
