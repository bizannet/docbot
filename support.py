# support.py
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


def get_support_keyboard() -> InlineKeyboardMarkup:
    """Кнопки: Написать админу + Назад в меню"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✍️ Написать", url="https://t.me/biz_annet"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад в меню", callback_data="menu:back"),
            ],
        ]
    )
    return keyboard


@router.callback_query(F.data == "support")
async def on_support_selected(callback: types.CallbackQuery):
    """Обработка кнопки «Поддержка» — БЕЗ проверки подписки"""
    await callback.message.edit_text(
        "❓ <b>Поддержка</b>\n\n"
        "По всем вопросам обращаться: @biz_annet",
        reply_markup=get_support_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()
