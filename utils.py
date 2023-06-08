
import json
from sse_starlette import EventSourceResponse
from fastapi.responses import PlainTextResponse


def get_message(chunk) -> str:
    message: str = chunk if isinstance(chunk, str) else chunk['choices'][0]['delta'].get(
        "content", "")
    return message.replace(" ", "##SPACE##").replace("\n", "##LINE##")


def get_chat_gpt_message(chunk:  bytes) -> str:
    bytes_str = chunk.decode("utf-8")
    try:
        msg = json.loads(bytes_str)
        message: str = msg['message']["content"]['parts'][0]
        return message.replace(" ", "##SPACE##").replace("\n", "##LINE##")
    except:
        return bytes_str


def return_response(response, stream: bool = False, prompt_only: bool = False, completor=None, status_code: int = 200):
    if completor == "chat_gpt":
        return EventSourceResponse(map(get_chat_gpt_message, response), status_code=status_code)

    if stream and not prompt_only:
        return EventSourceResponse(map(get_message, response), status_code=status_code)
    else:
        return PlainTextResponse(response, media_type="text/plain", status_code=status_code)
