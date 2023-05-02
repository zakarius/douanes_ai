
from chromadb.config import Settings
from chromadb.server.fastapi import FastAPI

from fastapi import Response
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse

settings = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory=".chromadb_cache",
    chroma_api_impl="local",
    chroma_server_host="localhost",
    chroma_server_http_port="8000",
    chroma_server_cors_allow_origins=["*"]
)
server = FastAPI(settings)
chromadb = server._api
app = server.app()


# OPEN_API_KEY = "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"


@app.get("/cdn/answer")
def answer_to_question(response: Response, question: str, api_key: str, stream: bool = False):
    from cdn import CodesDesDouanes
    codes = CodesDesDouanes(api_key)
    if (stream == False):
        return codes.run(question)
    response.headers["Content-Type"] = "text/plain"
    return StreamingResponse(codes.stream(question), media_type="text/plain")


@app.get("/cdn/search", response_class=JSONResponse)
def get_similar_content(question: str, api_key: str, collection: str = "articles",  n_result: int = 5):
    from cdn import CodesDesDouanes
    codes = CodesDesDouanes(api_key)
    results = codes.search(
        question=question,
        collection=collection,
        n_result=n_result
    )
    return [item.replace("##LINE##", "\n") for item in results["documents"][0]]
