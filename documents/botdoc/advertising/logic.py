# documents/botdoc/advertising/logic.py
from datetime import datetime


def prepare_bot_advertising_data(user_data: dict) -> dict:
    """
    Подготавливает данные для генерации Согласия на рекламу для бота.

    :param user_data: Сырые ответы из опроса
    :return: Готовый словарь для подстановки в Jinja2-шаблон
    """
    data = user_data.copy()

    # Авто-дата
    data["consent_date"] = datetime.now().strftime("%d.%m.%Y")

    # Фильтрация условных полей
    if data.get("operator_type") not in ["ИП", "ООО"]:
        data.pop("operator_ogrn", None)

    if data.get("advertising_tools") and "✅ Другое (укажу вручную)" not in data.get("advertising_tools", []):
        data.pop("advertising_tools_other", None)

    if data.get("data_collected") and "✅ Другое (укажу вручную)" not in data.get("data_collected", []):
        data.pop("data_collected_other", None)

    return data