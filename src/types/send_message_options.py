from typing import (
    TypedDict,
    NotRequired
)

class SendMessageOptions(TypedDict):
    model_name: str
    stream: NotRequired[bool]
    request_id: NotRequired[str | None]
