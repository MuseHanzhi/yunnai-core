import asyncio

from typing import (
    TYPE_CHECKING,
    Any
)
from .types import *
from src.ipc_handlers.types import IPCInvokeResult
# from src.components.gateway.gateway_client import GatewayClient
from src.components.ipc_com.ipc import IPC
from src.core.logger.logger import LogCreator

if TYPE_CHECKING:
    from src.application import Application

logger = LogCreator.instance.create(__name__)

class Handler:
    def __init__(self, app: "Application", ipc: IPC):
        self.app = app
        self.ipc = ipc
        self.event_loop: asyncio.AbstractEventLoop = app.event_loop
        self.init()
    
    def init(self):
        self.ipc.on('send_message', self.send_message)
        self.ipc.on('close_app', self.close_app)
    
    async def close_app(self, _: dict):
        await self.app.exit()
    
    def send_message(self, params: Any):
        message: MessageOptions = params
        self.event_loop.create_task(self.app.send_message(message['message'], {
            "model_name": message["model_name"],
            "stream": message.get("stream", True),
            "additional": {
                **message.get("additional", {}),
            }
        }))
