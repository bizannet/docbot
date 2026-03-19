# utils/validators.py
import re
from typing import Union

def amount_to_words(amount: Union[str, float, int]) -> str:
    """
    Преобразует числовую сумму в строку с прописью.
    Формат: "542 036 рублей 00 копеек (пятьсот сорок две тысячи тридцать шесть рублей 00 коп.)"

    :param amount: Сумма как строка, int или float (например, "542036" или 542036.50)
    :return: Отформатированная строка с прописью
    """
    try:
        amount_float = float(str(amount).replace(" ", "").replace(",", "."))
    except (ValueError, TypeError):
        return "0 рублей 00 копеек (ноль рублей 00 коп.)"

    rub = int(amount_float)
    kop = int(round((amount_float - rub) * 100))

    # Корректировка, если копейки = 100
    if kop == 100:
        rub += 1
        kop = 0

    # Форматируем цифры: 542036 → "542 036"
    amount_formatted = f"{rub:,}".replace(",", " ")
    amount_formatted += f" рублей {kop:02d} копеек"

    # Словари для преобразования чисел в слова
    units = ["", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
    teens = ["десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать", "пятнадцать",
             "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"]
    tens = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
    hundreds = ["", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот", "семьсот", "восемьсот", "девятьсот"]

    # Специальные формы для тысяч (женский род)
    units_thousands = ["", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]

    def convert_number(n: int, for_thousands: bool = False) -> str:
        """Преобразует число до 999 999 в слова"""
        if n == 0:
            return ""

        words = []

        # Миллионы
        if n >= 1_000_000:
            millions = n // 1_000_000
            words.append(convert_number(millions, False))
            # Склонение для миллионов
            last_digit = millions % 10
            last_two_digits = millions % 100
            if 5 <= last_two_digits <= 20 or last_digit == 0 or last_digit >= 5:
                words.append("миллионов")
            elif last_digit == 1:
                words.append("миллион")
            else:
                words.append("миллиона")
            n %= 1_000_000

        # Тысячи
        if n >= 1_000:
            thousands_value = n // 1_000

            # Преобразуем тысячи в слова
            if thousands_value >= 100:
                words.append(hundreds[thousands_value // 100])
                thousands_value %= 100
            if thousands_value >= 20:
                words.append(tens[thousands_value // 10])
                thousands_value %= 10
            if 10 <= thousands_value < 20:
                words.append(teens[thousands_value - 10])
            elif thousands_value > 0:
                words.append(units_thousands[thousands_value] if for_thousands else units[thousands_value])

            # Склонение для тысяч
            last_digit = thousands_value % 10
            last_two_digits = thousands_value % 100
            if 5 <= last_two_digits <= 20 or last_digit == 0 or last_digit >= 5:
                words.append("тысяч")
            elif last_digit == 1:
                words.append("тысяча")
            else:
                words.append("тысячи")

            n %= 1_000

        # Сотни
        if n >= 100:
            words.append(hundreds[n // 100])
            n %= 100

        # Десятки и единицы
        if n >= 20:
            words.append(tens[n // 10])
            n %= 10
        if 10 <= n < 20:
            words.append(teens[n - 10])
            n = 0
        if 0 < n < 10:
            words.append(units_thousands[n] if for_thousands else units[n])

        return " ".join(words).strip()

    # Склонение для рублей
    rub_word = "рублей"
    last_digit = rub % 10
    last_two_digits = rub % 100
    if 5 <= last_two_digits <= 20:
        rub_word = "рублей"
    elif last_digit == 1:
        rub_word = "рубль"
    elif 2 <= last_digit <= 4:
        rub_word = "рубля"

    # Склонение для копеек
    kop_word = "копеек"
    last_digit_kop = kop % 10
    last_two_digits_kop = kop % 100
    if 5 <= last_two_digits_kop <= 20:
        kop_word = "копеек"
    elif last_digit_kop == 1:
        kop_word = "копейка"
    elif 2 <= last_digit_kop <= 4:
        kop_word = "копейки"

    # Преобразуем рубли в слова
    rub_words = convert_number(rub, False) if rub > 0 else "ноль"
    kop_words = f"{kop:02d}"  # Копейки всегда цифрами

    # Формируем пропись в скобках
    words_in_brackets = f"({rub_words} {rub_word} {kop_words} {kop_word})"

    # Итоговая строка: цифры + пропись
    return f"{amount_formatted} {words_in_brackets}"


def validate_inn(value: str) -> tuple[bool, str]:
    value = re.sub(r"\D", "", value)  # Убираем всё кроме цифр

    if len(value) not in (10, 12):
        return False, "ИНН должен содержать 10 или 12 цифр"

    if not value.isdigit():
        return False, "ИНН должен содержать только цифры"

    if len(value) == 10:
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        checksum = sum(int(value[i]) * coefficients[i] for i in range(9)) % 11 % 10
        if checksum != int(value[9]):
            return False, "Неверный контрольный номер ИНН"

    return True, ""


def validate_ogrn(value: str) -> tuple[bool, str]:
    value = re.sub(r"\D", "", value)

    if len(value) not in (13, 15):
        return False, "ОГРН должен содержать 13 цифр, ОГРНИП — 15 цифр"

    if not value.isdigit():
        return False, "ОГРН должен содержать только цифры"

    n = len(value)
    checksum = int(value[:-1]) % (11 if n == 13 else 13)
    checksum = checksum % 10
    if checksum != int(value[-1]):
        return False, "Неверный контрольный номер ОГРН"

    return True, ""


def validate_email(value: str) -> tuple[bool, str]:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value.strip()):
        return False, "Неверный формат email"
    return True, ""


def validate_phone(value: str) -> tuple[bool, str]:
    cleaned = re.sub(r"[^\d+]", "", value)

    if cleaned.startswith("+7"):
        digits = cleaned[2:]
    elif cleaned.startswith("8") or cleaned.startswith("7"):
        digits = cleaned[1:]
    else:
        return False, "Телефон должен начинаться с +7, 7 или 8"

    if len(digits) != 10 or not digits.isdigit():
        return False, "Телефон должен содержать 10 цифр после кода"

    return True, ""


def validate_amount(value: str) -> tuple[bool, str]:
    cleaned = value.strip().replace(" ", "").replace(",", ".")
    pattern = r'^\d+(\.\d{1,2})?$'
    if not re.match(pattern, cleaned):
        return False, "Сумма должна быть числом (например, 50000 или 50000.50)"

    try:
        amount = float(cleaned)
        if amount <= 0:
            return False, "Сумма должна быть больше нуля"
        if amount > 1_000_000_000:
            return False, "Сумма слишком большая"
    except ValueError:
        return False, "Неверный формат суммы"

    return True, ""


VALIDATORS = {
    "inn": validate_inn,
    "ogrn": validate_ogrn,
    "email": validate_email,
    "phone": validate_phone,
    "amount": validate_amount,
}


def validate_field(field_type: str, value: str) -> tuple[bool, str]:
    if field_type not in VALIDATORS:
        return True, ""

    return VALIDATORS[field_type](value)