import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from ..states import PracticeStates
from ..services import db
from ..modules import force_clean_text
from ..modules.ai_gateway import call_openrouter_guarded
from ..modules.generation_control import generation_registry
import logging


router = Router()
logger = logging.getLogger(__name__)
@router.message(PracticeStates.waiting_answer)
async def check_answer(m: types.Message, state: FSMContext):
    """Проверяет ответ ученика и сохраняет прогресс"""
    # Если это команда /solution или /skip — пропускаем
    if m.text and (m.text.startswith('/solution') or m.text.startswith('/skip')):
        return

    await db.record_activity(m.from_user.id)
    
    data = await state.get_data()
    task = data.get('current_task')
    correct_answer = str(data.get('correct_answer') or '')
    user_answer = str(m.text or '').strip()
    used_explanation = data.get('explanation') is not None
    
    if not task:
        await state.clear()
        return
    
    # Очищаем ответ
    user_clean = user_answer.lower().strip().replace(' ', '')
    correct_clean = correct_answer.lower().strip().replace(' ', '')
    
    # Проверяем правильность
    is_correct = user_clean == correct_clean or user_clean in correct_clean or correct_clean in user_clean
    
    # Сохраняем прогресс в БД
    task_id = task.get('id')
    if task_id:
        try:
            async with db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO student_progress (user_id, task_id, subject_id, topic, user_answer, is_correct, used_explanation)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, m.from_user.id, task_id, task.get('subject_id'), task.get('topic'), user_answer, is_correct, used_explanation)
        except Exception as e:
            logger.error(f"Ошибка сохранения прогресса: {e}")
    
    # Формируем ответ
    if is_correct:
        response = f"✅ ПРАВИЛЬНО!\n\nТвой ответ: {user_answer}\nВерный ответ: {correct_answer}\n\n🎉 Отличная работа!"
        
    else:
        response = f"❌ НЕПРАВИЛЬНО\n\nТвой ответ: {user_answer}\nВерный ответ: {correct_answer}\n\n"
        
        if task.get('solution'):
            response += f"📖 Решение:\n{task['solution']}\n\n"
        
        response += "💡 Попробуй ещё раз или напиши /practice для новой задачи"

    from .achievements import check_achievements

    achievements = await check_achievements(m.from_user.id)
    if achievements:
        response += f"\n\n{achievements}"
    
    await m.answer(response)
    await state.clear()

@router.message(Command("solution"))
async def cmd_solution_fsm(m: types.Message, state: FSMContext):
    """Показать решение текущей задачи"""
    data = await state.get_data()
    task = data.get('current_task')
    
    if not task:
        await m.answer("❌ Нет активной задачи. Напиши /practice чтобы получить новую.")
        return
    
    # Если ученик ещё не получил объяснение — предлагаем сначала его
    current_state = await state.get_state()
    if current_state == PracticeStates.waiting_answer.state:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💡 Сначала дай объяснение", callback_data="get_explanation")],
            [InlineKeyboardButton(text="✅ Сразу показать ответ", callback_data="force_show_answer")]
        ])
        await m.answer(
            "💡 Сначала попробуй понять задачу!\n\n"
            "Нажми 'Дай объяснение' — я помогу разобраться, но не дам готовый ответ.",
            reply_markup=keyboard
        )
        return
    
    # Если уже в состоянии can_see_answer — показываем ответ
    response = f"📖 РЕШЕНИЕ\n\n"
    response += f"📋 Условие:\n{task['condition']}\n\n"
    if task.get('solution'):
        response += f"💡 Решение:\n{task['solution']}\n\n"
    response += f"✅ Ответ: {task.get('answer', 'не указан')}"
    
    await m.answer(response)
    await state.clear()

@router.callback_query(F.data == "force_show_answer")
async def force_show_answer(c: CallbackQuery, state: FSMContext):
    """Принудительно показать ответ (если ученик настаивает)"""
    data = await state.get_data()
    task = data.get('current_task')
    
    if not task:
        await c.answer("❌ Нет активной задачи", show_alert=True)
        return
    
    response = f"📖 РЕШЕНИЕ\n\n"
    response += f"📋 Условие:\n{task['condition']}\n\n"
    if task.get('solution'):
        response += f"💡 Решение:\n{task['solution']}\n\n"
    response += f"✅ Ответ: {task.get('answer', 'не указан')}"
    
    await c.message.answer(response)
    await state.clear()
    await c.answer()

@router.message(Command("skip"))
async def cmd_skip(m: types.Message, state: FSMContext):
    """Пропустить задачу"""
    await state.clear()
    await m.answer("⏭️ Задача пропущена. Напиши /practice для новой задачи.")


