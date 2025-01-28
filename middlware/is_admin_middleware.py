from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, CallbackQuery


class Authorize(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        visitor = data["visitor"]
        if not visitor.is_admin:
            if isinstance(event, Message):
                await event.answer("Не удалось выполнить запрос, попробуйте снова")
                return
            elif isinstance(event, CallbackQuery):
                await event.message.answer("Не удалось выполнить запрос, попробуйте снова")
                return
            else:
                return
        return await handler(event, data)
