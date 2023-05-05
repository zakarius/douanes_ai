from chromadb.config import Settings
from chromadb.server.fastapi import FastAPI
from  os import getenv

settings = Settings(
    chroma_db_impl=getenv("CHROMA_DB_IMPL", "duckdb+parquet"),
    clickhouse_host= getenv("CLICKHOUSE_HOST", "clickhouse"),
    clickhouse_port= getenv("CLICKHOUSE_PORT", "8123"),
    persist_directory= getenv("PERSIST_DIRECTORY", ".chromadb_cache"),
    chroma_api_impl="local",
    chroma_server_host="localhost",
    chroma_server_http_port="8000",
    chroma_server_cors_allow_origins=["*"]
)
server = FastAPI(settings)
chromadb = server._api