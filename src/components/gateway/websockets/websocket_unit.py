from typing import Callable, Coroutine, Any
from urllib import parse as url_parse
import websockets


class WebSocketUnit:

    async def __call__(self, func: Callable[[bytes | str], Coroutine[Any, Any, None]]):
        try:
            async for message in self.ws:
                await func(message)
        except websockets.ConnectionClosed | websockets.ConnectionClosedError | websockets.ConnectionClosedOK:
            raise
    
    async def close(self, code: int = 1000, reason: str = ""):
        try:
            await self.ws.close(code, reason)
        except websockets.ConnectionClosed | websockets.ConnectionClosedError | websockets.ConnectionClosedOK:
            pass
    
    async def send(self, message: str | bytes):
        try:
            await self.ws.send(message)
        except websockets.ConnectionClosed | websockets.ConnectionClosedError | websockets.ConnectionClosedOK:
            raise

    def __init__(self, ws: websockets.ServerConnection):
        self.ws = ws
        self.query: dict[str, list[str]] = self._parse_query(ws)
        self.headers: websockets.Headers = self._parse_headers(ws)
    
    def _parse_query(self, ws: websockets.ServerConnection) -> dict[str, list[str]]:
        request: websockets.Request | None = ws.request
        if request is None:
            return {}
        query_string = url_parse.urlsplit(request.path).query
        return url_parse.parse_qs(query_string)

    def _parse_headers(self, ws: websockets.ServerConnection) -> websockets.Headers:
        request: websockets.Request | None = ws.request
        if request is None:
            return websockets.Headers()
        return request.headers
