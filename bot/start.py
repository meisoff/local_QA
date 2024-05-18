import argparse
import llama_index
from .ui import LocalChatbotUI
from .pipeline import LocalRAGPipeline
from .logger import Logger
from .ollama import run_ollama_server, is_port_open



if __name__ == "__main__":

    # CONSTANTS
    LOG_FILE = "logging.log"
    DATA_DIR = "data/data"
    # AVATAR_IMAGES = ["./assets/user.png", "./assets/bot.png"]

    # PARSER
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "--host", type=str, default="host.docker.internal",
    #     help="Set host to local or in docker container"
    # )
    # parser.add_argument(
    #     "--token", type=str, action='store_true',
    #     help="Telegram bot token"
    # )
    # args = parser.parse_args()

    # OLLAMA SERVER
    # if args.host != "host.docker.internal":
    port_number = 11434
    if not is_port_open(port_number):
        run_ollama_server()

    # LOGGER

    llama_index.core.set_global_handler("simple")
    logger = Logger(LOG_FILE)
    logger.reset_logs()

    # PIPELINE
    pipeline = LocalRAGPipeline(host="0.0.0.0")

    # UI
    ui = LocalChatbotUI(
        pipeline=pipeline,
        logger=logger,
        host="0.0.0.0",
        data_dir=DATA_DIR,
        bot_token="6036877254:AAGi69UGwcX8X0hz0RwS8oyQZ52fTx3yY2w"
    )
