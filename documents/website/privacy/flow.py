# documents/website/privacy/flow.py
import json
from pathlib import Path
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID, CHANNEL_ID
from stats.podpiska import check_subscription
from stats.collector import log_generation
from documents.website.privacy.logic import prepare_privacy_data
from documents.base import DocumentGenerator
from documents.formats.pdf import generate_pdf
from documents.formats.word import generate_word

router = Router()


class PrivacyForm(StatesGroup):
    answering = State()


PRIVACY_INTRO_TEXT = (
    "📄 <b>Политика конфиденциальности для сайта</b>\n\n"
    "Обязательный документ по 152-ФЗ для любого сайта, который собирает данные пользователей.\n\n"
    "🔒 <b>Безопасность:</b> вы вводите данные только для генерации. После создания файла вся информация удаляется автоматически."
)

PRIVACY_WARNING_TEXT = (
    "📋 <b>Готовы заполнить документ?</b>\n\n"
    "Сейчас вам нужно будет ответить на <b>{questions_count}</b> вопросов.\n"
    "После этого я сразу пришлю готовый документ в чат.\n\n"
    "⏱️ Это займёт около 5 минут."
)

PRIVACY_COMPLETE_TEXT = (
    "✅ <b>Документ готов!</b>\n\n"
    "Файлы сформированы в двух форматах:\n"
    "📄 PDF — для размещения на сайте\n"
    "📝 Word — для редактирования\n\n"
    "Нажмите на файл, чтобы скачать."
)


def get_privacy_intro_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Заполнить", callback_data="privacy:fill")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="menu:back")],
    ])


def get_privacy_warning_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начнём", callback_data="privacy:start_questions")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="website:intro")],  # ← Возврат в меню сайта
    ])


def get_privacy_complete_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Заполнить ещё раз", callback_data="privacy:fill")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu:back")],
    ])


