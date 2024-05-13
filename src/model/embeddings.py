import os
from os import getenv
from txtai import Embeddings
from txtai.pipeline import Textractor
import ollama
import bs4
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import nltk

nltk.download('punkt')
PATH_TO_DATA = getenv('PATH_TO_DATA')

def stream(path, file_name, textractor):
    fpath = os.path.join(path, file_name)
    # Only accept documents
    if file_name.endswith(("docx", "xlsx", "pdf")):
        print(f"Indexing {fpath}")
        for paragraph in textractor(fpath):
            yield paragraph
    else:
        raise 'Расширение файла не: "docx", "xlsx", "pdf"'


def embeddings_files(file_name):
    # Document text extraction, split into paragraphs
    textractor = Textractor(paragraphs=True)

    # Vector Database
    embeddings = Embeddings(path='nvidia/dragon-multiturn-query-encoder', content=True, autoid="uuid5")
    embeddings.index(stream(PATH_TO_DATA, file_name, textractor))

    return embeddings


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
