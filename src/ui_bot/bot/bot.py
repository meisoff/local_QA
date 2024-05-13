import asyncio
import logging
import sys
import traceback
from os import getenv

from aiogram import Bot, types, F, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, FSInputFile

from src.db.save_content import save_file
from src.model.rpc.execute import execute
from src.ui_bot.bot.rpc.send import send_rabbit
from src.ui_bot.utils.strings import Strings

TOKEN = getenv("BOT_TOKEN")
PATH_TO_DATA = getenv('PATH_TO_DATA')


class DocumentStates(StatesGroup):
    file_name = State()


dp = Dispatcher()

messages = []


def setup_handlers(bot):
    @dp.message(CommandStart())
    async def start(message: types.Message, bot: Bot, state: FSMContext):
        # await set_commands(bot)
        logo = FSInputFile('bot/static/start_pic.jpg')
        await message.answer_photo(photo=logo,
                                   caption=Strings.HELLO_MSG)
        # Open main menu and set empty state
        # await menu(message, state)
        custom_keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="/file")]],
            resize_keyboard=True
        )
        await message.answer(
            "Send pdf to get answer.",
            reply_markup=custom_keyboard)
        await upload_file(message, state)
        await state.set_state(None)

    @dp.message(F.document)
    async def upload_file(message: Message, state: FSMContext):

        if message.document:
            file_extension = message.document.file_name.split(".")[-1]

            if file_extension in ["docx", "xlsx", "pdf"]:
                try:
                    await message.answer(Strings.WAIT_MSG)
                    file_id = message.document.file_id
                    file_name = file_id + "." + file_extension
                    data = await state.get_data()

                    if 'file_name' in data:
                        await state.update_data(file_name=file_name)

                    else:
                        await state.set_state(DocumentStates.file_name)
                        await state.update_data(file_name=file_name)

                    file = await bot.get_file(file_id)
                    file_on_disk = f"{PATH_TO_DATA}/{file_name}"


                    try:
                        # Сохраняем во временное хранилище
                        await bot.download_file(file.file_path, destination=file_on_disk)

                        # Сохраняем данные в бд и удаляем из временного хранилища
                        await save_file(file_name, message.from_user.id)
                        await message.answer(f"✅ {message.document.file_name} успешно загружен")

                    except:
                        await message.answer(f"❌ Ошибка при загрузке файла")


                except Exception as e:
                    print(e)
                    traceback.print_exc()
            else:
                await message.answer('⚙️ Можно загрузить только файлы расширения "docx", "xlsx", "pdf"')
        else:
            await message.answer("Пожалуйста, загрузите файл")


    @dp.message(F.text)
    async def command_print_handler(message: Message, state: FSMContext) -> None:
        data = await state.get_data()

        if 'file_name' in data:
            await message.answer(Strings.WAIT_MSG)
            answer = await execute(message.text, message.from_user.id)
            print(answer)
            await message.answer(answer)

        else:
            await message.answer("Пожалуйста, загрузите файл и повторите вопрос")


    @dp.message(Command("print"))
    async def command_print_handler(message: Message) -> None:
        last_message = messages[-1]
        await message.answer(f"Last message was printed: {last_message}")
        await send_rabbit(f"print {last_message}")

    @dp.message(Command("send"))
    async def command_send_handler(message: Message) -> None:
        last_message = messages[-1]
        await message.answer(f"Last message was send: {last_message}")
        await send_rabbit(f"send {last_message}")


    @dp.message()
    async def message_loger(message: types.Message) -> None:
        messages.append(message.text)






async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    setup_handlers(bot)
    print("Хэндлеры подгружены")
    await dp.start_polling(bot)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
