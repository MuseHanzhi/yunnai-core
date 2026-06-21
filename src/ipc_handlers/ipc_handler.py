import asyncio
from typing import (
    TYPE_CHECKING
)

# from src.components.gateway.gateway_client import GatewayClient
from src.components.ipc_com.ipc import IPC
from .modules.application_module.handler import Handler as AppHandler

if TYPE_CHECKING:
    from src.application import Application

class IPCHandler:
    def __init__(self, app: "Application", ipc: IPC | None):
        self.app = app
        if ipc is not None:
            self.app_module = AppHandler(self.app, ipc)
        
        self.ipc = ipc
    
    def init(self):
        ...
