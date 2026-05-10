from typing import (
    TypedDict,
    NotRequired,
    Any
)

class IPCInvokeResult(TypedDict):
    success: bool
    message: str
    data: NotRequired[Any]
