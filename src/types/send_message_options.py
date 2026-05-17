from typing import (
    TypedDict,
    NotRequired,
    Literal
)

class SendMessageOptions(TypedDict):
    model_name: str
    type: NotRequired[Literal["user", "tool"]]
    tool_call_id: NotRequired[str]
    stream: NotRequired[bool]
    image_urls: NotRequired[list[str]]
    additional: NotRequired[dict[str, str]]
