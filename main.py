from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn
# Assistant classs
from cdn import CodesDesDouanes
from tarif.tec2022 import Tec2022


class DouanesApi(FastAPI):
    _api_key: str | None = None
    cdn = CodesDesDouanes()
    tec = Tec2022()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value):
        self._api_key = value
        self.cdn.api_key = value
        self.tec.api_key = value


app = DouanesApi()  # server.app()

def get_message(chunk) -> str:
    message: str = chunk['choices'][0]['delta'].get(
        "content", "")
    return message.replace(" ", "\u00a0").replace("\n", "\u0085")

def return_response(response, stream: bool, prompt_only: bool):
    if stream and not prompt_only:
        return EventSourceResponse(map(get_message, response))
    else:
        return PlainTextResponse(response, media_type="text/plain")

@app.get("/tec/info")
def get_tec_info(query: str, api_key: str | None = None, stream: bool = False, prompt_only: bool = False, use_gpt4 : bool= False):
    tec = app.tec
    if api_key and api_key != '':
        app.api_key = api_key
    response = tec.get_info(
        query, stream=stream, prompt_only=prompt_only or (api_key is None), use_gpt4=use_gpt4)
    return return_response(response, stream, prompt_only)


@app.get("/cdn/answer")
async def answer_to_question(question: str, api_key: str, stream: bool = False, prompt_only: bool = False, use_gpt4: bool = False):
    tec_parts = question.split('@TEC:')
    if len(tec_parts) == 2:
       return  get_tec_info(tec_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only, use_gpt4=use_gpt4 )    


    app.api_key = api_key
    response = app.cdn.answer(question, stream=stream, prompt_only=prompt_only)
    return return_response(response, stream, prompt_only)


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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
