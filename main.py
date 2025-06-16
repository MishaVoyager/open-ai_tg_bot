import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config.settings import CommonSettings
from handlers import user_handlers, admin_handlers, cancel_handlers, commands_handlers
from middlware.auth_middleware import Auth
from service.visitor_actions import start_db_async


async def start_bot(token: str) -> None:
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.outer_middleware(Auth())
    dp.callback_query.outer_middleware(Auth())
    dp.include_routers(
        cancel_handlers.router,
        admin_handlers.router,
        commands_handlers.router,
        # должен идти последним, т.к. ловит любой текст:
        user_handlers.router
    )
    await bot.set_my_commands(
        [
            BotCommand(command="/friend", description="Чат с американцем"),
            BotCommand(command="/teacher", description="Монолог с учителем"),
            BotCommand(command="/cancel", description="Выйти из текущего режима"),
            BotCommand(command="/settings", description="Изменить настройки запросов"),
            BotCommand(command="/clean", description="Очистить контекст диалога")
        ]
    )
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main() -> None:
    await start_db_async()
    await start_bot(CommonSettings().BOT_TOKEN)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    asyncio.run(main())
