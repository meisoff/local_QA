import ollama
import bs4
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def get_document(data, tg_id):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = []
    for chunk in text_splitter.split_documents(data):
        metadata = {
            "tg_id": str(tg_id),
        }
        docs.append(Document(page_content=chunk.page_content, metadata=metadata))
    return docs


def embed_and_write(data, tg_id):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = Chroma(collection_name="files", embedding_function=embeddings, persist_directory="/home/kalyrginas/tg_rag_QA/src/db/chromadb")

    coll = vector_store.get()
    ids_to_del = []

    for idx in range(len(coll['ids'])):

        id = coll['ids'][idx]
        metadata = coll['metadatas'][idx]

        if metadata['tg_id'] == f"{tg_id}":
            ids_to_del.append(id)

    if len(ids_to_del) != 0:
        vector_store.delete(ids_to_del)

    documents = get_document(data, tg_id)

    if len(documents) == 0:
        raise ValueError

    texts = [d.page_content for d in documents]
    metadatas = [d.metadata for d in documents]
    vector_store.add_texts(texts, metadatas)

def get_retriever(user_id):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = Chroma(collection_name="files", embedding_function=embeddings,
                          persist_directory="/home/kalyrginas/tg_rag_QA/src/db/chromadb")
    return vector_store.as_retriever(search_kwargs={"filter": {"tg_id": str(user_id)}})



def start():
    # 1. Load the data
    loader = PyPDFLoader("/home/kalyrginas/tg_rag_QA/docs.pdf")
    docs = loader.load()

    embed_and_write(docs, 392919)

    # 4. RAG Setup
    retriever = get_retriever(392919)

    # 5. Use the RAG App
    result = rag_chain("Сумма оплат в договоре? Напиши по русски", retriever)
    print(result)


# # 1. Load the data
# loader = PyPDFLoader("/home/kalyrginas/tg_rag_QA/docs.pdf")
# docs = loader.load()
#
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
# # Добавить метаданные, по которым можно будет найти и удалить их из стора
# splits = text_splitter.split_documents(docs)
#
# # 2. Create Ollama embeddings and vector store
# embeddings = OllamaEmbeddings(model="nomic-embed-text")
# vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory="/home/kalyrginas/tg_rag_QA")

# 3. Call Ollama Llama3 model
def ollama_llm(question, context):
    # formatted_prompt = f"Question: {question}\n\nContext: {context}"
    formatted_prompt = f"""
            Answer the following question using only the context below. Only include information specifically discussed.

            question: {question}
            context: {context}
        """
    response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': formatted_prompt}])
    return response['message']['content']

# # 4. RAG Setup
# retriever = vectorstore.as_retriever()
def combine_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
def rag_chain(question, retriever):
    retrieved_docs = retriever.invoke(question)
    formatted_context = combine_docs(retrieved_docs)
    return ollama_llm(question, formatted_context)

# # 5. Use the RAG App
# result = rag_chain("Где живет заказчик?")
# print(result)


if __name__ == "__main__":
    print(str([{'sss':1212}]))