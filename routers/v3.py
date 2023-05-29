
from enum import Enum
import dotenv
from fastapi import APIRouter
from douanes.utils.chained_ai import BaseChainedAi
from douanes.pays import DouanesTogolaises

router = APIRouter()


class DouanesPaysEnum(str, Enum):
    TOGO = "togo"
    BENIN = "benin"


douanes_pays = {
    DouanesPaysEnum.TOGO: DouanesTogolaises(),
}


OPENAI_API_KEY = dotenv.get_key(".env", "OPENAI_API_KEY")


def get_douanes_pays(douanes_pays_enum: DouanesPaysEnum) -> BaseChainedAi:
    return douanes_pays[douanes_pays_enum]


@router.get("/togo")
def douanes_togolaise(question: str = "Je veux importer des tomates concentrées depuis la Chine. Quels dois-je savoir ?", api_key: str | None = OPENAI_API_KEY):
    llm = get_douanes_pays(DouanesPaysEnum.TOGO)
    llm.api_key = api_key
    return llm.answer(question)
