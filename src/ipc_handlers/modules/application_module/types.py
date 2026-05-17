from typing import TypedDict, Literal, NotRequired

class ModelOptions(TypedDict):
    model_name: str
    think_mode: bool

class MessageDataOptions(TypedDict):
    filePaths: list[str]
    text: str

class MessageOptions(TypedDict):
    message: str
    request_id: str | None
    model_name: str
    stream: NotRequired[bool]
    additional: NotRequired[dict]