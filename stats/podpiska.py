# stat/podpiska.py
from aiogram.exceptions import TelegramBadRequest


async def check_subscription(bot, user_id: int, channel_id: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest:
        return True
    except Exception:
        return True