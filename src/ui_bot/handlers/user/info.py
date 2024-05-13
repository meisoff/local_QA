from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from src.ui_bot.app import Config
from src.ui_bot.app import owner_commands, users_commands
from src.ui_bot.keyboards.inline import get_author_keyboard

router = Router()


@router.message(Command(commands=["help"]))
async def help_handler(message: Message, config: Config):
    text = "ℹ️ <b>Список команд:</b> \n\n"
    commands = (
        owner_commands.items()
        if message.from_user.id == config.settings.owner_id
        else users_commands.items()
    )
    for command, description in commands:
        text += f"/{command} - <b>{description}</b> \n"
    await message.answer(text)


@router.message(Command(commands=["about"]))
async def about_handler(message: Message, bot: Bot, config: Config):
    bot_information = await bot.get_me()
    await message.answer(
        "<b>ℹ️ Информация о боте:</b> \n\n"
        f"<b>Название - </b> {bot_information.full_name} \n"
        f"<b>Username - </b> @{bot_information.username} \n"
        f"<b>ID - </b> <code>{bot_information.id}</code> \n",
        reply_markup=get_author_keyboard(owner_id=config.settings.owner_id),
    )
