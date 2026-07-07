from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from ..states import PracticeStates
from ..services import task_search, trend_analyzer
from ..modules import get_exam_subjects_keyboard

router = Router()


# ============ КОМАНДЫ ОГЭ/ЕГЭ ============

@router.message(Command("exam"))
async def cmd_exam(m: types.Message):
    """Начать подготовку к экзамену"""
    await m.answer(" ПОДГОТОВКА К ОГЭ/ЕГЭ\n\nВыбери предмет:", reply_markup=get_exam_subjects_keyboard())

@router.message(Command("predict"))
async def cmd_predict(m: types.Message):
    """Показать прогноз трендов"""
    if not trend_analyzer:
        await m.answer("⚠️ Система аналитики ещё не настроена")
        return
    
    subject = m.text.split(maxsplit=1)[1] if len(m.text.split()) > 1 else "math-profile"
    
    await m.answer("🔮 Анализирую тренды...")
    report = await trend_analyzer.generate_prediction_report(subject)
    await m.answer(report)

@router.message(Command("practice"))
async def cmd_practice(m: types.Message, state: FSMContext):
    """Получить случайную задачу для тренировки"""
    if not task_search:
        await m.answer("⚠️ Система поиска ещё не настроена")
        return
    
    # Если указан предмет — используем его, иначе выбираем случайный из всех
    subject = m.text.split(maxsplit=1)[1] if len(m.text.split()) > 1 else None
    
    tasks = await task_search.get_random_tasks(subject, count=1)
    if not tasks:
        await m.answer("❌ Не найдено задач для тренировки")
        return
    
    task = tasks[0]
    
    # Сохраняем задачу в FSM
    await state.update_data(
        current_task=task,
        task_id=task['id'],
        correct_answer=task.get('answer', '')
    )
    await state.set_state(PracticeStates.waiting_answer)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Дай объяснение", callback_data="get_explanation")],
        [InlineKeyboardButton(text="❌ Пропустить", callback_data="skip_task")]
    ])
    
    await m.answer(
        f"📝 ЗАДАЧА ДЛЯ ТРЕНИРОВКИ\n\n"
        f"📚 {task['subject_name']}\n"
        f"🔢 Задание {task['task_number']} ({task['year']})\n"
        f"📌 Тема: {task['topic']}\n\n"
        f"📋 Условие:\n{task['condition']}\n\n"
        f"💬 Напиши свой ответ — я проверю!",
        reply_markup=keyboard
    )

@router.message(Command("solution"))
async def cmd_solution(m: types.Message):
    """Показать решение последней задачи"""
    await m.answer("📖 Решение будет здесь...")