@router.callback_query(F.data == "get_explanation", PracticeStates.waiting_answer)
async def get_explanation(c: CallbackQuery, state: FSMContext):
    """Запрашивает объяснение задачи у ИИ (без ответа) с кэшированием в БД"""
    await db.record_activity(c.from_user.id)
    data = await state.get_data()
    task = data.get('current_task')
    
    if not task:
        await c.answer("❌ Нет активной задачи", show_alert=True)
        return
    
    task_id = task.get('id')
    
    # 1. Сначала проверяем, есть ли объяснение в БД
    explanation = None
    if task_id:
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT explanation FROM fipi_tasks WHERE id = $1",
                task_id
            )
            if row and row['explanation']:
                explanation = row['explanation']
    
    # 2. Если нет — генерируем через OpenRouter (всегда!)
    if not explanation:
        await c.answer()
        # Отправляем сообщение с анимацией "Думаю"
        # Кнопка отмены
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏹️ Остановить", callback_data="cancel_generation")]
        ])
        thinking_msg = await c.message.answer("🤔 Думаю...", reply_markup=cancel_keyboard)
        
        # Функция обновления анимации
        animations = ["🤔", "🤔.", "🤔..", "🤔...", "💭", "💭.", "💭..", "💭..."]
        
        async def update_animation():
            index = 0
            while True:
                anim = animations[index % len(animations)]
                try:
                    await thinking_msg.edit_text(f"{anim} Генерирую объяснение...", reply_markup=cancel_keyboard)
                    await asyncio.sleep(1.5)
                except Exception:
                    await asyncio.sleep(1.5)
                index += 1
        
        prompt = f"""Ты — репетитор для школьников. Ученик решает задачу:

{str(task.get('condition') or '').strip()}

Объясни ему, как подступиться к этой задаче:
- Какие знания и формулы нужны
- На какие шаги разбить решение
- Дай подсказку, но НЕ показывай окончательный ответ

Пиши понятно, по шагам, без финального ответа. Используй красивые математические символы: √, π, α, β, γ, Δ, ∫, ∑."""
        
        try:
            # Запускаем анимацию в фоне
            animation_task = asyncio.create_task(update_animation())
            generation_task = None
            
            # Всегда используем OpenRouter для объяснений
            try:
                generation_task = asyncio.create_task(
                    call_openrouter_guarded(
                        c.from_user.id,
                        [{"role": "user", "content": prompt}],
                        kind="practice_explanation",
                        question=str(task.get("condition") or ""),
                    )
                )
                await generation_registry.register(
                    c.from_user.id,
                    generation_task,
                    chat_id=thinking_msg.chat.id,
                    message_id=thinking_msg.message_id,
                )
                guarded_response = await generation_task
                if guarded_response.busy:
                    animation_task.cancel()
                    try:
                        await animation_task
                    except asyncio.CancelledError:
                        pass
                    try:
                        await thinking_msg.delete()
                    except Exception:
                        pass
                    await c.message.answer(guarded_response.text)
                    return
                explanation = guarded_response.text
            except asyncio.CancelledError:
                animation_task.cancel()
                try:
                    await animation_task
                except asyncio.CancelledError:
                    pass
                try:
                    await thinking_msg.delete()
                except Exception:
                    pass
                await c.message.answer("⏹️ Генерация остановлена.")
                return
            except Exception as e:
                animation_task.cancel()
                try:
                    await animation_task
                except asyncio.CancelledError:
                    pass
                try:
                    await thinking_msg.delete()
                except Exception:
                    pass
                await c.message.answer("❌ Не удалось сгенерировать объяснение. Попробуй еще раз.")
                return
            finally:
                if generation_task:
                    await generation_registry.unregister(c.from_user.id, generation_task)
            
            # Останавливаем анимацию
            animation_task.cancel()
            try:
                await animation_task
            except asyncio.CancelledError:
                pass
            try:
                await thinking_msg.delete()
            except Exception:
                pass
            explanation = force_clean_text(explanation)
            if not explanation:
                await c.message.answer(
                    "Не получилось собрать объяснение для этой задачи. "
                    "Попробуй нажать кнопку ещё раз или пропусти задачу."
                )
                return
            
            # 3. Сохраняем объяснение в БД
            if task_id:
                async with db.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE fipi_tasks SET explanation = $1 WHERE id = $2",
                        explanation, task_id
                    )
                    logger.info(f"💾 Объяснение сохранено в БД для задачи {task_id}")
        except Exception as e:
            await c.message.answer(f"❌ Ошибка при генерации объяснения: {str(e)[:100]}")
            await c.answer()
            return
    else:
        await c.answer("⚡ Беру из кэша...")
        logger.info(f"⚡ Объяснение взято из кэша для задачи {task_id}")
    
    # 4. Показываем объяснение
    await state.update_data(explanation=explanation)
    await state.set_state(PracticeStates.can_see_answer)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сразу увидеть ответ", callback_data="show_answer")],
        [InlineKeyboardButton(text="💬 Напишу свой ответ", callback_data="continue_solving")]
    ])
    
    await c.message.answer(
        f"💡 ОБЪЯСНЕНИЕ\n\n{explanation}\n\n"
        f"Теперь попробуй решить сам или посмотри ответ 👇",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "show_answer", PracticeStates.can_see_answer)
async def show_answer(c: CallbackQuery, state: FSMContext):
    """Показывает точный ответ после объяснения"""
    await db.record_activity(c.from_user.id)
    data = await state.get_data()
    task = data.get('current_task')
    
    if not task:
        await c.answer("❌ Нет активной задачи", show_alert=True)
        return
    
    response = f"✅ ОТВЕТ\n\n"
    response += f"📋 Условие:\n{task['condition']}\n\n"
    if task.get('solution'):
        response += f"💡 Решение:\n{task['solution']}\n\n"
    response += f"🎯 Правильный ответ: {task.get('answer', 'не указан')}"
    
    await c.message.answer(response)
    await state.clear()
    await c.answer()

@router.callback_query(F.data == "continue_solving", PracticeStates.can_see_answer)
async def continue_solving(c: CallbackQuery, state: FSMContext):
    """Возвращает ученика к решению задачи"""
    await state.set_state(PracticeStates.waiting_answer)
    await c.message.answer("💬 Хорошо! Напиши свой ответ, я проверю.")
    await c.answer()

@router.callback_query(F.data == "skip_task", PracticeStates.waiting_answer)
async def skip_task_callback(c: CallbackQuery, state: FSMContext):
    """Пропустить задачу через кнопку"""
    await state.clear()
    await c.message.answer("⏭️ Задача пропущена. Напиши /practice для новой задачи.")
    await c.answer()
