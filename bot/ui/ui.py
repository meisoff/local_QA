import os
import shutil
import json
import sys
import time
from dataclasses import dataclass
from typing import ClassVar
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from ..pipeline import LocalRAGPipeline
from ..logger import Logger

import asyncio
import os
import json
import secrets
import traceback
from datetime import datetime, timezone

import tiktoken
import fire
from aiogram import Bot, Dispatcher
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from openai import AsyncOpenAI
from tinydb import TinyDB, where, Query
from tinydb import operations as ops
from transformers import AutoTokenizer


@dataclass
class DefaultElement:
    DEFAULT_MESSAGE: ClassVar[dict] = {"text": ""}
    DEFAULT_MODEL: str = ""
    DEFAULT_HISTORY: ClassVar[list] = []
    DEFAULT_DOCUMENT: ClassVar[list] = []

    HELLO_MESSAGE: str = "Hi 👋, how can I help you today?"
    SET_MODEL_MESSAGE: str = "You need to choose LLM model 🤖 first!"
    EMPTY_MESSAGE: str = "You need to enter your message!"
    DEFAULT_STATUS: str = "Ready!"
    CONFIRM_PULL_MODEL_STATUS: str = "Confirm Pull Model!"
    PULL_MODEL_SCUCCESS_STATUS: str = "Pulling model 🤖 completed!"
    PULL_MODEL_FAIL_STATUS: str = "Pulling model 🤖 failed!"
    MODEL_NOT_EXIST_STATUS: str = "Model doesn't exist!"
    PROCESS_DOCUMENT_SUCCESS_STATUS: str = "Processing documents 📄 completed!"
    PROCESS_DOCUMENT_EMPTY_STATUS: str = "Empty documents!"
    ANSWERING_STATUS: str = "Answering!"
    COMPLETED_STATUS: str = "Completed!"


class LLMResponse:
    def __init__(self) -> None:
        pass

    def _yield_string(self, message: str):
        for i in range(len(message)):
            time.sleep(0.01)
            yield (
                DefaultElement.DEFAULT_MESSAGE,
                [[None, message[:i+1]]],
                DefaultElement.DEFAULT_STATUS
            )

    def welcome(self):
        yield from self._yield_string(DefaultElement.HELLO_MESSAGE)

    def set_model(self):
        yield from self._yield_string(DefaultElement.SET_MODEL_MESSAGE)

    def empty_message(self):
        yield from self._yield_string(DefaultElement.EMPTY_MESSAGE)

    def stream_response(
        self,
        message: str,
        history: list[list[str]],
        response: StreamingAgentChatResponse
    ):
        answer = []
        for text in response.response_gen:
            answer.append(text)
            yield (
                DefaultElement.DEFAULT_MESSAGE,
                history + [[message, "".join(answer)]],
                DefaultElement.ANSWERING_STATUS
            )
        yield (
            DefaultElement.DEFAULT_MESSAGE,
            history + [[message, "".join(answer)]],
            DefaultElement.COMPLETED_STATUS
        )


