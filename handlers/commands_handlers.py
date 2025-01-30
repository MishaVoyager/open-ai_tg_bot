import datetime
from re import Match

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from config.settings import CommonSettings
from domain.models import Visitor
from helpers import tghelper
from helpers.open_ai_helper import Model, transcript_by_whisper, convert_text_to_audio_bytes, continue_dialog
from helpers.tghelper import get_inline_keyboard
from service.visitor_actions import change_visitor_model

router = Router()


class Dialog(StatesGroup):
    conversation = State()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    text = """Бот для запросов в OpenAI к вашим услугам! 
По умолчанию выбрана модель gpt-4o-mini. 
Ее можно изменить: /settings
"""
    await message.answer(text)


@router.message(Command("settings"))
async def settings_handler(message: Message, visitor: Visitor) -> None:
    options = list(Model) + ["Отмена"]
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
        await call.message.answer("Вы отменили действие")
    else:
        model = Model(match.group(1))
        await change_visitor_model(call.message.chat.id, model)
        await call.message.answer(f"Вы изменили модель на {model}")
    await call.message.delete()


@router.message(Command("dialog"))
async def start_dialog_handler(message: Message, state: FSMContext) -> None:
    await message.answer("Включен режим диалога! Записывайте аудио - и бот тоже будет отвечать голосом")
    await state.set_state(Dialog.conversation)


@router.message(Dialog.conversation, F.content_type.in_({'voice'}))
async def continue_dialog_audio_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    in_memory_file = await tghelper.get_voice_from_tg(message)
    transcript = transcript_by_whisper(in_memory_file)
    await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
    result = continue_dialog(transcript, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(f"Собеседник: \n\n{result.content}", parse_mode=ParseMode.MARKDOWN)
        audio = convert_text_to_audio_bytes(result.content)
        file_name = f"english{datetime.datetime.now().strftime(r'%H_%M_%S')}.mp3"
        input_file = BufferedInputFile(audio, file_name)
        await message.reply_document(input_file)


@router.message(Dialog.conversation, F.content_type.in_({'text'}))
async def continue_dialog_text_handler(message: Message, visitor: Visitor) -> None:
    await message.answer("Пришлите аудио! Если хотите завершить диалог, выберите /cancel")
