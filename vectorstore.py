from chromadb.config import Settings
from chromadb.server.fastapi import FastAPI

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