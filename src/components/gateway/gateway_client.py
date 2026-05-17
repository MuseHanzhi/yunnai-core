import pathlib
import tomllib
import asyncio
import uuid

from src.core import app_context
from src.core.logger.logger import LogCreator

from .base_gateway_client import BaseGatewayClient
from .exceptions import *
from .protocals.types import *
from .types import *
from .gateway import Gateway

from typing import (
    Coroutine,
    Callable,
    Any
)


logger = LogCreator.instance.create(__name__)
class GatewayClient(BaseGatewayClient):
    def __init__(self, event_loop: asyncio.AbstractEventLoop | None):
        self.config: GatewayConfig = self._load_config(app_context.data_home)
        self.gateway = Gateway(self, self.config, event_loop)
        self.event_loop = event_loop or asyncio.get_event_loop()
        
        # appid.request_id -> InvokeRequestSession
        self.request_sessions: dict[str, dict[str, InvokeRequestSession]] = {}

        self.event_handlers: dict[str, list[Callable[[Any, str], Coroutine[Any, Any, None] | None]]] = {}
        self.invoke_handlers: dict[str, Callable[[Any, str], Coroutine[Any, Any, None] | None]] = {}

        self.on_ready: Callable[[], None | Coroutine] | None = None
        self.on_connect: Callable[[str], None | Coroutine] | None = None
        self.on_disconnect: Callable[[str], None | Coroutine] | None = None
    
    def _load_config(self, data_home: str) -> GatewayConfig:
        path = pathlib.Path(data_home) / "gateway.toml"
        if not path.exists():
            # 创建默认配置文件
            config = GatewayConfig.model_validate({
                "host": "127.0.0.1",
                "port": 8866,
                "token": "token_abc",
                "max_count": 5,
                "apps": []
            })
            path.write_text("""host="127.0.0.1"
port=8866
token="token_abc"
max_count=5
""", encoding="utf-8")
            logger.info(f"created gateway.toml")
            return config
        
        try:
            config_text = path.read_text(encoding="utf-8")
            config_dict = tomllib.loads(config_text)
            return GatewayConfig.model_validate(config_dict)
        except Exception as e:
            logger.error(f"An error occurred while reading the configuration file. Please check the 'gateway.toml' configuration file", exc_info=e)
            raise e
    
    async def error_response(self, appid: str, error: ProtocalError):
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
        any_app_session = self.request_sessions.get("*")
        if any_app_session:
            session = any_app_session.get(response.id)
        else:
            appid_response = self.request_sessions.get(appid, {})
            session = appid_response.get(response.id)

        if session:
            if session["signal"].is_set():
                del self.request_sessions[response.id]
                return
            session["result"] = response.result
            session["signal"].set()
            del self.request_sessions[response.id]
        else:
            logger.warning(f"appid: {appid}, invoke: {response.id}. no session")
    
    async def invoke(self, name: str, args: dict[str, Any] | None = None, appid: str | None = None, timeout: int = 10000) -> Any:
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

        async def timeout_task():
            await asyncio.sleep(timeout / 1000)
            if session["signal"].is_set():
                return
            session["signal"].set()
            session["result"] = None
            session["is_timeout"] = True
        if timeout > 0:
            self.event_loop.create_task(timeout_task())

        await session["signal"].wait()

        if session["is_timeout"]:
            raise InvokeSessionTimeoutError(request_id, appid, "invoke session timeout")

        return session["result"]
    
    async def emit(self, name: str, args: dict[str, Any] | None = None, appid: str | None = None):
        event = Event(id=str(uuid.uuid4()), name=name, arguments=args)
        try:
            await self.gateway.send(event.model_dump_json(), appid)
        except Exception as e:
            logger.error(f"emit: {name}. error: {e}", exc_info=e)

    def register_event(self, event_name: str, event_func: Callable[[str, Any], None | Coroutine[Any, Any, None]]):
        self.event_handlers.setdefault(event_name, []).append(event_func)
    
    def remove_event(self, event_name: str, event_func: Callable[[str, Any], None | Coroutine[Any, Any, None]]):
        self.event_handlers.setdefault(event_name, []).remove(event_func)
    
    def register_handler(self, handler_name: str, handler: Callable[[str, Any], Any | Coroutine[Any, Any, Any]]):
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
