from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, CallbackQuery

from config.settings import CommonSettings


class DryMode(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        if CommonSettings().DRY_MODE:
            if isinstance(event, Message):
                await event.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
                return
            elif isinstance(event, CallbackQuery):
                await event.message.answer("Бот запущен в тестовом режиме. Запросы к OpenAI временно не выполняются")
                return
            else:
                return
        return await handler(event, data)
