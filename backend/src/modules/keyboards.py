"""Клавиатуры для школьников — новая версия"""
import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

DOCS_URL = os.getenv("DOCS_URL", "https://evo-lution96.ru")
PRIVACY_URL = f"{DOCS_URL}/privacy"


# ═══════════════════════════════════════════════════════════
#  ЭКРАН 1: Приветствие (показывается при /start)
# ═══════════════════════════════════════════════════════════
def get_start_keyboard() -> InlineKeyboardMarkup:
    """Первый экран — согласие с политикой"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Политика конфиденциальности", url=PRIVACY_URL)],
        [InlineKeyboardButton(text="✅ Мне есть 14 лет, принимаю", callback_data="consent_accept")],
        [InlineKeyboardButton(text="👨‍👩‍👧 Мне нет 14 лет (согласие родителя)", callback_data="consent_parent")]
    ])


def get_parent_consent_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Политика конфиденциальности", url=PRIVACY_URL)],
        [InlineKeyboardButton(text="✅ Я родитель, даю согласие", callback_data="parent_consent_accept")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="consent_cancel")]
    ])


# ═══════════════════════════════════════════════════════════
#  ЭКРАН 2: Выбор класса
# ═══════════════════════════════════════════════════════════
def get_grade_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧒 1-4 класс", callback_data="grade_1_4"),
            InlineKeyboardButton(text="📚 5-9 классы", callback_data="grade_5_9"),
        ],
        [InlineKeyboardButton(text="🎓 10-11 классы", callback_data="grade_10_11")],
    ])


# ═══════════════════════════════════════════════════════════
#  ЭКРАН 3: ГЛАВНОЕ МЕНЮ (универсальное для всех возрастов)
# ═══════════════════════════════════════════════════════════
def get_main_menu_keyboard(grade: str = "5_9") -> InlineKeyboardMarkup:
    """
    Главное меню адаптируется под класс:
    - 1-4: нет экзаменов, упор на домашку
    - 5-9: есть ОГЭ
    - 10-11: есть ЕГЭ
    """
    rows = []

    # ── Блок: УЧЁБА ──
    rows.append([InlineKeyboardButton(text="── 📖 УЧЁБА ──", callback_data="noop")])

    rows.append([
        InlineKeyboardButton(text="📝 Домашнее задание", callback_data="homework"),
        InlineKeyboardButton(text="💡 Объяснить тему", callback_data="explain_topic"),
    ])

    # Экзамены — только для 5-9 и 10-11
    if grade in ("5_9", "10_11"):
        exam_label = "🎯 Подготовка к ЕГЭ" if grade == "10_11" else "🎯 Подготовка к ОГЭ"
        rows.append([
            InlineKeyboardButton(text=exam_label, callback_data="exam_prep"),
            InlineKeyboardButton(text="🏋️ Практика задач", callback_data="practice_menu"),
        ])
    else:
        rows.append([
            InlineKeyboardButton(text="🏋️ Практика задач", callback_data="practice_menu"),
        ])

    # ── Блок: ИНСТРУМЕНТЫ ──
    rows.append([InlineKeyboardButton(text="── 🛠️ ИНСТРУМЕНТЫ ──", callback_data="noop")])

    rows.append([
        InlineKeyboardButton(text="📈 Графики функций", callback_data="tools_graph"),
        InlineKeyboardButton(text="📐 Формулы", callback_data="tools_formula"),
    ])
    rows.append([
        InlineKeyboardButton(text="📄 Создать документ", callback_data="tools_doc"),
        InlineKeyboardButton(text="📸 Распознать текст", callback_data="tools_ocr"),
    ])

    # ── Блок: ПРОГРЕСС ──
    rows.append([InlineKeyboardButton(text="── 📊 МОЙ ПРОГРЕСС ──", callback_data="noop")])
    rows.append([
        InlineKeyboardButton(text="📈 Моя статистика", callback_data="show_stats"),
        InlineKeyboardButton(text="🏆 Достижения", callback_data="show_achievements"),
    ])
    rows.append([
        InlineKeyboardButton(text="📋 План подготовки", callback_data="show_plan"),
        InlineKeyboardButton(text="⏱ Активность", callback_data="show_activity"),
    ])

    # ── Блок: НАСТРОЙКИ ──
    rows.append([InlineKeyboardButton(text="── ⚙️ НАСТРОЙКИ ──", callback_data="noop")])
    rows.append([InlineKeyboardButton(text="🔄 Сменить класс", callback_data="change_grade")])
    rows.append([
        InlineKeyboardButton(text="💎 Подписка", callback_data="show_subscribe"),
        InlineKeyboardButton(text="📚 Возможности бота", callback_data="show_features"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════
#  ЭКРАН: Выбор предмета для экзамена
# ═══════════════════════════════════════════════════════════
def get_exam_subjects_keyboard(grade: str = "5_9") -> InlineKeyboardMarkup:
    """Список предметов зависит от экзамена"""
    if grade == "10_11":
        # ЕГЭ предметы
        rows = [
            [
                InlineKeyboardButton(text="📐 Математика (профиль)", callback_data="exam_math_profile"),
                InlineKeyboardButton(text="📊 Математика (база)", callback_data="exam_math_base"),
            ],
            [InlineKeyboardButton(text="📝 Русский язык", callback_data="exam_russian")],
            [
                InlineKeyboardButton(text="⚛️ Физика", callback_data="exam_physics"),
                InlineKeyboardButton(text="⚗️ Химия", callback_data="exam_chemistry"),
            ],
            [
                InlineKeyboardButton(text="🧬 Биология", callback_data="exam_biology"),
                InlineKeyboardButton(text="📜 История", callback_data="exam_history"),
            ],
            [
                InlineKeyboardButton(text="🏛️ Обществознание", callback_data="exam_social"),
                InlineKeyboardButton(text="🌍 География", callback_data="exam_geography"),
            ],
            [
                InlineKeyboardButton(text="📖 Литература", callback_data="exam_literature"),
                InlineKeyboardButton(text="💻 Информатика", callback_data="exam_informatics"),
            ],
            [
                InlineKeyboardButton(text="🇬🇧 Английский", callback_data="exam_english"),
                InlineKeyboardButton(text="🇩🇪 Немецкий", callback_data="exam_german"),
            ],
        ]
    else:
        # ОГЭ предметы
        rows = [
            [
                InlineKeyboardButton(text="📐 Математика", callback_data="exam_math_oge"),
                InlineKeyboardButton(text="📝 Русский язык", callback_data="exam_russian_oge"),
            ],
            [
                InlineKeyboardButton(text="⚛️ Физика", callback_data="exam_physics_oge"),
                InlineKeyboardButton(text="⚗️ Химия", callback_data="exam_chemistry_oge"),
            ],
            [
                InlineKeyboardButton(text="🧬 Биология", callback_data="exam_biology_oge"),
                InlineKeyboardButton(text="📜 История", callback_data="exam_history_oge"),
            ],
            [
                InlineKeyboardButton(text="🏛️ Обществознание", callback_data="exam_social_oge"),
                InlineKeyboardButton(text="🌍 География", callback_data="exam_geography_oge"),
            ],
            [
                InlineKeyboardButton(text="📖 Литература", callback_data="exam_literature_oge"),
                InlineKeyboardButton(text="💻 Информатика", callback_data="exam_informatics_oge"),
            ],
            [
                InlineKeyboardButton(text="🇬🇧 Английский", callback_data="exam_english_oge"),
                InlineKeyboardButton(text="🇩🇪 Немецкий", callback_data="exam_german_oge"),
            ],
        ]

    rows.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════
#  ЭКРАН: Практика — выбор предмета
# ═══════════════════════════════════════════════════════════
def get_practice_subjects_keyboard(grade: str = "5_9") -> InlineKeyboardMarkup:
    """Выбор предмета для практики"""
    rows = [
        [
            InlineKeyboardButton(text="📐 Математика", callback_data="practice_math"),
            InlineKeyboardButton(text="📝 Русский язык", callback_data="practice_russian"),
        ],
        [
            InlineKeyboardButton(text="⚛️ Физика", callback_data="practice_physics"),
            InlineKeyboardButton(text="⚗️ Химия", callback_data="practice_chemistry"),
        ],
        [
            InlineKeyboardButton(text="🧬 Биология", callback_data="practice_biology"),
            InlineKeyboardButton(text="🏛️ Обществознание", callback_data="practice_social"),
        ],
        [
            InlineKeyboardButton(text="💻 Информатика", callback_data="practice_informatics"),
            InlineKeyboardButton(text="🇬🇧 Английский", callback_data="practice_english"),
        ],
        [InlineKeyboardButton(text="🎲 Случайный предмет", callback_data="practice_random")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════
#  ОСТАЛЬНЫЕ КЛАВИАТУРЫ (без изменений)
# ═══════════════════════════════════════════════════════════
def get_settings_keyboard(current_model: str = "standard") -> InlineKeyboardMarkup:
    if current_model == "standard":
        std_text = "✅ Стандарт"
        adv_text = "🧠 Продвинутая"
    else:
        std_text = "⚡ Стандарт"
        adv_text = "✅ Продвинутая"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=std_text, callback_data="set_model_standard")],
        [InlineKeyboardButton(text=adv_text, callback_data="set_model_advanced")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")]
    ])


def get_doc_format_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📘 DOCX", callback_data="doc_format_docx"),
            InlineKeyboardButton(text="📕 PDF", callback_data="doc_format_pdf"),
        ],
        [InlineKeyboardButton(text="⬅️ Отмена", callback_data="doc_format_cancel")]
    ])


def get_subscribe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Базовый — 299₽/мес", callback_data="buy_basic")],
        [InlineKeyboardButton(text="🔸 Расширенный — 499₽/мес", callback_data="buy_extended")],
        [InlineKeyboardButton(text="💎 Премиум — 990₽/мес", callback_data="buy_premium")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
    ])


def get_task_keyboard(has_answer: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура при решении задачи"""
    rows = [
        [InlineKeyboardButton(text="💡 Дай подсказку", callback_data="get_hint")],
        [InlineKeyboardButton(text="💡 Подробное объяснение", callback_data="get_explanation")],
    ]
    if has_answer:
        rows.append([InlineKeyboardButton(text="✅ Показать ответ", callback_data="show_answer")])
    rows.append([
        InlineKeyboardButton(text="➡️ Следующая задача", callback_data="next_task"),
        InlineKeyboardButton(text="❌ Пропустить", callback_data="skip_task"),
    ])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_back_keyboard(callback: str = "back_to_main") -> InlineKeyboardMarkup:
    """Простая кнопка 'Назад'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data=callback)]
    ])
