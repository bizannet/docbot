# documents/website/newsletter/logic.py
from datetime import datetime


def prepare_newsletter_data(user_data: dict) -> dict:
    """
    Подготавливает данные для генерации Согласия на рассылку.

    :param user_data: Сырые ответы из опроса
    :return: Готовый словарь для подстановки в Jinja2-шаблон
    """
    data = user_data.copy()

    # Авто-дата
    data["consent_date"] = datetime.now().strftime("%d.%m.%Y")

    # Фильтрация условных полей
    if data.get("operator_type") not in ["ИП", "ООО"]:
        data.pop("operator_ogrn", None)

    if data.get("newsletter_types") and "✅ Другое (укажу вручную)" not in data.get("newsletter_types", []):
        data.pop("newsletter_types_other", None)

    if data.get("newsletter_content") and "✅ Другое (укажу вручную)" not in data.get("newsletter_content", []):
        data.pop("newsletter_content_other", None)

    if data.get("newsletter_frequency") != "Другая частота (укажу вручную)":
        data.pop("newsletter_frequency_custom", None)

    return data