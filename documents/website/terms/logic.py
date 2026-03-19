# documents/website/terms/logic.py
from datetime import datetime


def prepare_terms_data(user_data: dict) -> dict:
    """
    Подготавливает данные для генерации Пользовательского соглашения.

    :param user_data: Сырые ответы из опроса
    :return: Готовый словарь для подстановки в Jinja2-шаблон
    """
    data = user_data.copy()

    # Авто-дата публикации
    data["agreement_date"] = datetime.now().strftime("%d.%m.%Y")

    # Фильтрация условных полей
    if data.get("operator_type") not in ["ИП", "ООО"]:
        data.pop("operator_ogrn", None)

    if data.get("site_purpose") and "✅ Другое (укажу вручную)" not in data.get("site_purpose", []):
        data.pop("site_purpose_other", None)

    if data.get("user_obligations") and "✅ Другое (укажу вручную)" not in data.get("user_obligations", []):
        data.pop("user_obligations_other", None)

    if data.get("prohibited_actions") and "✅ Другое (укажу вручную)" not in data.get("prohibited_actions", []):
        data.pop("prohibited_actions_other", None)

    return data