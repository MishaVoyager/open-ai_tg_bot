import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config.settings import CommonSettings
from handlers import search_handlers, admin_handlers
from middlware.auth_middleware import Auth
from service.visitor_actions import start_db_async


async def start_bot(token: str) -> None:
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.outer_middleware(Auth())
    dp.callback_query.outer_middleware(Auth())

    dp.include_routers(admin_handlers.router)
    dp.include_routers(search_handlers.router)
    await bot.set_my_commands(
        [
            BotCommand(command="/settings", description="Изменить настройки запросов"),
            BotCommand(command="/info", description="Узнать текущие настройки")
        ]
    )
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main() -> None:
    await start_db_async()
    await start_bot(CommonSettings().BOT_TOKEN)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    asyncio.run(main())
