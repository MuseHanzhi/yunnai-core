import asyncio
from typing import (
    TYPE_CHECKING
)

from src.components.gateway.gateway_client import GatewayClient
from .modules.application_module.handler import Handler as AppHandler

if TYPE_CHECKING:
    from src.application import Application

class IPCHandler:
    def __init__(self, app: "Application", ipc: GatewayClient):
        self.app = app
        self.event_loop: asyncio.AbstractEventLoop = app.event_loop
        self.app_module = AppHandler(self.app, ipc)
        
        self.ipc = ipc
    
    def init(self):
        ...
