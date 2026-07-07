from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from ..services import db
from ..modules import get_back_keyboard, get_practice_subjects_keyboard

router = Router()


# Обработчик "пустой" кнопки (разделители меню)
@router.callback_query(F.data == "noop")
async def noop_callback(cq: CallbackQuery):
    await cq.answer()  # Просто убираем "часики"


# ── УЧЁБА ──
@router.callback_query(F.data == "homework")
async def cb_homework(cq: CallbackQuery, state: FSMContext):
    await cq.message.edit_text(
        "📝 <b>Домашнее задание</b>\n\n"
        "Пришли мне задание:\n"
        "• Текстом — просто напиши условие\n"
        "• Фото — сфотографируй из учебника\n"
        "• Файлом — PDF или документ\n\n"
        "Я помогу разобраться и решить!",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )


@router.callback_query(F.data == "explain_topic")
async def cb_explain_topic(cq: CallbackQuery, state: FSMContext):
    await cq.message.edit_text(
        "💡 <b>Объяснить тему</b>\n\n"
        "Напиши, что нужно объяснить.\n"
        "Например:\n"
        "• «Объясни теорему Пифагора»\n"
        "• «Что такое причастный оборот?»\n"
        "• «Как работает электрический ток?»\n\n"
        "Объясню простыми словами, с примерами 📚",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )


@router.callback_query(F.data == "practice_menu")
async def cb_practice_menu(cq: CallbackQuery):
    u = await db.get_user(cq.from_user.id)
    grade = u.get("grade", "5_9")
    await cq.message.edit_text(
        "🏋️ <b>Практика задач</b>\n\n"
        "Выбери предмет, по которому хочешь потренироваться:",
        parse_mode="HTML",
        reply_markup=get_practice_subjects_keyboard(grade)
    )


# ── ИНСТРУМЕНТЫ ──
@router.callback_query(F.data == "tools_graph")
async def cb_tools_graph(cq: CallbackQuery):
    await cq.message.edit_text(
        "📈 <b>Построение графиков</b>\n\n"
        "Напиши функцию, например:\n"
        "• <code>y = x²</code>\n"
        "• <code>y = sin(x)</code>\n"
        "• <code>y = 2x + 1</code>\n\n"
        "Я построю красивый график 📊",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )


@router.callback_query(F.data == "tools_formula")
async def cb_tools_formula(cq: CallbackQuery):
    await cq.message.edit_text(
        "📐 <b>Решение примеров и формул</b>\n\n"
        "Пришли пример или уравнение:\n"
        "• <code>2x + 5 = 15</code>\n"
        "• <code>√(16) + 3²</code>\n"
        "• <code>E = mc², m=2, c=3</code>\n\n"
        "Решу и объясню каждый шаг ✏️",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )


@router.callback_query(F.data == "tools_doc")
async def cb_tools_doc(cq: CallbackQuery, state: FSMContext):
    await cq.message.edit_text(
        "📄 <b>Создание документов</b>\n\n"
        "Напиши тему, о которой нужно сделать документ.\n"
        "Например:\n"
        "• «Доклад о Пушкине»\n"
        "• «Конспект по биологии — клетка»\n"
        "• «Сочинение на тему Осень»\n\n"
        "Я создам готовый документ 📝",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )


@router.callback_query(F.data == "tools_ocr")
async def cb_tools_ocr(cq: CallbackQuery):
    await cq.message.edit_text(
        "📸 <b>Распознавание текста</b>\n\n"
        "Пришли фотографию с текстом:\n"
        "• Страница из учебника\n"
        "• Конспект в тетради\n"
        "• Документ или книга\n\n"
        "Я распознаю текст и смогу с ним работать 🔍",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )

