import asyncio
from typing import (
    TYPE_CHECKING
)

from src.components.ipc.ipc import IPCServer
from .modules.application_module.handler import Handler as AppHandler

if TYPE_CHECKING:
    from src.application import Application

class IPCHandler:
    def __init__(self, app: "Application", ipc: IPCServer):
        self.app = app
        self.event_loop: asyncio.AbstractEventLoop = app.event_loop
        self.app_module = AppHandler(self.app, ipc)
        
        self.ipc = ipc
    
    def init(self):
        ...
