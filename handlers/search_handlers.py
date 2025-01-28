import random
from re import Match

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from config.settings import CommonSettings
from domain.models import Visitor
from helpers.open_ai_helper import Model, generate
from helpers.tghelper import get_inline_keyboard
from service.visitor_actions import change_visitor_model

router = Router()


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


THINKING_PHRASES = [
    "Запрос обрабатывается...",
    "Секундочку...",
    "Я не зависла, просто стараюсь получше ответить...",
    "Мысли медленно крутятся в моей голове...",
    "Я размышляю о вашем запросе, подождите немножко, пожалуйста...",
    "Ожиданье - самый скучный повод...",
    "Это будет леген... подожди-подожди..."
]


@router.message()
async def search_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    await message.answer(random.choice(THINKING_PHRASES))
    result = generate(message.text, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(result.content, parse_mode=ParseMode.MARKDOWN)
