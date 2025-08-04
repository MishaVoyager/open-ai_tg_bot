from re import Match

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from domain.models import Visitor
from helpers.open_ai_helper import GPTModel, clean
from helpers.tghelper import get_inline_keyboard
from service.visitor_actions import change_visitor_model

router = Router()


class Modes(StatesGroup):
    conversation = State()
    monolog = State()


@router.message(Command("start", "help"))
async def start_handler(message: Message) -> None:
    text = """Бот для запросов в OpenAI к вашим услугам! 
Базовый режим - обычные запросы текстом и голосом. 

Команды:

/chat для дружеских бесед на любые темы, текстом и голосом
/teacher для улучшения устной и письменной речи
/cancel для возврата в базовый режим
/settings для изменения модели (по умолчанию - gpt-4o-mini)
/help для вызова подсказки по командам
/clean для очистки истории
"""
    await message.answer(text)


@router.message(Command("settings"))
async def settings_handler(message: Message, visitor: Visitor) -> None:
    options = list(GPTModel) + ["Отмена"]
    keyboard = get_inline_keyboard(options, "model")
    text = f"""Ваша текущая модель: {visitor.model}.\n 
Какую выберете вместо нее?
- gpt-4o-mini - дешевая, быстрая, с веб-поиском
- gpt-4.1-mini - дешевая и быстрая NEW
- gpt-4.1-nano - самая быстрая
- o3-mini - думающая дешевая
- o4-mini - думающая дешевая NEW
"""
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
    await call.message.delete()  # type: ignore


@router.message(Command("friend"))
async def start_friend_chat_handler(message: Message, state: FSMContext) -> None:
    clean(str(message.from_user.id))
    text = "Включен режим диалога! Болтайте с ботом голосовыми или текстом - он будет отвечать тем же способом"
    await message.answer(text)
    await state.set_state(Modes.conversation)


@router.message(Command("teacher"))
async def start_monolog_handler(message: Message, state: FSMContext) -> None:
    clean(str(message.from_user.id))
    text = """Включен режим обучения! 
Присылайте текст или аудио - и учитель будет предлагать, как сделать речь правильней и естественней"""
    await message.answer(text)
    await state.set_state(Modes.monolog)


@router.message(Command("clean"))
async def clean_history_handler(message: Message) -> None:
    clean(str(message.from_user.id))
    await message.answer("История сообщений очищена")
