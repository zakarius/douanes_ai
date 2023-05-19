
import dotenv
from fastapi import APIRouter
from fastapi.responses import JSONResponse
# Assistant classs
from cdn import CodesDesDouanes
from tarif.tec2022 import Tec2022
from utils import return_response
from valeur.valeur import Valeur, RegimeEconomique


DEFAULT_API_KEY = dotenv.get_key(".env", "OPENAI_API_KEY")


cdn = CodesDesDouanes()
tec = Tec2022()
valeur = Valeur()
regimes = RegimeEconomique()



router = APIRouter()


@router.get("/regime/info")
def get_info_from_regimes(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,   n_result: int = 15):
    
    response = regimes.get_info(
        question, stream=stream, prompt_only=prompt_only, n_result=n_result)
    return return_response(response, stream, prompt_only)

@router.get("/valeur/info")
def get_info_from_fiche_valeurs(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,   n_result: int = 10):
    response = valeur.answer(question, stream=stream, prompt_only=prompt_only, n_result=n_result)
    return return_response(response, stream, prompt_only)

@router.get("/valeur/cst")
def get_cst_code_infos(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,   n_result: int = 10):
    valeur.api_key = api_key   
    response = valeur.ge_cst(question, stream=stream, prompt_only=prompt_only, n_result=n_result)
    return return_response(response, stream, prompt_only)

@router.get("/tec/info")
def get_tec_info(query: str, api_key: str | None = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False, use_gpt4 : bool= False):
    valeur.api_key = api_key
    response = tec.get_info(
        query, stream=stream, prompt_only=prompt_only or (api_key is None), use_gpt4=use_gpt4)
    return return_response(response, stream, prompt_only)


@router.get("/cdn/answer")
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
    

    cdn.api_key = api_key
    response = cdn.answer(question, stream=stream, prompt_only=prompt_only)
    return return_response(response, stream, prompt_only)


@router.get("/cdn/search", response_class=JSONResponse)
def get_similar_content(question: str, api_key: str | None = DEFAULT_API_KEY, collection: str = "articles",  n_result: int = 5):
    cdn.api_key = api_key
    results = cdn.search(
        question=question,
        collection=collection,
        n_result=n_result,
    )
    return JSONResponse(
        content=[item.replace("##LINE##", "\n")
                 for item in results["documents"][0]],
    )