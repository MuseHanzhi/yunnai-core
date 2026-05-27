from abc import ABC, abstractmethod
from typing import Coroutine
from .protocols.types import *


class BaseGatewayClient(ABC):
    @abstractmethod
    async def event_request(self, appid: str, event: Event) -> Coroutine[Any, Any, None] | None:
        ...
    
    @abstractmethod
    async def invoke_request(self, appid: str, request: InvokeRequest) -> Coroutine[Any, Any, InvokeResponse] | InvokeResponse:
        ...
    
    @abstractmethod
    async def invoke_response(self, appid: str, response: InvokeResponse) -> Coroutine[Any, Any, None] | None:
        ...
    
    @abstractmethod
    async def error_response(self, appid: str, error: ProtocolError) -> Coroutine[Any, Any, None] | None:
        ...
