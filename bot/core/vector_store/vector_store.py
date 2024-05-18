from llama_index.core import VectorStoreIndex
from langchain_community.vectorstores import Chroma

from dotenv import load_dotenv
from ...settings import RAGSettings


load_dotenv()


class LocalVectorStore:
    def __init__(
        self,
        host: str = "host.docker.internal",
        setting: RAGSettings | None = None,
    ) -> None:
        # TODO
        # CHROMA VECTOR STORE
        self._setting = setting or RAGSettings()
        self.vector_store = Chroma(collection_name="files", persist_directory=self._setting.storage.persist_dir_chroma)


    def save_index(self, nodes, user_id):
        if len(nodes) == 0:
            return None

        coll = self.vector_store.get()

        ids_to_del = []
        for idx in range(len(coll['ids'])):

            id = coll['ids'][idx]
            metadata = coll['metadatas'][idx]

            if metadata['user_id'] == f"{user_id}":
                ids_to_del.append(id)

        if len(ids_to_del) != 0:
            self.vector_store.delete(ids_to_del)

        documents = get_document(data, tg_id)

        if len(documents) == 0:
            raise ValueError

        texts = [d.page_content for d in documents]
        metadatas = [d.metadata for d in documents]
        vector_store.add_texts(texts, metadatas)
        index = VectorStoreIndex(nodes=nodes)
        return index

    def get_index(self, user_id):
        node_store = self.vector_store.get()