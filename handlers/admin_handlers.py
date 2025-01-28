from re import Match

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from domain.models import Status
from middlware.is_admin_middleware import Authorize
from service.visitor_actions import get_visitor, change_visitor_status, get_all_visitors

router = Router()
router.message.middleware(Authorize())
router.callback_query.middleware(Authorize())


@router.message(Command("users"))
async def get_users_handler(message: Message) -> None:
    visitors = await get_all_visitors()
    await message.answer("Список пользователей:\n\n" + "\n\n".join([str(i) for i in visitors]))


@router.message(F.text.regexp(r"^(\/allow)(\d+)$").as_("match"))
async def allow_handler(message: Message, match: Match[str]) -> None:
    chat_id = int(match.group(2))
    visitor = await get_visitor(chat_id)
    if visitor is None:
        await message.answer(f"Не найден пользователь с chat_id {chat_id}")
    elif visitor.status == Status.PROCESSING.value:
        await change_visitor_status(chat_id, Status.VERIFIED)
        await message.bot.send_message(chat_id=chat_id, text="Вам дали доступ к боту!")
        await message.answer(f"Вы успешно предоставили доступ {visitor.short_str()}")
    elif visitor.status == Status.VERIFIED:
        await message.answer(f"Вы уже одобрили заявку {visitor.short_str()}")
    elif visitor.status == Status.DECLINED:
        await message.answer(f"Вы уже отклонили заявку {visitor.short_str()}")


@router.message(F.text.regexp(r"^(\/decline)(\d+)$").as_("match"))
async def decline_handler(message: Message, match: Match[str]) -> None:
    chat_id = int(match.group(2))
    visitor = await get_visitor(chat_id)
    if visitor is None:
        await message.answer(f"Не найден пользователь с chat_id {chat_id}")
    elif visitor.status == Status.PROCESSING.value:
        await change_visitor_status(chat_id, Status.DECLINED)
        await message.bot.send_message(chat_id=chat_id, text="Вам запретили доступ к боту!")
        await message.answer(f"Вы успешно запретили доступ {visitor.short_str()}")
    elif visitor.status == Status.VERIFIED:
        await message.answer(f"Вы уже одобрили заявку {visitor.short_str()}")
    elif visitor.status == Status.DECLINED:
        await message.answer(f"Вы уже отклонили заявку {visitor.short_str()}")
