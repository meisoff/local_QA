from aiogram.utils.markdown import hbold


class Strings:
    """
    A class for storing strings of constants.
    """

    HELLO_MSG = 'Приветствую. Я ' + hbold('ChatQA 👋') + f'\n\nМогу ответить на вопросы по вашему документу.'
    HELP_MSG = (
        "Просто отправь мне голосовое или текстовое сообщение - и я тут же отвечу!"
    )
    WAIT_MSG = "Запрос принят. Подождите, пожалуйста..."
    WAIT_MSG_FILE = "Видим ваш файл. Загружаем, подождите..."