def get_question_keyboard(question: dict, skip_available: bool = False) -> InlineKeyboardMarkup:
    keyboard = []

    if question["type"] == "single_select":
        for option in question["options"]:
            keyboard.append([InlineKeyboardButton(text=option, callback_data=f"ans:{option}")])
    elif question["type"] == "multi_select":
        for option in question["options"]:
            keyboard.append([InlineKeyboardButton(text=option, callback_data=f"ans:{option}")])
        keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="ans:multi_done")])

    if skip_available:
        keyboard.append([InlineKeyboardButton(text="⏭️ Пропустить", callback_data="ans:skip")])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu:back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def load_questions() -> list:
    questions_path = Path(__file__).parent / "questions.json"
    with open(questions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_questions_count() -> int:
    return len(load_questions())


def get_next_question_index(current_index: int, answers: dict, questions: list) -> int:
    for i in range(current_index + 1, len(questions)):
        q = questions[i]
        if "conditional" in q and "show_if" in q["conditional"]:
            condition = q["conditional"]["show_if"]
            key = list(condition.keys())[0]
            allowed_values = condition[key]

            if isinstance(allowed_values, list):
                if answers.get(key) not in allowed_values:
                    continue
            elif not all(answers.get(k) == v for k, v in condition.items()):
                continue
        return i
    return -1


def is_skip_available(question: dict, answers: dict) -> bool:
    if question.get("skip_button") and not question.get("required", True):
        return True
    if "conditional" in question:
        condition = question["conditional"].get("show_if", {})
        if condition and not all(answers.get(k) == v for k, v in condition.items()):
            return True
    return False


def format_question_text(question: dict) -> str:
    text = question["text"]
    if "hint" in question:
        text += f"\n\n💡 {question['hint']}"
    if "example" in question:
        text += f"\nПример: {question['example']}"
    return text


async def show_privacy_intro(callback: types.CallbackQuery, check_sub: bool = True):
    user_id = callback.from_user.id

    if check_sub and user_id != ADMIN_ID:
        is_subscribed = await check_subscription(callback.bot, user_id, CHANNEL_ID)
        if not is_subscribed:
            clean_username = CHANNEL_ID.lstrip("@")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подписаться", url=f"https://t.me/{clean_username}")]
            ])
            await callback.message.edit_text(
                "❌ Доступ только для подписчиков канала.\nПодпишитесь и нажмите /start ещё раз.",
                reply_markup=keyboard
            )
            await callback.answer()
            return

    await callback.message.edit_text(
        text=PRIVACY_INTRO_TEXT,
        reply_markup=get_privacy_intro_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


async def show_privacy_warning(callback: types.CallbackQuery):
    questions_count = load_questions_count()
    text = PRIVACY_WARNING_TEXT.format(questions_count=questions_count)

    await callback.message.edit_text(
        text=text,
        reply_markup=get_privacy_warning_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


async def show_question(callback: types.CallbackQuery, fsm: FSMContext, question_index: int = 0):
    questions = load_questions()
    if question_index >= len(questions):
        await on_questionnaire_complete(callback, fsm)
        return

    question = questions[question_index]
    user_data = await fsm.get_data()
    answers = user_data.get("answers", {})

    if "conditional" in question and "show_if" in question["conditional"]:
        condition = question["conditional"]["show_if"]
        key = list(condition.keys())[0]
        allowed_values = condition[key]

        if isinstance(allowed_values, list):
            if answers.get(key) not in allowed_values:
                next_idx = get_next_question_index(question_index, answers, questions)
                if next_idx == -1:
                    await on_questionnaire_complete(callback, fsm)
                else:
                    await show_question(callback, fsm, next_idx)
                return
        elif not all(answers.get(k) == v for k, v in condition.items()):
            next_idx = get_next_question_index(question_index, answers, questions)
            if next_idx == -1:
                await on_questionnaire_complete(callback, fsm)
            else:
                await show_question(callback, fsm, next_idx)
            return

    text = format_question_text(question)
    skip_available = is_skip_available(question, answers)
    keyboard = get_question_keyboard(question, skip_available)

    await fsm.update_data(current_question_index=question_index)

    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def on_questionnaire_complete(callback: types.CallbackQuery, fsm: FSMContext):
    user_data = await fsm.get_data()
    answers = user_data.get("answers", {})

    prepared = prepare_privacy_data(answers)

    template_path = Path(__file__).parent / "template.html"
    gen = DocumentGenerator()
    html_content = gen.render_template(str(template_path), prepared)

    pdf_file = generate_pdf(html_content, "privacy_policy.pdf")
    word_file = generate_word(html_content, "privacy_policy.docx")

    await callback.message.answer(PRIVACY_COMPLETE_TEXT, parse_mode="HTML")
    await callback.message.answer_document(document=types.FSInputFile(pdf_file), caption="📄 PDF-версия")
    await callback.message.answer_document(document=types.FSInputFile(word_file), caption="📝 Word-версия")

    user_id = callback.from_user.id
    log_generation(user_id, "website_privacy")

    await fsm.clear()

    await callback.message.answer(
        "Что делаем дальше?",
        reply_markup=get_privacy_complete_keyboard()
    )


# =============================================================================
# ХЕНДЛЕРЫ (ОБРАТИ ВНИМАНИЕ НА CALLBACK_DATA)
# =============================================================================

@router.callback_query(F.data == "doc:website_privacy")  # ✅ ИСПРАВЛЕНО: было "category:website"
async def on_privacy_selected(callback: types.CallbackQuery):
    """Хендлер для кнопки «Политика ПД» в меню сайта"""
    await show_privacy_intro(callback, check_sub=True)


@router.callback_query(F.data == "website:intro")
async def on_website_intro_back(callback: types.CallbackQuery, fsm: FSMContext):
    """Кнопка «Назад» из документа — возвращает в меню сайта"""
    await fsm.clear()
    await show_privacy_intro(callback, check_sub=False)
    await callback.answer()


@router.callback_query(F.data == "privacy:fill")
async def on_privacy_fill_selected(callback: types.CallbackQuery):
    await show_privacy_warning(callback)
    await callback.answer()


@router.callback_query(F.data == "privacy:start_questions")
async def on_privacy_start_questions(callback: types.CallbackQuery, fsm: FSMContext):
    await fsm.set_state(PrivacyForm.answering)
    await fsm.update_data(answers={}, current_question_index=0)
    await show_question(callback, fsm, 0)
    await callback.answer()


@router.callback_query(PrivacyForm.answering, F.data.startswith("ans:"))
async def handle_answer(callback: types.CallbackQuery, fsm: FSMContext):
    answer_value = callback.data.split(":", 1)[1]
    user_data = await fsm.get_data()
    answers = user_data.get("answers", {})
    current_index = user_data.get("current_question_index", 0)
    questions = load_questions()

    if current_index >= len(questions):
        await on_questionnaire_complete(callback, fsm)
        return

    question = questions[current_index]
    step_name = question["step"]

    if answer_value == "skip":
        pass
    elif answer_value == "multi_done":
        pass
    else:
        if question["type"] == "multi_select":
            current_list = answers.get(step_name, [])
            if answer_value not in current_list:
                current_list.append(answer_value)
            answers[step_name] = current_list
        else:
            answers[step_name] = answer_value

    await fsm.update_data(answers=answers)

    next_idx = get_next_question_index(current_index, answers, questions)
    if next_idx == -1:
        await on_questionnaire_complete(callback, fsm)
    else:
        await show_question(callback, fsm, next_idx)
    await callback.answer()


@router.callback_query(F.data == "privacy:complete")
async def on_privacy_complete(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text=PRIVACY_COMPLETE_TEXT,
        reply_markup=get_privacy_complete_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PrivacyForm.answering)
async def handle_text_answer(message: types.Message, fsm: FSMContext):
    user_data = await fsm.get_data()
    answers = user_data.get("answers", {})
    current_index = user_data.get("current_question_index", 0)
    questions = load_questions()

    if current_index >= len(questions):
        return

    question = questions[current_index]
    step_name = question["step"]

    if "validate" in question:
        from utils.validators import validate_field
        is_valid, error = validate_field(question["validate"], message.text)
        if not is_valid:
            await message.answer(f"❌ {error}\n\nПопробуйте ещё раз:")
            return

    answers[step_name] = message.text
    await fsm.update_data(answers=answers)

    next_idx = get_next_question_index(current_index, answers, questions)
    if next_idx == -1:
        await on_questionnaire_complete(message, fsm)
    else:
        await show_question(message, fsm, next_idx)