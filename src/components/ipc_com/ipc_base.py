from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .protocols.types import *

class IPCBase(ABC):
    @abstractmethod
    async def event_request(self, args: "EventRequest"):
        ...
    
    @abstractmethod
    async def invoke_request(self, args: "InvokeRequest") -> "InvokeResponse":
        ...
    
    @abstractmethod
    async def invoke_response(self, args: "InvokeResponse"):
        ...
    
    @abstractmethod
    async def error(self, args: "ProtocolError"):
        ...
