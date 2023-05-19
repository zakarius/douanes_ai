
from enum import Enum
import dotenv
from fastapi import  APIRouter

from douanes.monde import *
from  douanes.afrique import *
from  douanes.cedeao import CodeDesDouanesCEDEAO2017, TECCedeao2022
from  douanes.togo import CdnTogoEtCedeao2017, CodeDesDouanesTogo2017
from douanes.utils import BaseDouaneAI
from utils import return_response


router = APIRouter()


OPENAI_API_KEY = dotenv.get_key(".env", "OPENAI_API_KEY")
PALM_API_KEY = dotenv.get_key(".env", "PALM_API_KEY")


class DouanesModelsEnum(Enum):
    CDN_TOGO_2017 = "cdn-togo-2017"
    CDC_CEDEAO_2017 = "cdc-cedeao-2017"
    CDN_TOGO_CEDEAO_2017 = "cdn-togo-cedeao-2017"
    TEC_CEDEAO_2022 = "tec-cedeao-2022"

douanes_models : dict[str, BaseDouaneAI] = {
    "cdn-togo-2017": CodeDesDouanesTogo2017(),
    "cdc-cedeao-2017": CodeDesDouanesCEDEAO2017(),
    "cdn-togo-cedeao-2017": CdnTogoEtCedeao2017(),
    "tec-cedeao-2022": TECCedeao2022()
}


class AIProviders(Enum):
    OPEN_AI = "open_ai"
    GOOGLE = "google"
    GPT4ALL = "gpt4all"

ai_providers = {
    "open_ai": OPENAI_API_KEY,
    "google": PALM_API_KEY,
}


class ResponseMethod(Enum):
    GET_INFO = "info"
    ANSWER = "anwser"

class TecCollectionEnum(Enum):
    ALL = "all"
    SECTIONS = "sections"
    CHAPITRES = "chapitres"
    POSITIONS = "positions"




@router.get("/answer")
async def answer_to_question(
    question: str, 
    completor: AIProviders = AIProviders.OPEN_AI,
    douanes_ai: DouanesModelsEnum = DouanesModelsEnum.CDN_TOGO_CEDEAO_2017,
    tec_collection: TecCollectionEnum = TecCollectionEnum.ALL,
    api_key: str | None = None, 
    response_method: ResponseMethod = ResponseMethod.ANSWER,
    stream: bool = False, 
    prompt_only: bool = False,
    use_gpt4: bool = False,
    n_result: int = 5,
   ):
    api_key  = ai_providers[completor.value] if api_key is None else api_key
    assert api_key is not None and api_key.strip() != "", "La clé API est obligatoire"

    app = douanes_models[douanes_ai.value]
    app.api_key = api_key

    if prompt_only:
       return app.construct_prompt(question)

    if response_method == ResponseMethod.GET_INFO or douanes_ai == DouanesModelsEnum.TEC_CEDEAO_2022:
        if douanes_ai == DouanesModelsEnum.TEC_CEDEAO_2022:
            app.BASE_COLLECTION = tec_collection.value
        response = app.get_info(question, completor=completor.value, stream=stream, prompt_only=prompt_only,
                                use_gpt4=use_gpt4, n_result=n_result)
    else:
        response = app.answer(question, completor=completor.value, stream=stream, prompt_only=prompt_only, n_result=n_result)

    return return_response(response, stream, prompt_only)
