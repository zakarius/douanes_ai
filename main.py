import json
import dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn
# Assistant classs
from cdn import CodesDesDouanes
from tarif.tec2022 import Tec2022
from valeur.valeur import Valeur, RegimeEconomique



DEFAULT_API_KEY = dotenv.get_key(".env", "OPENAI_API_KEY")


class DouanesApi(FastAPI):
    _api_key: str | None = None
    cdn = CodesDesDouanes()
    tec = Tec2022()
    valeur = Valeur()
    regimes = RegimeEconomique()

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
        self.valeur.api_key = value
        self.regimes.api_key = value


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


@app.get("/regime/info")
def get_info_from_regimes(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,   n_result: int = 15):
    app.api_key = api_key   
    response = app.regimes.get_info(
        question, stream=stream, prompt_only=prompt_only, n_result=n_result)
    return return_response(response, stream, prompt_only)

@app.get("/valeur/info")
def get_info_from_fiche_valeurs(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,   n_result: int = 10):
    app.api_key = api_key   
    response = app.valeur.answer(question, stream=stream, prompt_only=prompt_only, n_result=n_result)
    return return_response(response, stream, prompt_only)

@app.get("/valeur/cst")
def get_cst_code_infos(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,   n_result: int = 10):
    app.api_key = api_key   
    response = app.valeur.ge_cst(question, stream=stream, prompt_only=prompt_only, n_result=n_result)
    return return_response(response, stream, prompt_only)

@app.get("/tec/info")
def get_tec_info(query: str, api_key: str | None = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False, use_gpt4 : bool= False):
    tec = app.tec
    if api_key and api_key != '':
        app.api_key = api_key
    response = tec.get_info(
        query, stream=stream, prompt_only=prompt_only or (api_key is None), use_gpt4=use_gpt4)
    return return_response(response, stream, prompt_only)


@app.get("/cdn/answer")
async def answer_to_question(question: str, api_key: str | None = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False, use_gpt4: bool = False):
    tec_parts = question.split('@TEC:')
    valeur_parts = question.split('@VALEUR')
    regime_parts = question.split("@REGIME")
    cst_parts = question.split("@CST")
    if len(tec_parts) == 2:
       return  get_tec_info(tec_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only, use_gpt4=use_gpt4 )
    elif len(valeur_parts) == 2:
       return get_info_from_fiche_valeurs(valeur_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only)
    elif len(regime_parts) == 2:
       return get_info_from_regimes(regime_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only)
    elif len(cst_parts) == 2:
       return get_cst_code_infos(cst_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only)
    

    app.api_key = api_key
    response = app.cdn.answer(question, stream=stream, prompt_only=prompt_only)
    return return_response(response, stream, prompt_only)


@app.get("/cdn/search", response_class=JSONResponse)
def get_similar_content(question: str, api_key: str | None = DEFAULT_API_KEY, collection: str = "articles",  n_result: int = 5):
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
