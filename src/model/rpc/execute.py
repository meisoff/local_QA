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

nltk.download('punkt')
PATH_TO_DATA = getenv('PATH_TO_DATA')


llm = LLM("/home/kalyrginas/tg_rag_QA/src/model/ChatQA-1.5-8B-Q8_0.gguf", template="""<|im_start|>system
    You are a friendly assistant. You answer questions from users.<|im_end|>
    <|im_start|>user
    {text} <|im_end|>
    <|im_start|>assistant
    """, method="llama.cpp")

def ollama_llm(question, context):
    # formatted_prompt = f"Question: {question}\n\nContext: {context}"
    formatted_prompt = f"""
            Answer the following question using only the context below. Only include information specifically discussed.

            question: {question}
            context: {context}
        """
    response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': formatted_prompt}])
    return response['message']['content']

def get_retriever(user_id):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = Chroma(collection_name="files", embedding_function=embeddings,
                          persist_directory="/home/kalyrginas/tg_rag_QA/src/db/chromadb")
    return vector_store.as_retriever(search_kwargs={"filter": {"tg_id": str(user_id)}})

def combine_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def rag_chain(question, retriever):
    retrieved_docs = retriever.invoke(question)
    formatted_context = combine_docs(retrieved_docs)
    return ollama_llm(question, formatted_context)

def prompt(question):
    return [{
        "query": question,
        "question": f"""
            Answer the following question using only the context below. Only include information specifically discussed.

            question: {question}
            context:
        """
    }]

async def execute(question, user_id):
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
        result = rag_chain(question, retriever)
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




if __name__ == "__main__":
    execute("Which hyper-parameters, learning rate and steps were used to solve the Example 1?")






