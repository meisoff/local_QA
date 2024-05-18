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

from config import DEFAULT_SYSTEM_PROMPT_RAG

os.environ["TOKENIZERS_PARALLELISM"] = "false"

DEFAULT_SYSTEM_PROMPT = DEFAULT_SYSTEM_PROMPT_RAG
DEFAULT_MODEL = "kto"


class Tokenizer:
    tokenizers = dict()

    @classmethod
    def get(cls, model_name: str = "IlyaGusev/saiga_llama3_8b"):
        if model_name not in cls.tokenizers:
            cls.tokenizers[model_name] = AutoTokenizer.from_pretrained(model_name)
        return cls.tokenizers[model_name]


class LlmBot:
    def __init__(
        self,
        bot_token: str,
        client_config_path: str,
        db_path: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        history_max_tokens: int,
        chunk_size: int = 3500
    ):

        # Клиент
        with open(client_config_path) as r:
            client_config = json.load(r)
        self.clients = dict()
        self.model_names = dict()
        for model_name, config in client_config.items():
            self.model_names[model_name] = config.pop("model_name")
            self.clients[model_name] = AsyncOpenAI(**config)
        assert self.clients
        assert self.model_names

        # Параметры
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.history_max_tokens = history_max_tokens

        # База
        self.db = TinyDB(db_path, ensure_ascii=False)
        self.messages_table = self.db.table("messages")
        self.conversations_table = self.db.table("current_conversations")
        self.system_prompts_table = self.db.table("system_prompts")
        self.models_table = self.db.table("models")
        self.likes_table = self.db.table("likes")

        # Клавиатуры
        self.inline_models_list_kb = InlineKeyboardBuilder()
        for model_id in self.clients.keys():
            self.inline_models_list_kb.add(InlineKeyboardButton(text=model_id, callback_data=f"setmodel:{model_id}"))

        # Бот
        self.chunk_size = chunk_size
        self.bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
        self.dp = Dispatcher()
        self.dp.message.register(self.start, Command("start"))
        self.dp.message.register(self.reset, Command("reset"))
        self.dp.message.register(self.history, Command("history"))
        self.dp.message.register(self.set_system, Command("setsystem"))
        self.dp.message.register(self.get_system, Command("getsystem"))
        self.dp.message.register(self.reset_system, Command("resetsystem"))
        self.dp.message.register(self.generate)
        self.dp.callback_query.register(self.save_feedback, F.data.startswith("feedback:"))
        self.dp.callback_query.register(self.set_model_button_handler, F.data.startswith("setmodel:"))


    async def start_polling(self):
        await self.dp.start_polling(self.bot)

    def get_current_model(self, user_id):
        query = Query()
        if self.models_table.contains(query.user_id == user_id):
            return self.models_table.get(query.user_id == user_id)["model"]
        return DEFAULT_MODEL

    def set_current_model(self, user_id: int, model_name: str):
        assert model_name in self.clients
        query = Query()
        if self.models_table.contains(query.user_id == user_id):
            self.models_table.update(ops.set("model", model_name), query.user_id == user_id)
        else:
            self.models_table.insert({"model": model_name, "user_id": user_id})

    def count_tokens(self, messages, model):
        tokenizer = Tokenizer.get()
        tokens = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
        return len(tokens)

    def fetch_conversation(self, conv_id):
        messages = self.messages_table.search(where("conv_id") == conv_id)
        if not messages:
            return []
        messages.sort(key=lambda x: x["timestamp"])
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    @staticmethod
    def merge_messages(messages):
        new_messages = []
        prev_role = None
        for m in messages:
            if m["content"] is None:
                continue
            if m["role"] == prev_role:
                new_messages[-1]["content"] += "\n" + m["content"]
                continue
            prev_role = m["role"]
            new_messages.append(m)
        return new_messages

    @staticmethod
    def get_current_ts():
        return int(datetime.now().replace(tzinfo=timezone.utc).timestamp())

    def create_conv_id(self, user_id):
        conv_id = secrets.token_hex(nbytes=16)
        self.conversations_table.insert({
            "user_id": user_id,
            "conv_id": conv_id,
            "timestamp": self.get_current_ts()
        })
        return conv_id

    def get_current_conv_id(self, user_id):
        conv_ids = self.conversations_table.search(where("user_id") == user_id)
        if not conv_ids:
            return self.create_conv_id(user_id)
        conv_ids.sort(key=lambda x: x["timestamp"], reverse=True)
        return conv_ids[0]["conv_id"]

    async def query_api(self, model, history, last_message: str, system_prompt: str):
        messages = history + [{"role": "user", "content": last_message}]
        messages = self.merge_messages(messages)

        tokens_count = self.count_tokens(messages, model=model)
        while tokens_count > self.history_max_tokens and len(messages) >= 3:
            messages = messages[2:]
            tokens_count = self.count_tokens(messages, model=model)

        if messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})

        print(model, "####", len(messages), "####", messages[-1]["content"].replace("\n", " ")[:40])
        chat_completion = await self.clients[model].chat.completions.create(
            model=self.model_names[model],
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens
        )
        answer = chat_completion.choices[0].message.content
        print(model, "####", len(messages), "####", messages[-1]["content"].replace("\n", " ")[:40], "####", answer.replace("\n", " ")[:40])
        return answer

    def get_system_prompt(self, user_id):
        query = Query()
        if self.system_prompts_table.contains(query.user_id == user_id):
            return self.system_prompts_table.get(query.user_id == user_id)["prompt"]
        return DEFAULT_SYSTEM_PROMPT

    def set_system_prompt(self, user_id: int, text: str):
        query = Query()
        if self.system_prompts_table.contains(query.user_id == user_id):
            self.system_prompts_table.update(ops.set("prompt", text), query.user_id == user_id)
        else:
            self.system_prompts_table.insert({"prompt": text, "user_id": user_id})

    async def start(self, message: Message):
        user_id = message.from_user.id
        self.create_conv_id(user_id)
        await message.reply("Привет! Как тебе помочь?")

    async def set_system(self, message: Message):
        user_id = message.from_user.id
        text = message.text.replace("/setsystem", "").strip()
        self.set_system_prompt(user_id, text)
        self.create_conv_id(user_id)
        await message.reply(f"Новый системный промпт задан:\n\n{text}")

    async def get_system(self, message: Message):
        user_id = message.from_user.id
        prompt = self.get_system_prompt(user_id)
        if prompt.strip():
            await message.reply(prompt)
        else:
            await message.reply("Системный промпт пуст")

    async def set_model_button_handler(self, callback: CallbackQuery):
        user_id = callback.from_user.id
        model_name = callback.data.split(":")[1]
        if model_name in self.clients:
            self.set_current_model(user_id, model_name)
            self.create_conv_id(user_id)
            await self.bot.send_message(chat_id=user_id, text=f"Новая модель задана:\n\n{model_name}")
        else:
            await self.bot.send_message(chat_id=user_id, text=f"Некорректное имя модели. Выберите из: {list(self.clients.keys())}")

    async def reset_system(self, message: Message):
        user_id = message.from_user.id
        self.set_system_prompt(user_id, DEFAULT_SYSTEM_PROMPT)
        self.create_conv_id(user_id)
        await message.reply("Системный промпт сброшен!")

    async def reset(self, message: Message):
        user_id = message.from_user.id
        self.create_conv_id(user_id)
        await message.reply("История сообщений сброшена!")

    async def history(self, message: Message):
        user_id = message.from_user.id
        conv_id = self.get_current_conv_id(user_id)
        history = self.fetch_conversation(conv_id)
        history = json.dumps(history, ensure_ascii=False)
        history = history[:3000] + "... truncated"
        await message.reply(history, parse_mode=None)

    async def generate(self, message: Message):
        user_id = message.from_user.id
        last_message = message.text
        conv_id = self.get_current_conv_id(user_id)
        history = self.fetch_conversation(conv_id)
        system_prompt = self.get_system_prompt(user_id)
        self.messages_table.insert({
            "role": "user",
            "content": last_message,
            "conv_id": conv_id,
            "timestamp": self.get_current_ts()
        })
        model = self.get_current_model(user_id)
        placeholder = await message.reply("Вопрос принят. Ищу ответ 📃🔍")

        try:
            answer = await self.query_api(
                model=model,
                history=history,
                last_message=last_message,
                system_prompt=system_prompt
            )

            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(
                text="👍",
                callback_data="feedback:like"
            ))
            builder.add(InlineKeyboardButton(
                text="👎",
                callback_data="feedback:dislike"
            ))
            markup = builder.as_markup()

            chunk_size = self.chunk_size
            answer_parts = [answer[i:i + chunk_size] for i in range(0, len(answer), chunk_size)]

            new_message = await placeholder.edit_text(answer_parts[0], parse_mode=None)
            for part in answer_parts[1:]:
                new_message = await message.answer(part, parse_mode=None)
            new_message = await new_message.edit_text(answer_parts[-1], parse_mode=None, reply_markup=markup)

            self.messages_table.insert({
                "role": "assistant",
                "content": answer,
                "conv_id": conv_id,
                "timestamp": self.get_current_ts(),
                "message_id": new_message.message_id,
                "model": model,
                "system_prompt": system_prompt
            })
        except Exception:
            traceback.print_exc()
            await placeholder.edit_text("Что-то пошло не так, ответ от ChatQA не получен или не смог отобразиться.")

    async def save_feedback(self, callback: CallbackQuery):
        user_id = callback.from_user.id
        message_id = callback.message.message_id
        feedback = callback.data.split(":")[1]
        self.likes_table.insert({
            "user_id": user_id,
            "message_id": message_id,
            "feedback": feedback,
            "is_correct": True
        })
        await self.bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=message_id,
            reply_markup=None
        )

def main(
    bot_token: str,
    client_config_path: str,
    db_path: str,
    temperature: float = 0.6,
    top_p: float = 0.9,
    max_tokens: int = 1536,
    history_max_tokens: int = 6144
) -> None:
    bot = LlmBot(
        bot_token=bot_token,
        client_config_path=client_config_path,
        db_path=db_path,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        history_max_tokens=history_max_tokens
    )
    asyncio.run(bot.start_polling())


if __name__ == "__main__":
    # fire.Fire(main)
    main(
        bot_token="6036877254:AAGi69UGwcX8X0hz0RwS8oyQZ52fTx3yY2w",
        client_config_path="/home/kalyrginas/tg_rag_QA/bot/client_config.json",
        db_path="/home/kalyrginas/tg_rag_QA/bot/db/tiny_db.json",

    )