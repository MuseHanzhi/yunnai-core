import pydantic
from pydantic import BaseModel
from typing import (
    Any,
    Literal
)
import datetime
import math

class BaseProtocal(BaseModel):
    id: str
    timestamp: int = pydantic.Field(default_factory=lambda: math.floor(datetime.datetime.now().timestamp() * 1000))
    type: Literal["event", "invoke-request", "invoke-response", "error"]

class Event(BaseProtocal):
    type: Literal["event"] = "event"
    name: str
    arguments: dict[str, Any] | None

class InvokeRequest(BaseProtocal):
    type: Literal["invoke-request"] = "invoke-request"
    method: str
    arguments: dict[str, Any] | None

class InvokeResponse(BaseProtocal):
    type: Literal["invoke-response"] = "invoke-response"
    success: bool
    message: str
    result: Any | None

class ProtocalError(BaseProtocal):
    id: str = pydantic.Field(default_factory=lambda: "")
    type: Literal["error"] = "error"
    message: str
