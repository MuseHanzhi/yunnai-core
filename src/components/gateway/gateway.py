import tomllib
import base64
import asyncio
import json

import websockets

from src.core.logger.logger import LogCreator
from .websockets.websocket_server import WebSocketServer
from .websockets.websocket_unit import WebSocketUnit
from .types import *
from .protocals.types import *
from .base_gateway_client import BaseGatewayClient

from typing import (
    Callable,
    Coroutine,
    Any,
    cast
)

logger = LogCreator.instance.create(__name__)
class Gateway:
    def __init__(self, gateway_client: BaseGatewayClient, config: GatewayConfig, event_loop: asyncio.AbstractEventLoop | None):
        self.gateway_client = gateway_client
        self.config = config
        self.event_loop = event_loop or asyncio.get_event_loop()
        self.ws_server = WebSocketServer(config.host, config.port)
        self.connections: dict[str, WebSocketUnit] = {}
        self.on_connect: Callable[[str], None | Coroutine[Any, Any, None]] | None = None
        self.on_disconnect: Callable[[str], None | Coroutine[Any, Any, None]] | None = None
    
        self.on_ready: Callable[[], None | Coroutine] | None = None

    @property
    def has_connection(self):
        return bool(self.connections)
    
    async def send(self, message: str | bytes, appid: str | None = None):
        if appid is None:
            for appid in self.connections:
                await self.send(message, appid)
            return
        
        if appid not in self.connections:
            logger.warning(f"appid '{appid}' not found")
            return
        try:
            await self.connections[appid].send(message)
        except websockets.ConnectionClosed | websockets.ConnectionClosedOK as e:
            del self.connections[appid]
            raise Exception("Client disconnected") from e
    
    async def _handle_message(self, message: str | bytes, websocket: WebSocketUnit, appid: str):
        base_protocal: BaseProtocal
        data_dict: dict
        try:
            data_dict: dict = json.loads(message)
            base_protocal = BaseProtocal.model_validate(data_dict)
        except json.JSONDecodeError:
            await websocket.send(ProtocalError(type="error", message="Invalid protocal").model_dump_json())
            return
        
        # 错误
        if base_protocal.type == "error":
            error_data: ProtocalError
            try:
                error_data = ProtocalError.model_validate(data_dict)
            except:
                await websocket.send(ProtocalError(type="error", message="Invalid protocal").model_dump_json())
                return
            try:
                res = self.gateway_client.error_response(appid, error_data)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error("on_error_response error", exc_info=e)
        # 事件
        elif base_protocal.type == "event":
            event: Event
            try:
                event = Event.model_validate(data_dict)
            except:
                await websocket.send(ProtocalError(type="error", message="Invalid protocal").model_dump_json())
                return
            try:
                res = self.gateway_client.event_request(appid, event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error("on_event_request error", exc_info=e)
        # 调用请求
        elif base_protocal.type == "invoke-request":
            invoke_request: InvokeRequest
            try:
                invoke_request = InvokeRequest.model_validate(data_dict)
            except:
                await websocket.send(ProtocalError(type="error", message="Invalid protocal").model_dump_json())
                return
            try:
                res = self.gateway_client.invoke_request(appid, invoke_request)
                result: InvokeResponse
                if asyncio.iscoroutine(res):
                    result = cast(InvokeResponse, await res)
                else:
                    result = res
                await self.send(result.model_dump_json(), appid)
            except Exception as e:
                logger.error("on_invoke_request error", exc_info=e)
        # 调用响应
        elif base_protocal.type == "invoke-response":
            invoke_response: InvokeResponse
            try:
                invoke_response = InvokeResponse.model_validate(data_dict)
            except:
                await websocket.send(ProtocalError(type="error", message="Invalid protocal").model_dump_json())
                return
            try:
                res = self.gateway_client.invoke_response(appid, invoke_response)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error("on_invoke_response error", exc_info=e)
        # 其他
        else:
            logger.warning(f"received unknow type '{base_protocal.type}'")
            try:
                await websocket.send(ProtocalError(type="error", message=f"type '{base_protocal.type}' is no support").model_dump_json())
            except Exception as e:
                logger.error("send error", exc_info=e)
        

    
    def _parse_token(self, token: str) -> TokenInfo | None:
        try:
            token_str = base64.b64decode(token).decode().split(",")
            return TokenInfo.model_validate({
                "token": token_str[0],
                "appid": token_str[1]
            })
        except:
            return None
    
    def _find_client(self, appid: str) -> App | None:
        for app in self.config.apps:
            if app.appid == appid:
                return app
        return None
    
    async def _on_ws_connect(self, websocket_unit: WebSocketUnit):
        if len(self.connections) >= self.config.max_count:
            logger.warning(f"too many connections")
            await websocket_unit.close(4029, "TooManyConnections")
            return

        token: str | None = websocket_unit.query.get("token", [None])[0]
        if token is None:
            temp_token = websocket_unit.headers.get("Authorization")
            if temp_token:
                splited = temp_token.split(" ")
                if len(splited) != 2:
                    await websocket_unit.close(4001, "Unauthorized")
                    return 
                method, t_token = splited
                if method != "Basic":
                    await websocket_unit.close(4001, "Unauthorized")
                    return 
                token = t_token
            else:
                logger.warning(f"NoToken")
                await websocket_unit.close(4001, "Unauthorized")
                return 

        token_info = self._parse_token(token)
        if token_info is None:
            logger.warning(f"Invalid token")
            await websocket_unit.close(4001, "Unauthorized")
            return
        if token_info.token != self.config.token:
            logger.warning(f"Invalid token")
            await websocket_unit.close(4001, "Unauthorized")
            return
        
        app = self._find_client(token_info.appid)
        if app is None:
            logger.warning(f"Appid '{token_info.appid}' is no exist")
            await websocket_unit.close(4001, "Unauthorized")
            return

        self.connections[app.appid] = websocket_unit
        if self.on_connect:
            res = self.on_connect(app.appid)
            if asyncio.iscoroutine(res):
                await res
        
        # 等待接收消息任务完成，保持连接活跃
        await self._receive_message(websocket_unit, token_info)
    
    async def _receive_message(self, websocket_unit: WebSocketUnit, token_info: TokenInfo):
        async def inner_receive_message(message: str | bytes):
            try:
                logger.debug(f"received message, length: {len(message)}")
                await self._handle_message(message, websocket_unit, token_info.appid)
            except Exception as e:
                logger.error("receive_message error", exc_info=e)

        try:
            await websocket_unit(inner_receive_message)
        except websockets.ConnectionClosed | websockets.ConnectionClosedOK as e:
            del self.connections[token_info.appid]
            if self.on_disconnect:
                address = "unknow"
                if len(websocket_unit.ws.remote_address) > 0:
                    address = websocket_unit.ws.remote_address[0]
                logger.info(f"{address} disconnected")
                res = self.on_disconnect(token_info.appid)
                if asyncio.iscoroutine(res):
                    await res
    
    def _gateway_ready(self):
        logger.info(f"server start host: {self.config.host}, port: {self.config.port}")
        if self.on_ready:
            self.on_ready()

    async def open(self):
        self.ws_server.on_connect = self._on_ws_connect
        self.ws_server.on_ready = self._gateway_ready
        await self.ws_server.start()

    async def close(self):
        await self.ws_server.stop()