from itertools import chain
from enum import Enum
import dotenv
from fastapi import APIRouter
from pydantic import BaseModel
from douanes.monde import *
from douanes.afrique import *
from douanes.cedeao import CodeDesDouanesCEDEAO2017, TECCedeao2022
from douanes.pays.togo import CdnTogoEtCedeao2017, CodeDesDouanesTogo2017, FicheValeurTogo2022, CodesCSTTogo2023, RegimesTogo2021, RegimesTogo2023, FiscaliteDouanesTogo2019
from douanes.utils import BaseDouaneAI
from douanes.utils.code_des_douanes import CodeDesDouanes
from douanes.utils.fiscalite_douaniere import FiscaliteDouaniere
from douanes.utils.regimes_economiques import RegimeEconomique
from douanes.utils.tarif_exterieur_commun import TarifExterieurCommun
from douanes.utils.valeur_en_douanes import CodesCST, FicheValeurs
from utils import return_response


router = APIRouter()


OPENAI_API_KEY = dotenv.get_key(".env", "OPENAI_API_KEY")
PALM_API_KEY = dotenv.get_key(".env", "PALM_API_KEY")


class DouanesModelsEnum(Enum):
    # CEDEAO
    CDC_CEDEAO_2017 = "cdc-cedeao-2017"
    TEC_CEDEAO_2022 = "tec-cedeao-2022"
    # TOGO
    CDN_TOGO_2017 = "cdn-togo-2017"
    CDN_TOGO_CEDEAO_2017 = "cdn-togo-cedeao-2017"
    FICHE_VALEUR_TOGO_2022 = "valeur-togo-fiche-2022"
    CST_TOGO_2023 = "valeur-togo-cst-2023"
    REGIMES_TOGO_2021 = "regimes-togo-2021"
    REGIMES_TOGO_2023 = "regimes-togo-2023"
    FISCALITE_TOGO_2019 = "fiscalite-togo-2019"


class CodeDesDouanesEnum(Enum):
    CDC_CEDEAO_2017 = "cdc-cedeao-2017"
    CDN_TOGO_2017 = "cdn-togo-2017"
    CDN_TOGO_CEDEAO_2017 = "cdn-togo-cedeao-2017"


class TecEnum(Enum):
    TEC_CEDEAO_2022 = "tec-cedeao-2022"


class RegimesEconomiquesEnum(Enum):
    REGIMES_TOGO_2021 = "regimes-togo-2021"


class FicheValeurEnum(Enum):
    FICHE_VALEUR_TOGO_2022 = "valeur-togo-fiche-2022"


class FiscaliteEnum(Enum):
    FISCALITE_TOGO_2019 = "fiscalite-togo-2019"


douanes_models: dict[str, BaseDouaneAI] = {
    # cedeao
    "cdc-cedeao-2017": CodeDesDouanesCEDEAO2017(),
    "tec-cedeao-2022": TECCedeao2022(),
    # togo
    "cdn-togo-2017": CodeDesDouanesTogo2017(),
    "cdn-togo-cedeao-2017": CdnTogoEtCedeao2017(),
    "valeur-togo-fiche-2022":  FicheValeurTogo2022(),
    "valeur-togo-cst-2023": CodesCSTTogo2023(),
    "regimes-togo-2021": RegimesTogo2021(),
    "regimes-togo-2023": RegimesTogo2023(),
    "fiscalite-togo-2019": FiscaliteDouanesTogo2019(),
}


class AIProviders(Enum):
    OPEN_AI = "open_ai"
    GOOGLE = "google"
    GPT4ALL = "gpt4all"


ai_providers = {
    "open_ai": OPENAI_API_KEY,
    "google": PALM_API_KEY,
}


class TecCollectionEnum(Enum):
    ALL = "all"
    SECTIONS = "sections"
    CHAPITRES = "chapitres"
    POSITIONS = "positions"


class ResponseFunction(Enum):
    ANSWER = "answer"
    GET_INFO = "get_info"
    TAXES_APPLIQUABLES = "taxes_appliquables"


class DouanesRequest(BaseModel):
    question: str
    completor: AIProviders = AIProviders.OPEN_AI
    douanes_ai: DouanesModelsEnum = DouanesModelsEnum.CDN_TOGO_CEDEAO_2017
    tec_collection: TecCollectionEnum = TecCollectionEnum.ALL
    api_key: str | None = None
    stream: bool = False
    prompt_only: bool = False
    use_gpt4: bool = False
    n_result: int = 5
    response_function: ResponseFunction = ResponseFunction.ANSWER


