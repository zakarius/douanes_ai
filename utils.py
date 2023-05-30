
import json
from sse_starlette import EventSourceResponse
from fastapi.responses import PlainTextResponse


def get_message(chunk) -> str:
    message: str = chunk if isinstance(chunk, str) else chunk['choices'][0]['delta'].get(
        "content", "")
    return message.replace(" ", "#SPACE#").replace("\n", "##LINE##")


def get_chat_gpt_message(chunk:  bytes) -> str:
    bytes_str = chunk.decode("utf-8")
    print(bytes_str)
    try:
        msg = json.loads(bytes_str)
        message: str = msg['message']["content"]['parts'][0]
        print(message)
        return message.replace(" ", "##SPACE#").replace("\n", "##LINE##")
    except:
        return bytes_str


def return_response(response, stream: bool = False, prompt_only: bool = False, completor=None):
    if completor == "chat_gpt":
        return EventSourceResponse(map(get_chat_gpt_message, response))

    if stream and not prompt_only:
        return EventSourceResponse(map(get_message, response))
    else:
        return PlainTextResponse(response, media_type="text/plain")
