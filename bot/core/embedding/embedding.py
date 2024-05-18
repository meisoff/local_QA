import requests
from langchain_community.embeddings import OllamaEmbeddings
from ...settings import RAGSettings
from dotenv import load_dotenv


load_dotenv()


class LocalEmbedding:
    @staticmethod
    def set(setting: RAGSettings | None = None, **kwargs):
        setting = setting or RAGSettings()
        model_name = setting.ingestion.embed_llm
        return OllamaEmbeddings(model_name=model_name)

    @staticmethod
    def pull(host: str, **kwargs):
        setting = RAGSettings()
        payload = {
            "name": setting.ingestion.embed_llm
        }
        return requests.post(f"http://{host}:11434/api/pull", json=payload, stream=True)

    @staticmethod
    def check_model_exist(host: str, **kwargs) -> bool:
        setting = RAGSettings()
        data = requests.get(f"http://{host}:11434/api/tags").json()
        list_model = [d["name"] for d in data["models"]]
        if setting.ingestion.embed_llm in list_model:
            return True
        return False