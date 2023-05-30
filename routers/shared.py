from enum import Enum
import dotenv
from pydantic import BaseModel
from douanes.monde import *
from douanes.afrique import *
from douanes.zones import CodeDesDouanesCEDEAO2017, TECCedeao2022
from douanes.pays.togo import CdnTogoEtCedeao2017, CodeDesDouanesTogo2017, DouanesTogolaises, FicheValeurTogo2022, CodesCSTTogo2023, RegimesTogo2021, RegimesTogo2023, FiscaliteDouanesTogo2019, TecTogo2022
from douanes.utils import BaseDouaneAI
from douanes.utils.chained_ai import BaseChainedAi
from douanes.utils.code_des_douanes import CodeDesDouanes
from douanes.utils.fiscalite_douaniere import FiscaliteDouaniere
from douanes.utils.regimes_economiques import RegimeEconomique
from douanes.utils.tarif_exterieur_commun import TarifExterieurCommun
from douanes.utils.valeur_en_douanes import CodesCST, FicheValeurs
from utils import return_response


OPENAI_API_KEY = dotenv.get_key(".env", "OPENAI_API_KEY")
PALM_API_KEY = dotenv.get_key(".env", "PALM_API_KEY")


class DouanesModelsEnum(Enum):
    # CEDEAO
    CDC_CEDEAO_2017 = "cdc-cedeao-2017"
    TEC_CEDEAO_2022 = "tec-cedeao-2022"
    # TOGO
    CDN_TOGO_2017 = "cdn-togo-2017"
    TEC_TOGO_2022 = "tec-togo-2022"
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
    TEC_TOGO_2022 = "tec-togo-2022"


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
    "tec-togo-2022": TecTogo2022(),
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
    CHAT_GPT = "chat_gpt"


ai_providers = {
    "open_ai": OPENAI_API_KEY,
    "google": PALM_API_KEY,
    "chat_gpt": OPENAI_API_KEY,
}


class DouanesPaysEnum(str, Enum):
    TOGO = "togo"
    BENIN = "benin"


douanes_pays = {
    DouanesPaysEnum.TOGO: DouanesTogolaises(),
}


def get_douanes_pays(douanes_pays_enum: DouanesPaysEnum) -> BaseChainedAi:
    return douanes_pays[douanes_pays_enum]


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
