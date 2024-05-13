from aiogram.utils.markdown import hbold


class Strings:
    """
    A class for storing strings of constants.
    """

    HELLO_MSG = 'Welcome to ' + hbold('Find in Docs Bot 👋') + f'\n\nUsing this bot, you can search answer in docs with LLM system.'
    HELP_MSG = (
        "Просто отправь мне голосовое или текстовое сообщение - и я тут же отвечу!"
    )
    WAIT_MSG = "Подождите, пожалуйста...😇"