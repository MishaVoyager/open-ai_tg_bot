import base64
from re import Match

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from config.settings import CommonSettings
from domain.models import Visitor
from helpers import tghelper
from helpers.open_ai_helper import GPTModel, audio_to_text, text_to_audio, get_answer_from_friend, \
    get_english_teacher_comment, generate_image
from helpers.tghelper import get_inline_keyboard, get_random_processing_phrase, process_file_for_tg
from service.visitor_actions import change_visitor_model

router = Router()


class Modes(StatesGroup):
    conversation = State()
    monolog = State()
    images = State()


@router.message(Command("start", "help"))
async def start_handler(message: Message) -> None:
    text = """Бот для запросов в OpenAI к вашим услугам! 
Базовый режим - обычные запросы текстом и голосом. 

Команды:

/dialog для дружеских бесед на любые темы, текстом и голосом
/teacher для улучшения устной и письменной речи
/images для режима генерации изображений
/cancel для возврата в базовый режим
/settings для изменения модели (по умолчанию - gpt-4o-mini)
/help для вызова подсказки по командам
"""
    await message.answer(text)


@router.message(Command("settings"))
async def settings_handler(message: Message, visitor: Visitor) -> None:
    options = list(GPTModel) + ["Отмена"]
    keyboard = get_inline_keyboard(options, "model")
    text = f"""Ваша текущая модель: {visitor.model}.\n 
Какую выберете вместо нее?
- gpt-4o-mini - быстрая и дешевая
- gpt-4o - средний вариант
- gpt-o1 - думающая, долгая и умная
- gpt-o1-mini - ее облегченная версия"""
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.regexp(r"^model_([^ ]*)$").as_("match"))
async def choose_model_handler(call: CallbackQuery, match: Match[str]) -> None:
    await call.answer()
    if match.group(1) == "Отмена":
        await call.message.answer("Вы отменили действие")  # type: ignore
    else:
        model = GPTModel(match.group(1))
        await change_visitor_model(call.message.chat.id, model)
        await call.message.answer(f"Вы изменили модель на {model}")  # type: ignore
    await call.message.delete()


@router.message(Command("dialog"))
async def start_dialog_handler(message: Message, state: FSMContext) -> None:
    text = "Включен режим диалога! Болтайте с ботом голосовыми или текстом - он будет отвечать тем же способом"
    await message.answer(text)
    await state.set_state(Modes.conversation)


@router.message(Modes.conversation, F.content_type.in_({'voice'}))
async def continue_dialog_audio_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    in_memory_file = await tghelper.get_voice_from_tg(message)
    transcript = audio_to_text(in_memory_file)
    await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
    result = get_answer_from_friend(transcript, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        audio = text_to_audio(result.content)
        tg_file = process_file_for_tg(audio, "mp3")
        await message.reply_document(tg_file)


@router.message(Modes.conversation, F.content_type.in_({'text'}))
async def continue_dialog_text_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    result = get_answer_from_friend(message.text, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(result.content, parse_mode=ParseMode.MARKDOWN)


@router.message(Command("teacher"))
async def start_monolog_handler(message: Message, state: FSMContext) -> None:
    text = """Включен режим обучения! 
Присылайте текст или аудио - и учитель будет предлагать, как сделать речь правильней и естественней"""
    await message.answer(text)
    await state.set_state(Modes.monolog)


@router.message(Modes.monolog, F.content_type.in_({'voice'}))
async def feedback_audio_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    in_memory_file = await tghelper.get_voice_from_tg(message)
    transcript = audio_to_text(in_memory_file)
    await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
    result = get_english_teacher_comment(transcript, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(f"Коммент учителя английского: \n\n{result.content}", parse_mode=ParseMode.MARKDOWN)


@router.message(Modes.monolog, F.content_type.in_({'text'}))
async def feedback_text_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    result = get_english_teacher_comment(message.text, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(f"Коммент учителя английского: \n\n{result.content}", parse_mode=ParseMode.MARKDOWN)


@router.message(Command("images"))
async def start_images_handler(message: Message, state: FSMContext) -> None:
    await message.answer("Включен режим генерации изображений!")
    await state.set_state(Modes.images)


@router.message(Modes.images, F.content_type.in_({'text'}))
async def gen_image_handler(message: Message) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    await message.answer(get_random_processing_phrase())
    image = generate_image(message.text)
    if not image:
        await message.answer("Не удалось сгенерировать изображение, попробуйте снова", parse_mode=ParseMode.MARKDOWN)
    else:
        image_bytes = base64.b64decode(image)
        tg_file = process_file_for_tg(image_bytes, "png")  # type: ignore
        await message.reply_photo(tg_file)
