"""
Роутер для отмены. Позволяет выйти из любого сценария текстом cancel / отмена / отменить.
Удобно определить в одном месте, чтобы не делать это в каждом роутере.
Также это подстраховка для сценария, в котором пользователь заблокируется.
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from helpers.open_ai_helper import clean

router = Router()


@router.message(Command("cancel"))
@router.message(F.text.casefold().contains("отменить"))
@router.message(F.text.casefold().contains("отмена"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    clean(str(message.from_user.id))
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("Вы вернулись в основной режим - поиска", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Уже включен основной режим - поиска", reply_markup=ReplyKeyboardRemove())
