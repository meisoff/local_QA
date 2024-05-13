from aiogram import Dispatcher

from src.ui_bot.app import Config


def register_middlewares(dp: Dispatcher, config: Config):
    from . import throttling

    throttling.register_middleware(dp=dp, config=config)
