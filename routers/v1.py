
import dotenv
from fastapi import APIRouter
from fastapi.responses import JSONResponse
# Assistant classs
from utils import return_response
from . import v2 as V2

DEFAULT_API_KEY = dotenv.get_key(".env", "OPENAI_API_KEY")

router = APIRouter()


@router.get("/regime/info")
async def get_info_from_regimes(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,   n_result: int = 15):
    return await V2.answer_to_question(
        question=question,
        douanes_ai=V2.DouanesModelsEnum.REGIMES_TOGO_2021,
        api_key=api_key,
        stream=stream,
        prompt_only=prompt_only,
        n_result=n_result
    )

@router.get("/valeur/info")
async def get_info_from_fiche_valeurs(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,  n_result: int = 10):
    return await V2.answer_to_question(
        question=question,
        douanes_ai=V2.DouanesModelsEnum.FICHE_VALEUR_TOGO_2022,
        api_key=api_key,
        stream=stream,
        prompt_only=prompt_only,
        n_result=n_result
    )

@router.get("/valeur/cst")
async def get_cst_code_infos(question: str, api_key: str = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False,   n_result: int = 10):
    return await V2.answer_to_question(
        question=question,
        douanes_ai=V2.DouanesModelsEnum.CST_TOGO_2023,
        api_key=api_key,
        stream=stream,
        prompt_only=prompt_only,
        n_result=n_result
    )

@router.get("/tec/info")
async def get_tec_info(query: str | None = None, question: str |None = None , api_key: str | None = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False, use_gpt4 : bool= False):
    return await V2.answer_to_question(
        question=query if question is None else question,
        douanes_ai=V2.DouanesModelsEnum.TEC_CEDEAO_2022,
        api_key=api_key,
        stream=stream,
        prompt_only=prompt_only,
        use_gpt4=use_gpt4,
    )

@router.get("/cdn/answer")
async def answer_to_question(question: str, api_key: str | None = DEFAULT_API_KEY, stream: bool = False, prompt_only: bool = False, use_gpt4: bool = False):
    douanes_ai=V2.DouanesModelsEnum.CDN_TOGO_CEDEAO_2017
    tec_parts = question.split('@TEC:')
    valeur_parts = question.split('@VALEUR')
    regime_parts = question.split("@REGIME")
    cst_parts = question.split("@CST")
    if len(tec_parts) == 2:
       return await get_tec_info(tec_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only, use_gpt4=use_gpt4 )
    elif len(valeur_parts) == 2:
       return get_info_from_fiche_valeurs(valeur_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only)
    elif len(regime_parts) == 2:
       return await get_info_from_regimes(regime_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only)
    elif len(cst_parts) == 2:
       return await get_cst_code_infos(cst_parts[1], api_key=api_key, stream=stream, prompt_only=prompt_only)
    
    return await V2.answer_to_question(
        question=question,
        douanes_ai=douanes_ai,
        api_key=api_key,
        stream=stream,
        prompt_only=prompt_only,
        use_gpt4=use_gpt4,
    )
