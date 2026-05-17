from typing import (
    Callable,
    Coroutine,
    Any
)
import asyncio
import websockets.asyncio.server as AsyncWebSocket

from .websocket_unit import WebSocketUnit

from src.core.logger.logger import LogCreator

logger = LogCreator.instance.create(__name__)
class WebSocketServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.on_connect: Callable[[WebSocketUnit], None | Coroutine[Any, Any, None]] | None = None
        self.on_ready: Callable[[], None | Coroutine[Any, Any, None]] | None = None
        self._close_signal = asyncio.Event()

    async def _on_connect_handler(self, websocket: AsyncWebSocket.ServerConnection):
        address = "unknow"
        if len(websocket.remote_address) > 0:
            address = websocket.remote_address[0]
        logger.info(f"New connection from {address}")
        if not self.on_connect:
            logger.warning("No on_connect handler")
            await websocket.close(code=1011, reason="InternalServerError")
            return
        unit = WebSocketUnit(websocket)
        t = self.on_connect(unit)
        if asyncio.iscoroutine(t):
            try:
                await t
                return
            except Exception as e:
                logger.error(f"An error occurred: {e}", exc_info=e)
                await websocket.close(code=1011, reason="InternalServerError")
                return

    async def start(self):
        async with AsyncWebSocket.serve(self._on_connect_handler, self.host, self.port):
            if self.on_ready:
                res = self.on_ready()
                if asyncio.iscoroutine(res):
                    await res
            self._close_signal.clear()
            await self._close_signal.wait()

    async def stop(self):
        self._close_signal.set()
