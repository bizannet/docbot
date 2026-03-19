# bot.py
import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN, STATS_GROUP_ID, TIMEZONE, LOGS_DIR, STATS_DB, ADMIN_ID
from stats.collector import init_stats_table
from stats.reporter import schedule_stats_reports

# Роутеры главного меню и поддержки
from start import router as start_router
from support import router as support_router

# Роутеры документов для сайта
from documents.website.privacy.flow import router as website_privacy_router
from documents.website.consent.flow import router as website_consent_router
from documents.website.terms.flow import router as website_terms_router
from documents.website.newsletter.flow import router as website_newsletter_router
from documents.website.advertising.flow import router as website_advertising_router

# Роутеры документов для бота
from documents.botdoc.privacy.flow import router as botdoc_privacy_router
from documents.botdoc.consent.flow import router as botdoc_consent_router
from documents.botdoc.terms.flow import router as botdoc_terms_router
from documents.botdoc.newsletter.flow import router as botdoc_newsletter_router
from documents.botdoc.advertising.flow import router as botdoc_advertising_router

# =============================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


# =============================================================================
# ОБРАБОТЧИК ОШИБОК
# =============================================================================

async def on_error(event: ErrorEvent, bot: Bot) -> None:
    """Глобальный обработчик ошибок"""
    logger.error(f"❌ Ошибка: {event.exception}", exc_info=event.exception)

    if event.update.message:
        await bot.send_message(
            chat_id=event.update.message.chat.id,
            text="⚠️ Произошла ошибка. Попробуйте ещё раз или напишите в поддержку."
        )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ <b>Ошибка в боте</b>\n\n"
                 f"Пользователь: {event.update.message.from_user.id if event.update.message else 'N/A'}\n"
                 f"Ошибка: {type(event.exception).__name__}: {event.exception}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")


# =============================================================================
# ХУКИ ЗАПУСКА
# =============================================================================

async def on_startup(bot: Bot):
    """Выполняется при старте бота"""
    logger.info("🚀 Бот запущен")
    try:
        me = await bot.get_me()
        logger.info(f"👤 Бот: @{me.username} (ID: {me.id})")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить информацию о боте: {e}")


# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================

async def main():
    """Точка входа"""

    # Инициализация таблицы статистики
    init_stats_table()
    logger.info("📊 Таблица статистики инициализирована")

    # Инициализация бота и диспетчера
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Регистрация обработчика ошибок
    dp.errors.register(on_error)

    # Подключение роутеров
    dp.include_router(start_router)  # Главное меню
    dp.include_router(support_router)  # Поддержка

    # Документы для сайта
    dp.include_router(website_privacy_router)  # Политика конфиденциальности
    dp.include_router(website_consent_router)  # Согласие на обработку ПД
    dp.include_router(website_terms_router)  # Пользовательское соглашение
    dp.include_router(website_newsletter_router)  # Согласие на рассылку
    dp.include_router(website_advertising_router)  # Согласие на рекламу

    # Документы для бота
    dp.include_router(botdoc_privacy_router)  # Политика конфиденциальности
    dp.include_router(botdoc_consent_router)  # Согласие на обработку ПД
    dp.include_router(botdoc_terms_router)  # Пользовательское соглашение
    dp.include_router(botdoc_newsletter_router)  # Согласие на рассылку
    dp.include_router(botdoc_advertising_router)  # Согласие на рекламу

    # Планировщик задач (отчёты в 10:00 МСК)
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    schedule_stats_reports(scheduler, bot, STATS_GROUP_ID)
    scheduler.start()
    logger.info("⏰ Планировщик отчётов запущен")

    # Хук при старте
    dp.startup.register(on_startup)

    # Запуск polling
    logger.info("▶️ Запуск polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
        print("🛑 Бот остановлен")
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка при запуске: {e}", exc_info=True)
        print(f"💥 Ошибка: {e}")