async def _answer_to_question(req: DouanesRequest):
    completor = req.completor.value
    douanes_ai = req.douanes_ai.value
    tec_collection = req.tec_collection.value
    question = req.question
    stream = req.stream
    prompt_only = req.prompt_only
    use_gpt4 = req.use_gpt4
    n_result = req.n_result
    response_function = req.response_function
    api_key = req.api_key

    api_key = ai_providers[completor] if api_key is None else api_key
    assert api_key is not None and api_key.strip() != "", "La clé API est obligatoire"

    app = douanes_models[douanes_ai]
    app.api_key = api_key

    ai_type = douanes_ai.split("-")[0]

    if ai_type == "tec":
        app.BASE_COLLECTION = tec_collection
    elif ai_type == "fiscalite":
        if response_function == ResponseFunction.TAXES_APPLIQUABLES:
            app.taxes_appliquables()

    response = app.get_info(question, completor=completor, stream=stream, prompt_only=prompt_only,
                            use_gpt4=use_gpt4, n_result=n_result)

    return return_response(response, stream, prompt_only)


@router.get("/answer")
async def answer_to_question(
    question: str,
    completor: AIProviders = AIProviders.OPEN_AI,
    douanes_ai: DouanesModelsEnum = DouanesModelsEnum.CDN_TOGO_CEDEAO_2017,
    tec_collection: TecCollectionEnum = TecCollectionEnum.ALL,
    api_key: str | None = None,
    stream: bool = False,
    prompt_only: bool = False,
    use_gpt4: bool = False,
    n_result: int = 5,
    response_function: ResponseFunction = ResponseFunction.ANSWER,
):
    if question.startswith("@/"):
        return await analyse_question(
            question=question.removeprefix("@/"),
            api_key=api_key,
            stream=stream,
        )
    else:
        request = DouanesRequest(
            question=question,
            completor=completor,
            douanes_ai=douanes_ai,
            tec_collection=tec_collection,
            api_key=api_key,
            stream=stream,
            use_gpt4=use_gpt4,
            prompt_only=prompt_only,
            n_result=n_result,
            response_function=response_function,
        )
        return await _answer_to_question(request)


@router.get("/analyse")
async def analyse_question(
    question: str,
    completor: AIProviders = AIProviders.OPEN_AI,
    api_key: str | None = None,
    code_des_douanes: CodeDesDouanesEnum = CodeDesDouanesEnum.CDN_TOGO_CEDEAO_2017,
    tec: TecEnum = TecEnum.TEC_CEDEAO_2022,
    fiche_valeur: FicheValeurEnum = FicheValeurEnum.FICHE_VALEUR_TOGO_2022,
    regimes: RegimesEconomiquesEnum = RegimesEconomiquesEnum.REGIMES_TOGO_2021,
    fiscalite: FiscaliteEnum = FiscaliteEnum.FISCALITE_TOGO_2019,
    stream: bool = False,
):
    api_key = ai_providers[completor.value] if api_key is None else api_key

    codes_app: CodeDesDouanes = douanes_models[code_des_douanes.value]
    codes_app.api_key = api_key

    tec_app: TarifExterieurCommun = douanes_models[tec.value]
    tec_app.api_key = api_key

    fiche_valeur_app: FicheValeurs = douanes_models[fiche_valeur.value]
    fiche_valeur_app.api_key = api_key

    regimes_app: RegimeEconomique = douanes_models[regimes.value]
    regimes_app.api_key = api_key

    fiscalite_app: FiscaliteDouaniere = douanes_models[fiscalite.value]
    fiscalite_app.api_key = api_key

    taxes_applicables_app:  FiscaliteDouaniere = douanes_models[fiscalite.value]
    taxes_applicables_app.api_key = api_key

    def to_openai_message(data: str):
        if isinstance(data, str):
            yield {
                "choices": [
                    {
                        "delta": {
                            "content": data
                        }
                    }
                ]
            }
        return data

    def title_gen(title: str):
        if stream:
            yield from to_openai_message(f"\n\n{title.upper()} : \n")
        else:
            return title

    codes_response = codes_app.answer(question, stream=stream, n_result=2)
    tec_response = tec_app.answer(question, stream=stream, n_result=5)
    fiche_valeur_response = fiche_valeur_app.answer(
        question, stream=stream, n_result=10)
    regimes_response = regimes_app.answer(question, stream=stream, n_result=10)

    taxes_applicables_app = taxes_applicables_app.taxes_appliquables()
    taxes_appliquables_response = taxes_applicables_app.answer(
        question, stream=stream)

    # fiscalite_response = fiscalite_app.infos_sur_taxes_applicables(
    #     map(get_message, taxes_appliquables_response), stream=stream)

    # yield from title_gen("Fiscalité ")
    # yield from fiscalite_response

    response = [
        title_gen("Codes des douanes"),
        codes_response,
        title_gen("Tarif exterieu commun"),
        tec_response,
        title_gen("Fiche des valeurs"),
        fiche_valeur_response,
        title_gen("Régimes économiques"),
        regimes_response,
        title_gen("Taxes applicables"),
        taxes_appliquables_response,
    ]

    if stream:
        concatenated_generator = chain.from_iterable(response)

        return return_response(concatenated_generator, stream=stream)
    else:
        response = "\n".join(response)
        return return_response(response, stream=stream)
