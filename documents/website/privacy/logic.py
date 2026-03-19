# documents/website/privacy/logic.py
from datetime import datetime


def prepare_privacy_data(user_data: dict) -> dict:
    """
    Подготавливает данные для генерации Политики конфиденциальности.

    :param user_ Сырые ответы из опроса
    :return: Готовый словарь для подстановки в Jinja2-шаблон
    """
    data = user_data.copy()

    # Авто-дата публикации
    data["policy_date"] = datetime.now().strftime("%d.%m.%Y")

    # Обработка multi_select полей (преобразуем списки в строки для шаблона)
    if isinstance(data.get("data_collected"), list):
        data["data_collected"] = data["data_collected"]

    if isinstance(data.get("processing_purposes"), list):
        data["processing_purposes"] = data["processing_purposes"]

    # Фильтрация условных полей
    if data.get("operator_type") not in ["ИП", "ООО"]:
        data.pop("operator_ogrn", None)

    if data.get("contact_phone") is None or data.get("contact_phone") == "":
        data.pop("contact_phone", None)

    if data.get("data_collected") and "✅ Другое (укажу вручную)" not in data.get("data_collected", []):
        data.pop("data_collected_other", None)

    if data.get("processing_purposes") and "✅ Другое (укажу вручную)" not in data.get("processing_purposes", []):
        data.pop("processing_purposes_other", None)

    if data.get("data_retention") != "Другой срок (укажу вручную)":
        data.pop("data_retention_custom", None)

    if data.get("third_parties") != "✅ Да, перечислю кому":
        data.pop("third_parties_list", None)

    return data