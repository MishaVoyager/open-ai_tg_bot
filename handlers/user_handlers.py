from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.types import Message

from domain.models import Visitor
from handlers.commands_handlers import Modes
from helpers import tghelper
from helpers.open_ai_helper import generate_text, audio_to_text, get_answer_from_friend, text_to_audio, \
    get_english_teacher_comment
from helpers.tghelper import get_random_processing_phrase, process_file_for_tg, send_text_any_size
from middlware.dry_mode_middlware import DryMode

router = Router()
router.message.middleware(DryMode())
router.callback_query.middleware(DryMode())


@router.message(StateFilter(None), F.content_type.in_({'text'}))
async def search_text_handler(message: Message, visitor: Visitor) -> None:
    tmp_message = await message.answer(get_random_processing_phrase())
    result = generate_text(message.text, visitor.model)
    await tmp_message.delete()
    text = result.refusal if result.refusal else result.content
    print(text)
    await send_text_any_size(message, text)


@router.message(StateFilter(None), F.content_type.in_({'voice'}))
async def search_audio_handler(message: Message, visitor: Visitor) -> None:
    in_memory_file = await tghelper.get_voice_from_tg(message)
    transcript = audio_to_text(in_memory_file)
    await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
    tmp_message = await message.answer(get_random_processing_phrase())
    result = generate_text(transcript, visitor.model)
    await tmp_message.delete()
    text = result.refusal if result.refusal else result.content
    await send_text_any_size(message, text)


@router.message(Modes.conversation, F.content_type.in_({'voice'}))
async def continue_dialog_audio_handler(message: Message, visitor: Visitor) -> None:
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
    result = get_answer_from_friend(message.text, visitor.model)
    text = result.refusal if result.refusal else result.content
    await send_text_any_size(message, text)


@router.message(Modes.monolog, F.content_type.in_({'voice'}))
async def feedback_audio_handler(message: Message, visitor: Visitor) -> None:
    in_memory_file = await tghelper.get_voice_from_tg(message)
    transcript = audio_to_text(in_memory_file)
    await message.answer(f"Транскрипт вашего аудио: \n\n{transcript}")
    result = get_english_teacher_comment(transcript, visitor.model)
    text = result.refusal if result.refusal else f"Коммент учителя английского: \n\n{result.content}"
    await send_text_any_size(message, text)


@router.message(Modes.monolog, F.content_type.in_({'text'}))
async def feedback_text_handler(message: Message, visitor: Visitor) -> None:
    result = get_english_teacher_comment(message.text, visitor.model)
    text = result.refusal if result.refusal else f"Коммент учителя английского: \n\n{result.content}"
    await send_text_any_size(message, text)
