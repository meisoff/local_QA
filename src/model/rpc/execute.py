import json
import os
import shutil
from os import getenv

import nltk
from txtai import Embeddings
from txtai.pipeline import Extractor
from txtai.pipeline import LLM
from txtai.pipeline import Textractor
from src.db import schema as db
from src.db.save_content import save_files_from_base64

import ollama
import bs4
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.model.prompt import SYSTEM_MESSAGE_PROMT, CONTEXT_PROMPT_EN, NEW_CONTEXT_QUESTION


# nltk.download('punkt')
# PATH_TO_DATA = getenv('PATH_TO_DATA')


# llm = LLM("/home/kalyrginas/tg_rag_QA/src/model/ChatQA-1.5-8B-Q8_0.gguf", template="""<|im_start|>system
#     You are a friendly assistant. You answer questions from users.<|im_end|>
#     <|im_start|>user
#     {text} <|im_end|>
#     <|im_start|>assistant
#     """, method="llama.cpp")

def get_chat_history_str(chat_history):
    chat_history_str = ""
    for item in chat_history:
        role = item["role"]
        content = item["content"]
        chat_history_str += f'{role}: {content}\n'
    return chat_history_str


def ollama_llm(question, context, chat_history):
    # formatted_prompt = f"Question: {question}\n\nContext: {context}"

    message_template = {"role": "user",
                        "content": CONTEXT_PROMPT_EN.format(
                            chat_history=get_chat_history_str(chat_history) if chat_history else None,
                            question=question,
                            context_str=context)}

    messages = [{"role": "system", "content": SYSTEM_MESSAGE_PROMT}, message_template]

    response = ollama.chat(model='llama3', messages=messages)
    messages.append(response['message'])
    print(messages)
    print(response)
    return {
        "chat_history": messages,
        "response": response['message']['content']
    }


def get_retriever(user_id):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = Chroma(collection_name="files", embedding_function=embeddings,
                          persist_directory="/home/kalyrginas/tg_rag_QA/src/db/chromadb")
    return vector_store.as_retriever(search_kwargs={"k": 5, "filter": {"tg_id": str(user_id)}})


def combine_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def rag_chain(question, retriever, chat_history):
    if chat_history:
        chat_history_str = get_chat_history_str(chat_history)
        response = ollama.chat(model='llama3', messages=[{"role": "system", "content": NEW_CONTEXT_QUESTION.format(
            chat_history=chat_history_str, question=question)}])
        question = response['message']['content']

    retrieved_docs = retriever.invoke(question)
    formatted_context = combine_docs(retrieved_docs)
    return ollama_llm(question, formatted_context, chat_history)


def prompt(question):
    return [{
        "query": question,
        "question": f"""
            Answer the following question using only the context below. Only include information specifically discussed.

            question: {question}
            context:
        """
    }]


async def execute(question, user_id, chat_history):
    if question is None:
        return ("Вопрос не передан")

    try:
        account_info = db.Account.select().where(db.Account.tg_id == user_id)
        # if account_info:
        #     embeddings_serialized = account_info[0].embeddings_serialized
        #     hash_file = account_info[0].hash_file
        #     print("Получили embeddings_serialized из БД")
        # else:
        #     print("Ошибка при получении embeddings_serialized из БД")
        #     error_message = "Вероятно мы забыли ваш файл… 🤔 \nОтправьте его снова ⚙️"
        #     return error_message

        retriever = get_retriever(user_id)

        # 5. Use the RAG App
        result = rag_chain(question, retriever, chat_history)
        print(result)

        return result

        # try:
        #     # Восстанавливаем сериализуемые данные из БД
        #     save_files_from_base64(f"{PATH_TO_DATA}/{hash_file}", embeddings_serialized)
        #
        #     embeddings = Embeddings()
        #     embeddings.load(f"{PATH_TO_DATA}/{hash_file}")
        #
        # except Exception as e:
        #     raise e
        #
        # finally:
        #     shutil.rmtree(f"{PATH_TO_DATA}/{hash_file}")
        #     print(f"Папка {PATH_TO_DATA}/{hash_file} успешно удалена вместе со всем содержимым.")

        # # Create extractor instance
        # extractor = Extractor(embeddings, llm, output="reference")
        #
        # result = extractor(prompt(question),
        #                    maxlength=4096, pad_token_id=32000)[0] # НЕ может принимать pad_token_id=32000 почему то
        # answer = result["answer"]
        # citation = embeddings.search("select id, text from txtai where id = :id", limit=1,
        #                              parameters={"id": result["reference"]})
        #
        # text = f"""
        #         Ответ: {answer} \nЦитата из файла: {citation}
        #     """
        #
        # return text

    except Exception as e:
        raise e
