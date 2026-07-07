from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from ..services import db
from ..modules import get_grade_keyboard, get_parent_consent_keyboard

router = Router()


@router.callback_query(F.data == "consent_parent")
async def parent_consent(c: CallbackQuery):
    """Согласие родителя для детей до 14 лет"""
    await c.message.edit_text(
        "👨‍👩‍👧 СОГЛАСИЕ РОДИТЕЛЯ\n\n"
        "Для пользователей до 14 лет требуется согласие родителя или законного представителя.\n\n"
        "Нажимая кнопку ниже, вы подтверждаете:\n"
        "• Я являюсь родителем/законным представителем\n"
        "• Я ознакомился с Политикой конфиденциальности\n"
        "• Я даю согласие на обработку персональных данных моего ребёнка\n"
        "• Я даю согласие на трансграничную передачу данных (если выбрана модель Qwen)",
        reply_markup=get_parent_consent_keyboard()
    )
    await c.answer()

@router.callback_query(F.data == "parent_consent_accept")
async def parent_consent_accept(c: CallbackQuery):
    """Родитель дал согласие"""
    await db.set_consent(c.from_user.id, parent_consent=True)
    await c.message.edit_text("✅ Согласие родителя получено!\n\n📚 Выбери свой класс:", reply_markup=get_grade_keyboard())
    await c.answer()

@router.callback_query(F.data == "consent_cancel")
async def consent_cancel(c: CallbackQuery):
    """Отмена согласия"""
    await c.message.edit_text("❌ Отменено\n\n/start — начать заново")
    await c.answer()

@router.message(Command("delete_my_data"))
async def cmd_delete_data(m: types.Message):
    """Удалить все данные пользователя"""
    await db.delete_user(m.from_user.id)
    await m.answer(
        "✅ Все ваши данные удалены\n\n"
        "Были удалены:\n"
        "• Ваш профиль\n"
        "• История прогресса\n"
        "• Все настройки\n\n"
        "Для повторного использования бота напишите /start"
    )

@router.message(Command("revoke_consent"))
async def cmd_revoke_consent(m: types.Message):
    """Отозвать согласие на обработку данных"""
    await db.revoke_consent(m.from_user.id)
    await m.answer(
        "✅ Согласие отозвано\n\n"
        "Ваши данные будут удалены в течение 30 дней.\n"
        "Для полного удаления используйте /delete_my_data"
    )

