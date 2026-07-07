import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery
from ..states import DocStates
from ..services import db
from ..helpers import create_docx_file, create_pdf_file, get_user_grade
from ..modules import force_clean_text, get_document_prompt
from ..modules.ai_gateway import call_openrouter_guarded
from ..modules.generation_control import generation_registry

router = Router()


@router.callback_query(DocStates.waiting_for_format, F.data.startswith("doc_format_"))
async def process_doc_format(c: CallbackQuery, state: FSMContext):
    format_choice = c.data.replace("doc_format_", "")
    if format_choice == "cancel":
        await c.message.edit_text("❌ Отменено")
        await state.clear()
        await c.answer()
        return
    await c.message.edit_text(f"📄 Напиши тему для {format_choice.upper()}:")
    await state.update_data(format=format_choice)
    await state.set_state(DocStates.waiting_for_topic)
    await c.answer()

@router.message(DocStates.waiting_for_topic)
async def process_doc_topic(m: types.Message, state: FSMContext):
    data = await state.get_data()
    # Кнопка отмены
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏹️ Остановить", callback_data="cancel_generation")]
    ])
    thinking_msg = await m.answer("⏳ Генерирую документ...", reply_markup=cancel_keyboard)
    
    doc_format = data.get('format', 'docx')
    topic = m.text
    u = await db.get_user(m.from_user.id)
    grade = get_user_grade(u)
    
    prompt = get_document_prompt(grade, topic)
    generation_task = None
    try:
        generation_task = asyncio.create_task(
            call_openrouter_guarded(
                m.from_user.id,
                [{"role": "user", "content": prompt}],
                kind="document",
                question=topic,
            )
        )
        await generation_registry.register(
            m.from_user.id,
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
            await m.answer(guarded_response.text)
            await state.clear()
            return
        response = guarded_response.text
    except asyncio.CancelledError:
        try:
            await thinking_msg.delete()
        except Exception:
            pass
        await m.answer("⏹️ Генерация остановлена.")
        await state.clear()
        return
    except Exception as e:
        await thinking_msg.delete()
        await m.answer("❌ Не удалось сгенерировать документ. Попробуй еще раз.")
        await state.clear()
        return
    finally:
        if generation_task:
            await generation_registry.unregister(m.from_user.id, generation_task)
    try:
        await thinking_msg.delete()
    except Exception:
        pass
    
    if response.startswith("❌"):
        await m.answer(f"❌ {response}")
        await state.clear()
        return
    
    await m.answer(f"⏳ Создаю {doc_format.upper()}...")
    response = force_clean_text(response)
    
    if doc_format == 'docx':
        
        file_bytes = create_docx_file(response, f"ЭВО:ЛЮЦИЯ - {topic[:50]}")
        filename = "doc.docx"
        caption = f"📘 DOCX: {topic[:50]}"
    else:
        
        file_bytes = create_pdf_file(response, f"ЭВО:ЛЮЦИЯ - {topic[:50]}")
        filename = "doc.pdf"
        caption = f"📕 PDF: {topic[:50]}"
    
    if file_bytes:
        await m.bot.send_document(m.chat.id, BufferedInputFile(file=file_bytes, filename=filename), caption=caption)
    else:
        await m.answer("❌ Ошибка создания файла")
    await state.clear()
