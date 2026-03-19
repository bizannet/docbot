# stat/collector.py
import sqlite3
from datetime import datetime, timedelta

from config import STATS_DB, TIMEZONE


def _get_db_connection():
    conn = sqlite3.connect(str(STATS_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_stats_table():
    conn = _get_db_connection()
    cursor = conn.cursor()

    query = """
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doc_name TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """
    cursor.execute(query)
    conn.commit()
    conn.close()


def log_generation(user_id: int, doc_name: str):
    conn = _get_db_connection()
    cursor = conn.cursor()
    now = datetime.now(TIMEZONE).isoformat()

    query = """
        INSERT INTO stats (user_id, doc_name, timestamp)
        VALUES (?, ?, ?)
    """
    cursor.execute(query, (user_id, doc_name, now))
    conn.commit()
    conn.close()


def clear_old_stats(days: int = 365):
    conn = _get_db_connection()
    cursor = conn.cursor()

    cutoff_date = (datetime.now(TIMEZONE) - timedelta(days=days)).isoformat()

    query = """
        DELETE FROM stats
        WHERE timestamp < ?
    """
    cursor.execute(query, (cutoff_date,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted_count


__all__ = ["init_stats_table", "log_generation", "clear_old_stats"]