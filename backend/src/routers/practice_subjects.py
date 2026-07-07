from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from ..states import PracticeStates
from ..services import task_search
from ..modules import get_back_keyboard, get_practice_subjects_keyboard, get_task_keyboard

router = Router()


# ── Обработчики для практики по предметам ──
@router.callback_query(F.data.startswith("practice_"))
async def cb_practice_subject(cq: CallbackQuery, state: FSMContext):
    subject_map = {
        "practice_math": "math",
        "practice_russian": "russian",
        "practice_physics": "physics",
        "practice_chemistry": "chemistry",
        "practice_biology": "biology",
        "practice_social": "social-studies",
        "practice_informatics": "informatics",
        "practice_english": "english",
        "practice_random": None,
    }
    
    subject_code = subject_map.get(cq.data)
    
    if not task_search:
        await cq.message.edit_text(
            "⚠️ Система поиска задач ещё настраивается.\n"
            "Попробуй позже!",
            reply_markup=get_back_keyboard()
        )
        return
    
    tasks = await task_search.get_random_tasks(subject_code, count=1)
    if not tasks:
        await cq.message.edit_text(
            "❌ Пока нет задач для этого предмета.\n"
            "Выбери другой:",
            reply_markup=get_practice_subjects_keyboard()
        )
        return
    
    task = tasks[0]
    await state.update_data(
        current_task=task,
        task_id=task['id'],
        correct_answer=task.get('answer', '')
    )
    await state.set_state(PracticeStates.waiting_answer)
    
    await cq.message.edit_text(
        f"📝 <b>ЗАДАЧА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 <b>{task['subject_name']}</b>\n"
        f"📌 Тема: <i>{task.get('topic', '—')}</i>\n\n"
        f"📋 <b>Условие:</b>\n{task['condition']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 Напиши свой ответ — я проверю!",
        parse_mode="HTML",
        reply_markup=get_task_keyboard(has_answer=bool(task.get('answer')))
    )
    await cq.answer()
