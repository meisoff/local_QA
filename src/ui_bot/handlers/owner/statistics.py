from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.ui_bot.app import IsOwner
from src.ui_bot.app import User

router = Router()


@router.message(IsOwner(is_owner=True), Command(commands=["stats"]))
async def stats_handler(message: Message):
    count = await User.get_count()
    await message.answer(
        f"📊 <b>Количество пользователей бота -</b> <code>{count}</code>"
    )
