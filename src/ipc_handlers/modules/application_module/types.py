from typing import TypedDict, Literal, NotRequired

class ModelOptions(TypedDict):
    model_name: str
    think_mode: bool

class MessageDataOptions(TypedDict):
    filePaths: list[str]
    text: str

class MessageOptions(TypedDict):
    message: str
    model_name: str
    request_id: NotRequired[str]
    tool_call_id: NotRequired[str]
    stream: NotRequired[bool]
    additional: NotRequired[dict]