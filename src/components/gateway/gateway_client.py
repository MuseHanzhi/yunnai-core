import asyncio
import uuid

from src.core import app_context
from src.core.app_context.types import GatewayOption
from src.core.logger.logger import LogCreator
from src.types.lfecycle_hooks import Hooks

from .base_gateway_client import BaseGatewayClient
from .exceptions import *
from .protocols.types import *
from .types import *
from .gateway import Gateway

from typing import (
    Coroutine,
    Callable,
    Any
)


logger = LogCreator.instance.create(__name__)
InvokeName = Hooks | str
class GatewayClient(BaseGatewayClient):
    def __init__(self, event_loop: asyncio.AbstractEventLoop | None):
        self.config: GatewayOption = app_context.app_config.gateway
        self.gateway = Gateway(self, self.config.server, self.config.apps, event_loop)
        self.event_loop = event_loop or asyncio.get_event_loop()
        
        # appid.request_id -> InvokeRequestSession
        self.request_sessions: dict[str, dict[str, InvokeRequestSession]] = {}

        self.event_handlers: dict[str, list[Callable[[Any, str], Coroutine[Any, Any, None] | None]]] = {}
        self.invoke_handlers: dict[str, Callable[[Any, str], Coroutine[Any, Any, None] | None]] = {}

        self.on_ready: Callable[[], None | Coroutine] | None = None
        self.on_connect: Callable[[str], None | Coroutine] | None = None
        self.on_disconnect: Callable[[str], None | Coroutine] | None = None
    
    async def error_response(self, appid: str, error: ProtocolError):
        logger.error(f"appid: '{appid}'. protocol error: {error.message}")
    
    async def event_request(self, appid: str, event: Event):
        logger.debug(f"appid: '{appid}'. event: {event.name}. request_id: {event.id}")
        handlers = self.event_handlers.get(event.name)
        if not handlers:
            logger.warning(f"event: {event.name}. no handler")
            return
        try:
            for handler in handlers:
                res = handler(event.arguments, appid)
                if asyncio.iscoroutine(res):
                    await res
        except Exception as e:
            logger.error(f"event: {event.name}. error: {e}", exc_info=e)
    
    async def invoke_request(self, appid: str, request: InvokeRequest) -> InvokeResponse:
        logger.debug(f"appid: '{appid}'. invoke: {request.method}. request_id: {request.id}")
        handler = self.invoke_handlers.get(request.method)
        if not handler:
            logger.warning(f"invoke: {request.method}. no handler")
            return InvokeResponse(id=request.id, message="no handler", success=False, result=None)
        try:
            res = handler(request.arguments, appid)
            if asyncio.iscoroutine(res):
                res = await res
            return InvokeResponse(id=request.id, message="success", success=True, result=res)
        except Exception as e:
            logger.error(f"invoke: {request.method}. error: {e}", exc_info=e)
            return InvokeResponse(id=request.id, message=str(e), success=False, result=None)
    
    async def invoke_response(self, appid: str, response: InvokeResponse):
        logger.debug(f"appid: '{appid}'. invoke: {response.id}. response_id: {response.id}")
        app_request_session = self.request_sessions.get("*")
        if app_request_session:
            session = app_request_session.get(response.id)
        else:
            app_request_session = self.request_sessions.get(appid, {})
            session = app_request_session.get(response.id)

        if session:
            if session["signal"].is_set():
                del app_request_session[response.id]
                return
            session["result"] = response.result
            session["signal"].set()
            del app_request_session[response.id]
        else:
            logger.warning(f"appid: {appid}, invoke: {response.id}. no session")
    
    async def _serial_invoke_all(self, name: InvokeName, args: dict | None = None, timeout: int = 10000):
        appids = list(self.gateway.connections.keys())
        if not appids:
            return None
            
        current_args = args
        last_result = None
            
        for appid in appids:
            try:
                last_result = await self.invoke(name, current_args, appid, timeout)
                current_args = last_result
            except Exception as ex:
                logger.error(f"appid: {appid} exception: {ex}", exc_info=ex)
                
        return last_result
    
    async def invoke(self, name: InvokeName, args: dict[str, Any] | None = None, appid: str | None = None, timeout: int = 10000) -> Any:
        if not appid:
            return await self._serial_invoke_all(name, args, timeout)
        if not self.gateway.has_connection:
            logger.warning("no connection. skip invoke request")
            return None
        request_id = str(uuid.uuid4())
        while request_id in self.request_sessions:
            request_id = str(uuid.uuid4())

        request = InvokeRequest(id=request_id, method=name, arguments=args)
        try:
            await self.gateway.send(request.model_dump_json(), appid)
        except Exception:
            raise
            
        session = self._create_sesion(request_id)

        try:
            await asyncio.wait_for(session["signal"].wait(), timeout=timeout / 1000)
        except asyncio.TimeoutError:
            session["is_timeout"] = True
            raise InvokeSessionTimeoutError(request_id, appid, "invoke session timeout")
        finally:
            # 清理 session
            if appid in self.request_sessions and request_id in self.request_sessions[appid]:
                del self.request_sessions[appid][request_id]

        return session["result"]
    
    async def emit(self, name: InvokeName, args: dict[str, Any] | None = None, appid: str | None = None):
        event = Event(id=str(uuid.uuid4()), name=name, arguments=args)
        try:
            await self.gateway.send(event.model_dump_json(), appid)
        except Exception as e:
            logger.error(f"emit: {name}. error: {e}", exc_info=e)

    def register_event(self, event_name: str, event_func: Callable[[Any, str], None | Coroutine[Any, Any, None]]):
        self.event_handlers.setdefault(event_name, []).append(event_func)
    
    def remove_event(self, event_name: str, event_func: Callable[[Any, str], None | Coroutine[Any, Any, None]]):
        self.event_handlers.setdefault(event_name, []).remove(event_func)
    
    def register_handler(self, handler_name: str, handler: Callable[[Any, str], Any | Coroutine[Any, Any, Any]]):
        if handler_name in self.invoke_handlers:
            logger.warning(f"The handler with the same name '{handler_name}' has already been covered")
        self.invoke_handlers[handler_name] = handler
    
    def _create_sesion(self, request_id: str, appid: str | None = None):
        session: InvokeRequestSession = {
                "result": None,
                "signal": asyncio.Event(),
                "start_time": math.floor(datetime.datetime.now().timestamp() * 1000),
                "is_timeout": False
            }
        if appid is None:
            appid = "*"
        self.request_sessions.setdefault(appid, {})[request_id] = session
        return session

    async def _on_connect(self, appid: str):
        await self.emit("hello", {}, appid)
        # self.on_connect

    async def start(self):
        self.gateway.on_connect = self._on_connect
        self.gateway.on_disconnect = self.on_disconnect
        self.gateway.on_ready = self.on_ready
        await self.gateway.open()
    
    async def end(self):
        await self.gateway.close()
