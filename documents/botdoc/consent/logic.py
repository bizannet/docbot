# documents/botdoc/consent/logic.py
from datetime import datetime


def prepare_bot_consent_data(user_data: dict) -> dict:
    """
    Подготавливает данные для генерации Согласия на обработку ПД для бота.

    :param user_data: Сырые ответы из опроса
    :return: Готовый словарь для подстановки в Jinja2-шаблон
    """
    data = user_data.copy()

    # Авто-дата
    data["consent_date"] = datetime.now().strftime("%d.%m.%Y")

    # Фильтрация условных полей
    if data.get("operator_type") not in ["ИП", "ООО"]:
        data.pop("operator_ogrn", None)

    if data.get("data_purposes") and "✅ Другое (укажу вручную)" not in data.get("data_purposes", []):
        data.pop("data_purposes_other", None)

    if data.get("consent_duration") != "Другой срок (укажу вручную)":
        data.pop("consent_duration_custom", None)

    if data.get("withdrawal_method") != "✅ Другой способ (укажу вручную)":
        data.pop("withdrawal_method_custom", None)

    return data