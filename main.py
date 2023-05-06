from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn
# Assistant classs
from cdn import CodesDesDouanes


class DouanesApi(FastAPI):
    _api_key: str | None = None
    cdn = CodesDesDouanes()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value):
        self._api_key = value
        self.cdn.api_key = value


app = DouanesApi()  # server.app()


@app.get("/cdn/answer")
async def answer_to_question(question: str, api_key: str, stream: bool = False, prompt_only: bool = False, openai_message: bool = False):
    app.api_key = api_key
    response = app.cdn.answer(question, stream=stream, prompt_only=prompt_only)
    if stream and not prompt_only:
        def get_message(chunk) -> str:
            return chunk['choices'][0]['delta'].get(
                "content", "")

        return EventSourceResponse(response if openai_message else map(get_message, response))
    else:
        return PlainTextResponse(response, media_type="text/plain")


@app.get("/cdn/search", response_class=JSONResponse)
def get_similar_content(question: str, api_key: str, collection: str = "articles",  n_result: int = 5):
    app.api_key = api_key
    results = app.cdn.search(
        question=question,
        collection=collection,
        n_result=n_result,
    )
    return JSONResponse(
        content=[item.replace("##LINE##", "\n")
                 for item in results["documents"][0]],
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
