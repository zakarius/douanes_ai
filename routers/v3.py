from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer

from .shared import *

router = APIRouter()

token_auth_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="Accests Token",
)
# apikey = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJqc21tMnRvZ29AZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJodHRwczovL2FwaS5vcGVuYWkuY29tL2F1dGgiOnsidXNlcl9pZCI6InVzZXItYXhEclVlV0lhQjltcG4xSTVUcWFsckVYIn0sImlzcyI6Imh0dHBzOi8vYXV0aDAub3BlbmFpLmNvbS8iLCJzdWIiOiJnb29nbGUtb2F1dGgyfDExNzAxOTY5MzU3Mjc1OTA4MDMxMCIsImF1ZCI6WyJodHRwczovL2FwaS5vcGVuYWkuY29tL3YxIiwiaHR0cHM6Ly9vcGVuYWkub3BlbmFpLmF1dGgwYXBwLmNvbS91c2VyaW5mbyJdLCJpYXQiOjE2ODQ2OTcxNzQsImV4cCI6MTY4NTkwNjc3NCwiYXpwIjoiVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEciLCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG1vZGVsLnJlYWQgbW9kZWwucmVxdWVzdCBvcmdhbml6YXRpb24ucmVhZCBvcmdhbml6YXRpb24ud3JpdGUifQ.iGT7Op6RO6BncZcPn-5qMYE9C-gLmjf-KD60uBtgqZ4dozTAu7Dfs9bhm3Sreq6wnlpq1lc4__Zt8hXcGTmmg5t4NOGYbGMW_Z2UjtDD161Ing7spIB4bxG6njj41zrc_sIOQbVGhbSZZfz1k8G38lATSYiYVViO1fuhJ4hnOJnV_9ps2rHTRchMoAe6UqwoW2NV_1oajBvLe-UKXqZC7feNSxUGSeJDxWjpWUhRZy--oJuMyYb-ebLmdk804Cqeitxivg9P3X1W7_OiRKLe--OO3Qpqm1kEvqtvrnVi7VflS-N_5nuOKNr-ZGGfe_4LZc_T3lN8Ug5-VzDIiw7VPA"


async def _answer_to_question(req: DouanesRequest,
                              token: Optional[str] = Depends(
                                  token_auth_scheme),
                              ):
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

    api_key = ai_providers[completor] if api_key is None else req.api_key
    assert api_key is not None and api_key.strip() != "", "La clé API est obligatoire"

    app = douanes_models[douanes_ai]

    if completor != AIProviders.OPEN_AI:
        app.api_key = ai_providers[AIProviders.OPEN_AI.value]
        app.token = token
    else:
        app.api_key = api_key

    ai_type = douanes_ai.split("-")[0]

    if ai_type == "tec":
        app.BASE_COLLECTION = tec_collection
    elif ai_type == "fiscalite":
        if response_function == ResponseFunction.TAXES_APPLIQUABLES:
            app.taxes_appliquables()

    response = app.get_info(question, completor=completor, stream=stream, prompt_only=prompt_only,
                            use_gpt4=use_gpt4, n_result=n_result)

    return return_response(
        response=response,
        stream=stream,
        prompt_only=prompt_only,
        completor=completor,
    )


@router.options("/answer")
async def answer_to_question(
    question: str,
    completor: AIProviders = AIProviders.OPEN_AI,
    douanes_ai: DouanesModelsEnum = DouanesModelsEnum.CDN_TOGO_CEDEAO_2017,
    tec_collection: TecCollectionEnum = TecCollectionEnum.ALL,
    stream: bool = False,
    prompt_only: bool = False,
    use_gpt4: bool = False,
    n_result: int = 5,
    response_function: ResponseFunction = ResponseFunction.ANSWER,
    token: Optional[str] = Depends(token_auth_scheme),
):
    request = DouanesRequest(
        question=question,
        completor=completor,
        douanes_ai=douanes_ai,
        tec_collection=tec_collection,
        stream=stream,
        use_gpt4=use_gpt4,
        prompt_only=prompt_only,
        n_result=n_result,
        response_function=response_function,
    )
    return await _answer_to_question(request, token)


@router.get("/togo")
def douanes_togolaise(question: str = "Je veux importer des tomates concentrées depuis la Chine. Quels dois-je savoir ?", api_key: str | None = OPENAI_API_KEY):
    llm = get_douanes_pays(DouanesPaysEnum.TOGO)
    llm.api_key = api_key
    return llm.answer(question)
