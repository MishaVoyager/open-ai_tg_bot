from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, CallbackQuery, InaccessibleMessage

from config.settings import CommonSettings
from domain.models import Visitor, Status
from service.visitor_actions import get_visitor, get_all_admins, add_visitor


class Auth(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        if not (isinstance(event, Message) or isinstance(event, CallbackQuery)):
            return
        message = event if isinstance(event, Message) else event.message
        if isinstance(message, InaccessibleMessage) or message is None:
            return
        visitor = await get_visitor(message.chat.id)
        if visitor:
            if visitor.status == Status.PROCESSING.value:
                await message.answer("Подождите, пока админ одобрит ваш запрос")
                return
            elif visitor.status == Status.DECLINED.value:
                await message.answer("Вам запрещено пользоваться ботом")
                return
            else:
                data["visitor"] = visitor
                return await handler(event, data)
        username = message.from_user.username
        is_admin = username in CommonSettings().ADMINS
        verified = username in CommonSettings().USERNAMES
        visitor = Visitor(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=username,
            is_admin=is_admin,
            status=Status.VERIFIED.value if verified else Status.PROCESSING.value
        )
        await add_visitor(visitor)
        if verified and not is_admin:
            await message.answer("Вы получили доступ к боту! Пусть он принесет вам много пользы")
            data["visitor"] = visitor
            return await handler(event, data)
        if verified and is_admin:
            await message.answer("Вы авторизовались как админ бота!")
            data["visitor"] = visitor
            return await handler(event, data)
        admins = await get_all_admins()
        for admin in admins:
            await message.bot.send_message(
                chat_id=admin.chat_id,
                text=f"Пользователь {visitor.full_name} @{username} просит доступ\n/allow{visitor.chat_id}\n/decline{visitor.chat_id}"
            )
        await message.answer("Пока что нет доступа к боту. Админам отправлен запрос")
