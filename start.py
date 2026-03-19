# start.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import CHANNEL_ID, ADMIN_ID
from stats.podpiska import check_subscription

router = Router()


# =============================================================================
# КЛАВИАТУРЫ
# =============================================================================

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню: 2 категории + поддержка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌐 Для сайта", callback_data="category:website"),
            InlineKeyboardButton(text="🤖 Для бота", callback_data="category:bot"),
        ],
        [
            InlineKeyboardButton(text="❓ Поддержка", callback_data="support"),
        ],
    ])


def get_website_menu_keyboard() -> InlineKeyboardMarkup:
    """Подменю документов для сайта (кнопки попарно)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 Политика ПД", callback_data="doc:website_privacy"),
            InlineKeyboardButton(text="📄 Согласие на ПД", callback_data="doc:website_consent"),
        ],
        [
            InlineKeyboardButton(text="📬 Рассылка", callback_data="doc:website_newsletter"),
            InlineKeyboardButton(text="📢 Реклама", callback_data="doc:website_advertising"),
        ],
        [
            InlineKeyboardButton(text="📄 Польз. соглашение", callback_data="doc:website_terms"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back"),
        ],
    ])


def get_botdoc_menu_keyboard() -> InlineKeyboardMarkup:
    """Подменю документов для бота (кнопки попарно)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 Политика ПД", callback_data="doc:bot_privacy"),
            InlineKeyboardButton(text="📄 Согласие на ПД", callback_data="doc:bot_consent"),
        ],
        [
            InlineKeyboardButton(text="📬 Рассылка", callback_data="doc:bot_newsletter"),
            InlineKeyboardButton(text="📢 Реклама", callback_data="doc:bot_advertising"),
        ],
        [
            InlineKeyboardButton(text="📄 Польз. соглашение", callback_data="doc:bot_terms"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back"),
        ],
    ])


# =============================================================================
# ТЕКСТЫ
# =============================================================================

def get_main_menu_text() -> str:
    """Текст главного меню (HTML-разметка)"""
    return (
        "👋 <b>Добро пожаловать в сервис умного документооборота!</b>\n\n"
        "Просто ответьте на несколько вопросов — и я сгенерирую готовый документ за 5 минут.\n\n"
        "✨ <b>Что вы получите прямо в этом чате:</b>\n\n"
        "• <b>Автогенерацию</b> — просто ответьте на вопросы, и документ заполнится автоматически.\n"
        "• <b>Форматы PDF и Word</b> — готовый файл можно скачать и сразу использовать.\n\n"
        "💼 <b>В моей базе доступны документы:</b>\n"
        "• Для вашего сайта и бота: Политика ПД, Согласие, Соглашение, Рассылка, Реклама\n\n"
        "➡️ <b>Выберите категорию, чтобы начать</b>\n\n"
        "🔒 <i>Мы не храним ваши персональные данные. Вся информация удаляется автоматически после генерации документа.</i>"
    )


def get_website_menu_text() -> str:
    """Текст подменю для сайта"""
    return (
        "🌐 <b>Документы для сайта</b>\n\n"
        "Выберите документ для генерации:\n\n"
        "📄 <b>Политика ПД</b> — обязательный документ для сайта, собирающего данные\n"
        "📄 <b>Согласие на ПД</b> — отдельный документ для галочки «Согласен»\n"
        "📄 <b>Пользовательское соглашение</b> — правила использования сайта\n"
        "📬 <b>Согласие на рассылку</b> — для email/sms/push-рассылок\n"
        "📢 <b>Согласие на рекламу</b> — для cookie и таргетированной рекламы\n\n"
        "➡️ <b>Нажмите на документ, чтобы начать заполнение</b>"
    )


def get_botdoc_menu_text() -> str:
    """Текст подменю для бота"""
    return (
        "🤖 <b>Документы для Telegram-бота</b>\n\n"
        "Выберите документ для генерации:\n\n"
        "📄 <b>Политика ПД</b> — обязательный документ для бота, собирающего данные\n"
        "📄 <b>Согласие на ПД</b> — отдельный документ для галочки «Согласен»\n"
        "📄 <b>Пользовательское соглашение</b> — правила использования бота\n"
        "📬 <b>Согласие на рассылку</b> — для рассылок через бота и email\n"
        "📢 <b>Согласие на рекламу</b> — для аналитики и таргетированной рекламы\n\n"
        "➡️ <b>Нажмите на документ, чтобы начать заполнение</b>"
    )


# =============================================================================
# ФУНКЦИИ ПОКАЗА МЕНЮ (БЕЗ ПРОВЕРКИ ПОДПИСКИ)
# =============================================================================

async def show_main_menu(message: types.Message | types.CallbackQuery):
    """Показывает главное меню — БЕЗ проверки подписки"""
    if isinstance(message, types.CallbackQuery):
        send_method = message.message.edit_text
    else:
        send_method = message.answer

    # Показываем меню сразу, без проверки
    await send_method(
        text=get_main_menu_text(),
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


async def show_website_menu(callback: types.CallbackQuery):
    """Показывает подменю документов для сайта — БЕЗ проверки подписки"""
    await callback.message.edit_text(
        text=get_website_menu_text(),
        reply_markup=get_website_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


async def show_botdoc_menu(callback: types.CallbackQuery):
    """Показывает подменю документов для бота — БЕЗ проверки подписки"""
    await callback.message.edit_text(
        text=get_botdoc_menu_text(),
        reply_markup=get_botdoc_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# =============================================================================
# ХЕНДЛЕРЫ
# =============================================================================

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработка /start — показывает главное меню (без проверки подписки)"""
    await show_main_menu(message)


@router.callback_query(F.data == "menu:back")
async def on_menu_back(callback: types.CallbackQuery):
    """Глобальная кнопка «Назад в меню» — возвращает в главное меню"""
    await show_main_menu(callback)
    await callback.answer()


# --- Переходы из главного меню в подменю ---

@router.callback_query(F.data == "category:website")
async def on_category_website(callback: types.CallbackQuery):
    """Кнопка «Для сайта» в главном меню"""
    await show_website_menu(callback)


@router.callback_query(F.data == "category:bot")
async def on_category_bot(callback: types.CallbackQuery):
    """Кнопка «Для бота» в главном меню"""
    await show_botdoc_menu(callback)


# --- Обработчики для кнопок «Назад» из flow.py ---

@router.callback_query(F.data == "website:intro")
async def on_website_intro_back(callback: types.CallbackQuery):
    """Кнопка «Назад» из документов сайта — возвращает в меню сайта"""
    await show_website_menu(callback)
    await callback.answer()


@router.callback_query(F.data == "botdoc:intro")
async def on_botdoc_intro_back(callback: types.CallbackQuery):
    """Кнопка «Назад» из документов бота — возвращает в меню бота"""
    await show_botdoc_menu(callback)
    await callback.answer()