import asyncio

from typing import (
    TYPE_CHECKING,
    Any
)
from .types import *
from src.ipc_handlers.types import IPCInvokeResult
from src.components.ipc.ipc import IPCServer
from src.core.logger.logger import LogCreator

if TYPE_CHECKING:
    from src.application import Application

logger = LogCreator.instance.create(__name__)

class Handler:
    def __init__(self, app: "Application", ipc: IPCServer):
        self.app = app
        self.ipc = ipc
        self.event_loop: asyncio.AbstractEventLoop = app.event_loop
        self.init()
    
    def init(self):
        self.ipc.on('send_message', self.send_message)
        self.ipc.on('close_app', self.close_app)
        self.ipc.on("ready", self.ready)
    
    def ready(self, params: dict):
        ...
        # mcp_list: dict[str, MCPStdioOption | MCPStreamableHTTPOption] | None = params.get("mcp_list", None)
        # client_info: SysInfo | None = params.get("client_info", None)

        # if mcp_list is None or client_info is None:
        #     logger.warning("[MCP] No mcp_list or client_info provided")
        #     return
        
        # self.app.mcp_manager.load(mcp_list, client_info)
    
    def close_app(self, params: dict):
        self.app.exit()
    
    def send_message(self, params: Any):
        message: MessageOptions = params
        self.event_loop.create_task(self.app.send_message(message['message'], {
            "request_id": message.get("request_id", ""),
            "model_name": message["model_name"],
            "stream": message.get("stream", True)
        }))
