import pydantic
from pydantic import BaseModel
from typing import (
    Any,
    Literal
)
import datetime
import math

class BaseProtocol(BaseModel):
    id: str
    timestamp: int = pydantic.Field(default_factory=lambda: math.floor(datetime.datetime.now().timestamp() * 1000))
    type: Literal["event", "invoke-request", "invoke-response", "error"]

class Event(BaseProtocol):
    type: Literal["event"] = "event"
    name: str
    arguments: dict[str, Any] | None

class InvokeRequest(BaseProtocol):
    type: Literal["invoke-request"] = "invoke-request"
    method: str
    arguments: dict[str, Any] | None

class InvokeResponse(BaseProtocol):
    type: Literal["invoke-response"] = "invoke-response"
    success: bool
    message: str
    result: Any | None

class ProtocolError(BaseProtocol):
    id: str = pydantic.Field(default_factory=lambda: "")
    type: Literal["error"] = "error"
    message: str
