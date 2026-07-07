import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from ..modules import force_clean_text
from ..modules.ai_gateway import call_openrouter_guarded
from ..modules.generation_control import generation_registry

router = Router()


# ============ ГЕНЕРАЦИЯ С КНОПКОЙ ОТМЕНЫ ============

async def generate_with_cancel(
    message: types.Message,
    prompt: str,
    thinking_text: str = "🤔 Думаю...",
    animations: list = None,
    kind: str = "generation",
) -> tuple[str | None, bool]:
    """
    Генерирует ответ через ИИ с кнопкой "Отменить".
    Возвращает (результат, was_cancelled).
    """
    if animations is None:
        animations = ["🤔", "🤔.", "🤔..", "🤔...", "💭", "💭.", "💭..", "💭..."]
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_generation")]
    ])
    
    # Отправляем сообщение с анимацией
    thinking_msg = await message.answer(thinking_text, reply_markup=keyboard)
    
    # Сохраняем ID сообщения и chat_id в состоянии для отмены
    # (нужно для обработчика cancel_generation)
    
    cancelled = False
    result = None
    generation_task = None
    
    # Функция обновления анимации
    async def update_animation():
        nonlocal cancelled
        index = 0
        while not cancelled:
            anim = animations[index % len(animations)]
            if cancelled:
                break
            try:
                await thinking_msg.edit_text(f"{anim} {thinking_text}", reply_markup=keyboard)
                await asyncio.sleep(1.5)
            except Exception:
                await asyncio.sleep(1.5)
            index += 1
    
    # Запускаем анимацию в фоне
    animation_task = asyncio.create_task(update_animation())
    
    try:
        # Генерируем через OpenRouter
        generation_task = asyncio.create_task(
            call_openrouter_guarded(
                message.from_user.id,
                [{"role": "user", "content": prompt}],
                kind=kind,
                question=prompt,
            )
        )
        await generation_registry.register(
            message.from_user.id,
            generation_task,
            chat_id=thinking_msg.chat.id,
            message_id=thinking_msg.message_id,
        )
        guarded_response = await generation_task
        if guarded_response.busy:
            try:
                await thinking_msg.delete()
            except Exception:
                pass
            await message.answer(guarded_response.text)
            return None, True
        result = force_clean_text(guarded_response.text)
    except asyncio.CancelledError:
        cancelled = True
    except Exception as e:
        cancelled = True
        await thinking_msg.edit_text(f"❌ Ошибка генерации: {str(e)[:100]}", reply_markup=None)
        return None, True
    finally:
        if generation_task:
            await generation_registry.unregister(message.from_user.id, generation_task)
        # Останавливаем анимацию
        animation_task.cancel()
        try:
            await animation_task
        except asyncio.CancelledError:
            pass
    
    if cancelled:
        try:
            await thinking_msg.delete()
        except Exception:
            pass
        await message.answer("⏹️ Генерация остановлена.")
        return None, True
    
    # Удаляем сообщение с анимацией
    try:
        await thinking_msg.delete()
    except Exception:
        pass
    
    return result, False


@router.callback_query(F.data == "cancel_generation")
async def cancel_generation(c: CallbackQuery, state: FSMContext):
    """Отменяет текущую генерацию"""
    cancelled = await generation_registry.cancel(c.from_user.id)
    await c.answer("⏹️ Останавливаю генерацию" if cancelled else "Активной генерации нет")
    
    # Очищаем состояние
    await state.clear()
    
    # Удаляем сообщение с анимацией
    try:
        await c.message.delete()
    except Exception:
        pass
    
    if not cancelled:
        return
