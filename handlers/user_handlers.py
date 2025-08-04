import logging

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.types import Message

from domain.models import Visitor
from handlers.commands_handlers import Modes
from helpers import tghelper
from helpers.open_ai_helper import generate_text, WEB_SEARCH_MODELS, audio_to_text, get_answer_from_friend, text_to_audio, \
    get_english_teacher_comment
from helpers.tghelper import get_random_processing_phrase, process_file_for_tg, send_text_any_size
from middlware.dry_mode_middlware import DryMode

router = Router()
router.message.middleware(DryMode())
router.callback_query.middleware(DryMode())


@router.message(StateFilter(None), F.content_type.in_({'text'}))
async def search_text_handler(message: Message, visitor: Visitor) -> None:
    tmp_message = await message.answer(get_random_processing_phrase())
    try:
        result = await generate_text(str(message.from_user.id), message.text, visitor.model, visitor.model in WEB_SEARCH_MODELS)
        await tmp_message.delete()
        await send_text_any_size(message, result)
    except Exception as e:
        await tmp_message.delete()
        await message.answer(f"Произошла ошибка: {str(e)[:100]}...")
        logging.error(f"Ошибка в search_text_handler: {e}")


@router.message(StateFilter(None), F.content_type.in_({'voice'}))
async def search_audio_handler(message: Message, visitor: Visitor) -> None:
    try:
        in_memory_file = await tghelper.get_voice_from_tg(message)
        transcript = await audio_to_text(in_memory_file)
        await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
        tmp_message = await message.answer(get_random_processing_phrase())
        result = await generate_text(str(message.from_user.id), transcript, visitor.model)
        await tmp_message.delete()
        await send_text_any_size(message, result)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)[:100]}...")
        logging.error(f"Ошибка в search_audio_handler: {e}")


@router.message(Modes.conversation, F.content_type.in_({'voice'}))
async def continue_friend_chat_audio_handler(message: Message, visitor: Visitor) -> None:
    try:
        in_memory_file = await tghelper.get_voice_from_tg(message)
        transcript = await audio_to_text(in_memory_file)
        await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
        result = await get_answer_from_friend(str(message.from_user.id), transcript, visitor.model)
        if result:
            audio = await text_to_audio(result)
            tg_file = process_file_for_tg(audio, "mp3")
            await message.reply_document(tg_file)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)[:100]}...")
        logging.error(f"Ошибка в continue_friend_chat_audio_handler: {e}")


@router.message(Modes.conversation, F.content_type.in_({'text'}))
async def continue_friend_chat_text_handler(message: Message, visitor: Visitor) -> None:
    try:
        result = await get_answer_from_friend(str(message.from_user.id), message.text, visitor.model)
        await send_text_any_size(message, result)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)[:100]}...")
        logging.error(f"Ошибка в continue_friend_chat_text_handler: {e}")


@router.message(Modes.monolog, F.content_type.in_({'voice'}))
async def feedback_audio_handler(message: Message, visitor: Visitor) -> None:
    try:
        in_memory_file = await tghelper.get_voice_from_tg(message)
        transcript = await audio_to_text(in_memory_file)
        await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
        result = await get_english_teacher_comment(str(message.from_user.id), transcript, visitor.model)
        text = f"Коммент учителя английского: \n\n{result}" if result else "Не удалось получить ответ"
        await send_text_any_size(message, text)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)[:100]}...")
        logging.error(f"Ошибка в feedback_audio_handler: {e}")


@router.message(Modes.monolog, F.content_type.in_({'text'}))
async def feedback_text_handler(message: Message, visitor: Visitor) -> None:
    try:
        result = await get_english_teacher_comment(str(message.from_user.id), message.text, visitor.model)
        text = f"Коммент учителя английского: \n\n{result}" if result else "Не удалось получить ответ"
        await send_text_any_size(message, text)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)[:100]}...")
        logging.error(f"Ошибка в feedback_text_handler: {e}")
