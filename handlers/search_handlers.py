import random

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message

from config.settings import CommonSettings
from domain.models import Visitor
from helpers import tghelper
from helpers.open_ai_helper import generate, transcript_by_whisper, get_english_teacher_comment

router = Router()

THINKING_PHRASES = [
    "Запрос обрабатывается...",
    "Секундочку...",
    "Я не зависла, просто стараюсь получше ответить...",
    "Мысли медленно крутятся в моей голове...",
    "Я размышляю о вашем запросе, подождите немножко, пожалуйста...",
    "Ожиданье - самый скучный повод...",
    "Это будет леген... подожди-подожди..."
]


@router.message(F.content_type.in_({'text'}))
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


@router.message(F.content_type.in_({'voice'}))
async def answer_audio_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    in_memory_file = await tghelper.get_voice_from_tg(message)
    transcript = transcript_by_whisper(in_memory_file)
    await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
    result = get_english_teacher_comment(transcript, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(f"Коммент учителя английского: \n\n{result.content}", parse_mode=ParseMode.MARKDOWN)
