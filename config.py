# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
STATS_GROUP_ID = os.getenv("STATS_GROUP_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

if not TOKEN:
    raise ValueError("❌ TOKEN не указан в .env")
if not CHANNEL_ID:
    raise ValueError("❌ CHANNEL_ID не указан в .env")
if not STATS_GROUP_ID:
    raise ValueError("❌ STATS_GROUP_ID не указан в .env")
if not ADMIN_ID:
    raise ValueError("❌ ADMIN_ID не указан в .env")

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
STATS_DB = BASE_DIR / "stats" / "stats.db"

SESSION_TIMEOUT = 1800