from chromadb.config import Settings
from chromadb.server.fastapi import FastAPI
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory= ".chromadb_cache",
    chroma_api_impl="local",
    chroma_server_host="localhost",
    chroma_server_http_port="8000",
    chroma_server_cors_allow_origins=["*"]
)
server = FastAPI(settings)
chromadb = server._api


class BaseDouaneData():
    _api_key: str | None = None

    data_frames_path: str 
    embeddings_path: str 
    embedding_functions: OpenAIEmbeddingFunction
    

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, api_key: str):
        self._api_key = api_key
        self.embedding_functions = OpenAIEmbeddingFunction(api_key)
    
