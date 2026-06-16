import pydantic
from pydantic import BaseModel
import math
import datetime
from typing import (
    Literal,
    Any
)

class BaseProtocol(BaseModel):
    model_config = pydantic.ConfigDict(extra="ignore")
    id: str
    timestamp: int = pydantic.Field(default_factory=lambda: math.floor(datetime.datetime.now().timestamp() * 1000))
    type: Literal["event", "invoke-request", "invoke-response", "error", "ack", "heartbeat"]

class EventRequest(BaseProtocol):
    """
    推送事件
    """
    type: Literal["event"] = "event"
    name: str
    arguments: dict[str, Any] = pydantic.Field(default_factory=dict)

class InvokeRequest(BaseProtocol):
    """
    调用方法
    """
    type: Literal["invoke-request"] = "invoke-request"
    method: str
    arguments: dict[str, Any] = pydantic.Field(default_factory=dict)

class InvokeResponse(BaseProtocol):
    """
    调用响应结果
    """
    type: Literal["invoke-response"] = "invoke-response"
    message: str
    result: Any = pydantic.Field(default_factory=lambda: None)
    code: int = 0

class ProtocolError(BaseProtocol):
    """
    协议错误  
    发生时机：  
        1. 接收到无效的协议包, `code: 400`  
        2. `invoke-request` 时，对方没有提供'method'的处理方法, `code: 404`  
        3. `invoke-request` 的`arguments` 必须是json或者空, `code: 400`  
        4. `type` 不是 `event`, `invoke-request`, `invoke-response`, `error`
    """
    type: Literal["error"] = "error"
    message: str
    code: int

class HeartbeatMessage(BaseProtocol):
    """
    心跳包
    """
    type: Literal["heartbeat"] = "heartbeat"
    method: Literal["ping", "pong"]
    timestamp: int = pydantic.Field(default_factory=lambda: math.floor(datetime.datetime.now().timestamp() * 1000))

class ACKMessage(BaseProtocol):
    """
    ACK
    """
    type: Literal["ack"] = "ack"
    content: BaseProtocol
