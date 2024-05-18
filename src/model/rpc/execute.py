from src.model.prompt import SYSTEM_MESSAGE_PROMT, CONTEXT_PROMPT_EN, NEW_CONTEXT_QUESTION

import ollama

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings


def ollama_llm(question, context):
    message_template = {"role": "user",
                        "content": CONTEXT_PROMPT_EN.format(question=question,
                                                            context_str=context)}

    messages = [{"role": "system", "content": SYSTEM_MESSAGE_PROMT}, message_template]

    response = ollama.chat(model='llama3', messages=messages)
    r = ollama.AsyncClient
    messages.append(response['message'])
    print(messages)
    print(response)
    return response['message']['content']


def get_retriever(user_id):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = Chroma(collection_name="files", embedding_function=embeddings,
                          persist_directory="/home/kalyrginas/tg_rag_QA/src/db/chromadb")
    return vector_store.as_retriever(search_kwargs={"k": 5, "filter": {"tg_id": str(user_id)}})


def combine_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def rag_chain(question, retriever):
    retrieved_docs = retriever.invoke(question)
    formatted_context = combine_docs(retrieved_docs)
    return ollama_llm(question, formatted_context)


async def execute(question, user_id):
    if question is None:
        return ("Вопрос не передан")

    try:
        retriever = get_retriever(user_id)
        result = rag_chain(question, retriever)
        print(result)

        return result

    except Exception as e:
        raise e