class LocalChatbotUI:
    def __init__(
        self,
        pipeline: LocalRAGPipeline,
        logger: Logger,
        host: str = "host.docker.internal",
        data_dir: str = "data/data",
        bot_token: str = None
    ):
        self._pipeline = pipeline
        self._logger = logger
        self._host = host
        self._data_dir = os.path.join(os.getcwd(), data_dir)
        # self._avatar_images = [os.path.join(os.getcwd(), image) for image in avatar_images]
        self._variant = "panel"
        self._llm_response = LLMResponse()

        # # База
        # self.db = TinyDB(db_path, ensure_ascii=False)
        # self.messages_table = self.db.table("messages")
        # self.conversations_table = self.db.table("current_conversations")
        # self.system_prompts_table = self.db.table("system_prompts")
        # self.models_table = self.db.table("models")
        # self.likes_table = self.db.table("likes")

        # Клавиатуры
        # self.inline_models_list_kb = InlineKeyboardBuilder()
        # for model_id in self.clients.keys():
        #     self.inline_models_list_kb.add(InlineKeyboardButton(text=model_id, callback_data=f"setmodel:{model_id}"))

        # Бот
        self.bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        self.dp = Dispatcher()
        self.dp.message.register(self._welcome, Command("start"))
        # self.dp.message.register(self._reset_chat, Command("reset"))
        # self.dp.message.register(self._change_system_prompt, Command("setsystem"))
        # self.dp.message.register(self.get_system, Command("getsystem"))
        # self.dp.message.register(self.reset_system, Command("resetsystem"))
        # self.dp.message.register(self.set_model, Command("setmodel"))
        # self.dp.message.register(self.get_model, Command("getmodel"))
        self.dp.message.register(self._get_respone)
        # self.dp.callback_query.register(self.save_feedback, F.data.startswith("feedback:"))
        # self.dp.callback_query.register(self.set_model_button_handler, F.data.startswith("setmodel:"))


    def _get_respone(
        self,
        chat_mode: str,
        message: dict[str, str],
        chatbot: list[list[str, str]],
    ):
        if self._pipeline.get_model_name() in [None, ""]:
            for m in self._llm_response.set_model():
                yield m
        elif message['text'] in [None, ""]:
            for m in self._llm_response.empty_message():
                yield m
        else:
            console = sys.stdout
            sys.stdout = self._logger
            response = self._pipeline.query(chat_mode, message['text'], chatbot)
            for m in self._llm_response.stream_response(message['text'], chatbot, response):
                yield m
            sys.stdout = console

    def _get_confirm_pull_model(self, model: str):
        if self._pipeline.check_exist(model):
            self._change_model(model)
            return (
                # gr.update(visible=False),
                # gr.update(visible=False),
                DefaultElement.DEFAULT_STATUS
            )
        return (
            # gr.update(visible=True),
            # gr.update(visible=True),
            DefaultElement.CONFIRM_PULL_MODEL_STATUS
        )

    # def _pull_model(self, model: str, progress=gr.Progress(track_tqdm=True)):
    #     if not self._pipeline.check_exist(model):
    #         response = self._pipeline.pull_model(model)
    #         if response.status_code == 200:
    #             # gr.Info(f"Pulling {model}!")
    #             for data in response.iter_lines(chunk_size=1):
    #                 data = json.loads(data)
    #                 if 'completed' in data.keys() and 'total' in data.keys():
    #                     progress(data['completed'] / data['total'], desc="Downloading")
    #                 else:
    #                     progress(0.)
    #         else:
    #             # gr.Warning(f"Model {model} doesn't exist!")
    #             return (
    #                 DefaultElement.DEFAULT_MESSAGE,
    #                 DefaultElement.DEFAULT_HISTORY,
    #                 DefaultElement.PULL_MODEL_FAIL_STATUS,
    #                 DefaultElement.DEFAULT_MODEL
    #             )
    #
    #     return (
    #         DefaultElement.DEFAULT_MESSAGE,
    #         DefaultElement.DEFAULT_HISTORY,
    #         DefaultElement.PULL_MODEL_SCUCCESS_STATUS,
    #         model
    #     )

    def _change_model(self, model: str):
        if model not in [None, ""]:
            self._pipeline.set_model_name(model)
            self._pipeline.set_model()
            self._pipeline.set_engine()
            # gr.Info(f"Change model to {model}!")
        return DefaultElement.DEFAULT_STATUS

    def _upload_document(self, document: list[str], list_files: list[str] | dict):
        if document in [None, []]:
            if isinstance(list_files, list):
                return (
                    list_files,
                    DefaultElement.DEFAULT_DOCUMENT
                )
            else:
                if list_files.get("files", None):
                    return list_files.get("files")
                return document
        else:
            if isinstance(list_files, list):
                return (
                    document + list_files,
                    DefaultElement.DEFAULT_DOCUMENT
                )
            else:
                if list_files.get("files", None):
                    return document + list_files.get("files")
                return document

    def _reset_document(self):
        self._pipeline.reset_documents()
        # gr.Info("Reset all documents!")
        return (
            DefaultElement.DEFAULT_DOCUMENT,
            # gr.update(visible=False),
            # gr.update(visible=False)
        )

    def _show_document_btn(self, document: list[str]):
        visible = False if document in [None, []] else True
        return (
            # gr.update(visible=visible),
            # gr.update(visible=visible)
        )

    def _processing_document(
        self,
        document: list[str]
    ):
        document = document or []
        if self._host == "host.docker.internal":
            input_files = []
            for file_path in document:
                dest = os.path.join(self._data_dir, file_path.split("/")[-1])
                shutil.move(src=file_path, dst=dest)
                input_files.append(dest)
            self._pipeline.store_nodes(input_files=input_files)
        else:
            self._pipeline.store_nodes(input_files=document)
        self._pipeline.set_chat_mode()
        # gr.Info("Processing Completed!")
        return (
            self._pipeline.get_system_prompt(),
            DefaultElement.COMPLETED_STATUS
        )

    def _change_system_prompt(self, sys_prompt: str):
        self._pipeline.set_system_prompt(sys_prompt)
        self._pipeline.set_chat_mode()
        # gr.Info("System prompt updated!")

    def _change_language(self, language: str):
        self._pipeline.set_language(language)
        self._pipeline.set_chat_mode()
        # gr.Info(f"Change language to {language}")

    def _undo_chat(self, history: list[list[str, str]]):
        if len(history) > 0:
            history.pop(-1)
            return history
        return DefaultElement.DEFAULT_HISTORY

    def _reset_chat(self):
        self._pipeline.reset_conversation()
        # gr.Info("Reset chat!")
        return (
            DefaultElement.DEFAULT_MESSAGE,
            DefaultElement.DEFAULT_HISTORY,
            DefaultElement.DEFAULT_DOCUMENT,
            DefaultElement.DEFAULT_STATUS
        )

    def _clear_chat(self):
        self._pipeline.clear_conversation()
        # gr.Info("Clear chat!")
        return (
            DefaultElement.DEFAULT_MESSAGE,
            DefaultElement.DEFAULT_HISTORY,
            DefaultElement.DEFAULT_STATUS
        )

    def _welcome(self):
        for m in self._llm_response.welcome():
            yield m