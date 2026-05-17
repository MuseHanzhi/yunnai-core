from typing import (
    Callable,
    Coroutine,
    Any
)
import asyncio
import websockets

from .websocket_unit import WebSocketUnit

from src.core.logger.logger import LogCreator

logger = LogCreator.instance.create(__name__)
class WebSocketServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.serve: websockets.serve | None = None
        self.server: websockets.Server | None = None
        self.on_connect: Callable[[WebSocketUnit], None | Coroutine[Any, Any, None]] | None = None

    async def _on_connect_handler(self, websocket: websockets.ServerConnection):
        logger.info(f"New connection from {websocket.remote_address}")
        if self.on_connect:
            unit = WebSocketUnit(websocket)
            t = self.on_connect(unit)
            if asyncio.iscoroutine(t):
                try:
                    await t
                except Exception as e:
                    logger.error(f"An error occurred: {e}", exc_info=e)
                    await websocket.close(code=500, reason="InternalServerError")

        logger.warning("No on_connect handler")
        await websocket.close(code=500, reason="InternalServerError")

    async def start(self):
        self.serve = websockets.serve(self._on_connect_handler, self.host, self.port)
        self.server = await self.serve

    async def stop(self):
        if self.server:
            self.server.close()
