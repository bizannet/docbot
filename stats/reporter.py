# stat/reporter.py
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import STATS_DB, TIMEZONE


def _get_db_connection():
    """Создает подключение к базе статистики"""
    conn = sqlite3.connect(str(STATS_DB))
    conn.row_factory = sqlite3.Row
    return conn


def _get_stats_for_period(start_date: datetime, end_date: datetime) -> dict:
    """
    Получает статистику за период из SQLite.
    Возвращает: количество пользователей, генераций, топ документов, список ID.
    """
    conn = _get_db_connection()
    cursor = conn.cursor()

    # Запрос: только анонимные данные (user_id, doc_name, timestamp)
    query = """
        SELECT user_id, doc_name, timestamp 
        FROM stats 
        WHERE timestamp >= ? AND timestamp < ?
        ORDER BY timestamp DESC
    """
    cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {
            "users_count": 0,
            "generations_count": 0,
            "top_docs": [],
            "user_ids": []
        }

    # Считаем уникальных пользователей
    unique_users = set(row["user_id"] for row in rows)

    # Считаем генерации по документам
    doc_counts = {}
    for row in rows:
        doc_name = row["doc_name"]
        doc_counts[doc_name] = doc_counts.get(doc_name, 0) + 1

    # Топ-3 документа
    top_docs = sorted(doc_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "users_count": len(unique_users),
        "generations_count": len(rows),
        "top_docs": top_docs,
        "user_ids": sorted(unique_users)
    }


def _format_report_text(stats: dict, period_label: str) -> str:
    """Форматирует статистику в текст для Telegram"""
    if stats["generations_count"] == 0:
        return f"📊 {period_label}\n\nЗа период нет активных генераций."

    # Формируем строку топ-документов
    top_lines = "\n".join(f"• {name} — {count}" for name, count in stats["top_docs"])

    # Формируем список ID (максимум 10, чтобы не спамить)
    ids_sample = stats["user_ids"][:10]
    ids_text = ", ".join(str(uid) for uid in ids_sample)
    if len(stats["user_ids"]) > 10:
        ids_text += f" и ещё {len(stats['user_ids']) - 10}"

    return (
        f"📊 {period_label}\n\n"
        f"👥 Пользователи: {stats['users_count']}\n"
        f"📄 Всего генераций: {stats['generations_count']}\n\n"
        f"📋 Топ документов:\n{top_lines}\n\n"
        f"👤 ID пользователей:\n{ids_text}"
    )


async def _send_report(bot: Bot, group_id: str, start_date: datetime, end_date: datetime, period_label: str):
    """Внутренняя функция: получает статистику и отправляет отчёт"""
    stats = _get_stats_for_period(start_date, end_date)
    text = _format_report_text(stats, period_label)

    try:
        await bot.send_message(chat_id=group_id, text=text, parse_mode="HTML")
    except Exception as e:
        # Логируем ошибку, но не ломаем бота
        print(f"❌ Не удалось отправить отчёт: {e}")


async def send_daily_report(bot: Bot, group_id: str):
    """Ежедневный отчёт: за вчерашний день"""
    today = datetime.now(TIMEZONE).date()
    yesterday_start = datetime.combine(today - timedelta(days=1), datetime.min.time(), tzinfo=TIMEZONE)
    yesterday_end = datetime.combine(today, datetime.min.time(), tzinfo=TIMEZONE)

    await _send_report(bot, group_id, yesterday_start, yesterday_end,
                       f"Отчёт за {yesterday_start.strftime('%d.%m.%Y')}")


async def send_monthly_report(bot: Bot, group_id: str):
    """Ежемесячный отчёт: за прошлый месяц"""
    today = datetime.now(TIMEZONE)
    first_day_current = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_prev = first_day_current - timedelta(seconds=1)
    first_day_prev = last_day_prev.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    label = f"Отчёт за {first_day_prev.strftime('%B %Y')}"
    await _send_report(bot, group_id, first_day_prev, first_day_current, label)


async def send_yearly_report(bot: Bot, group_id: str):
    """Ежегодный отчёт: за прошлый год"""
    today = datetime.now(TIMEZONE)
    first_day_current = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_prev = first_day_current - timedelta(seconds=1)
    first_day_prev = last_day_prev.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    label = f"Отчёт за {first_day_prev.year} год"
    await _send_report(bot, group_id, first_day_prev, first_day_current, label)


def schedule_stats_reports(scheduler: AsyncIOScheduler, bot: Bot, group_id: str):
    """
    Настраивает планировщик задач для отправки отчётов.
    Вызывается из bot.py при запуске.
    """
    # Ежедневный отчёт в 10:00 МСК
    scheduler.add_job(
        send_daily_report,
        trigger="cron",
        hour=10,
        minute=0,
        timezone=TIMEZONE,
        args=[bot, group_id],
        id="daily_report",
        replace_existing=True
    )

    # Ежемесячный отчёт 1-го числа в 10:00 МСК
    scheduler.add_job(
        send_monthly_report,
        trigger="cron",
        day=1,
        hour=10,
        minute=0,
        timezone=TIMEZONE,
        args=[bot, group_id],
        id="monthly_report",
        replace_existing=True
    )

    # Ежегодный отчёт 1 января в 10:00 МСК
    scheduler.add_job(
        send_yearly_report,
        trigger="cron",
        month=1,
        day=1,
        hour=10,
        minute=0,
        timezone=TIMEZONE,
        args=[bot, group_id],
        id="yearly_report",
        replace_existing=True
    )


__all__ = ["schedule_stats_reports"]
