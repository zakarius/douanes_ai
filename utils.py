
from sse_starlette import EventSourceResponse
from fastapi.responses import PlainTextResponse

def get_message(chunk) -> str:
    message: str = chunk['choices'][0]['delta'].get(
        "content", "")
    return message.replace(" ", "\u00a0").replace("\n", "\u0085")


def return_response(response, stream: bool = False, prompt_only: bool = False):
    if stream and not prompt_only:
        return EventSourceResponse(map(get_message, response))
    else:
        return PlainTextResponse(response, media_type="text/plain")
