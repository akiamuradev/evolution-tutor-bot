from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..services import db
from ..modules import get_exam_subjects_keyboard, get_settings_keyboard

router = Router()


@router.callback_query(F.data == "show_features")
async def show_features(c: CallbackQuery):
    """Показать возможности бота"""
    try:
        with open('/app/src/bot_features.txt', 'r', encoding='utf-8') as f:
            features_text = f.read()
        # Отправляем отдельным сообщением, т.к. текст длинный
        await c.message.answer(features_text)
    except Exception:
        await c.message.answer(
            "📚 ВОЗМОЖНОСТИ БОТА\n\n"
            "💬 Чат-репетитор по всем предметам\n"
            "🎓 Подготовка к ОГЭ/ЕГЭ\n"
            "📊 Построение графиков\n"
            "📐 Математические формулы\n"
            "📄 Создание документов DOCX/PDF\n"
            "📸 OCR — распознавание текста с фото\n"
            "🎤 Голосовые ответы\n"
            "🤔 Анимация 'Думаю...'"
        )
    await c.answer()


@router.callback_query(F.data == "exam_prep")
async def exam_prep_callback(c: CallbackQuery):
    """Обработка кнопки 'Подготовка к ОГЭ/ЕГЭ' из меню"""
    await c.message.edit_text(
        "🎓 ПОДГОТОВКА К ОГЭ/ЕГЭ\n\nВыбери предмет:",
        reply_markup=get_exam_subjects_keyboard()
    )
    await c.answer()


@router.callback_query(F.data == "settings")
async def show_settings(c: CallbackQuery):
    """Показать настройки"""
    u = await db.get_user(c.from_user.id)
    current_model = u.get('preferred_model', 'standard')
    await c.message.edit_text(
        "⚙️ НАСТРОЙКИ\n\n"
        "Выберите модель ИИ:",
        reply_markup=get_settings_keyboard(current_model)
    )
    await c.answer()

@router.callback_query(F.data == "set_model_standard")
async def set_model_standard(c: CallbackQuery):
    """Установить стандартную модель"""
    await db.set_preferred_model(c.from_user.id, 'standard')
    await c.message.edit_text(
        "⚙️ НАСТРОЙКИ\n\n"
        "Выберите модель ИИ:",
        reply_markup=get_settings_keyboard('standard')
    )
    await c.answer("✅ Модель изменена", show_alert=True)

@router.callback_query(F.data == "set_model_advanced")
async def set_model_advanced(c: CallbackQuery):
    """Установить продвинутую модель"""
    await db.set_preferred_model(c.from_user.id, 'advanced')
    await c.message.edit_text(
        "⚙️ НАСТРОЙКИ\n\n"
        "Выберите модель ИИ:",
        reply_markup=get_settings_keyboard('advanced')
    )
    await c.answer("✅ Модель изменена", show_alert=True)

