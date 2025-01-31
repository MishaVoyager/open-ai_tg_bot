from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message

from config.settings import CommonSettings
from domain.models import Visitor
from helpers import tghelper
from helpers.open_ai_helper import generate_text, audio_to_text
from helpers.tghelper import get_random_processing_phrase

router = Router()


@router.message(F.content_type.in_({'text'}))
async def search_text_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    await message.answer(get_random_processing_phrase())
    result = generate_text(message.text, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(result.content, parse_mode=ParseMode.MARKDOWN)


@router.message(F.content_type.in_({'voice'}))
async def search_audio_handler(message: Message, visitor: Visitor) -> None:
    if CommonSettings().DRY_MODE:
        await message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
        return
    in_memory_file = await tghelper.get_voice_from_tg(message)
    transcript = audio_to_text(in_memory_file)
    await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
    await message.answer(get_random_processing_phrase())
    result = generate_text(transcript, visitor.model)
    if result.refusal:
        await message.answer(result.refusal, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(result.content, parse_mode=ParseMode.MARKDOWN)
