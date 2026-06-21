import asyncio

import uuid

from .ipc_base import IPCBase
from .protocols import Protocols
from .protocols.types import *
from .exceptions import *

from typing import (
    Callable,
    Coroutine,
    Any
)

class InvokeRequestState:
    def __init__(self, request: InvokeRequest):
        self.request = request
        self.future = asyncio.Future()
    
    def set_result(self, result: Any):
        self.future.set_result(result)
    
    def set_exception(self, exception: Exception):
        self.future.set_exception(exception)
    
    async def wait(self, timeout: int = 0):
        if timeout == 0:
            return await self.future
        try:
            return await asyncio.wait_for(self.future, timeout)
        except asyncio.TimeoutError as e:
            raise e


class IPC(IPCBase):
    def __init__(self, ws_url: str):
        self._protocols = Protocols(ws_url, self)

        self._invoke_handlers: dict[str, Callable[[dict[str, Any]], Coroutine | Any]] = {}
        self._event_handlers: dict[str, Callable[[dict[str, Any]], Coroutine | None]] = {}
        self._once_event_handlers: dict[str, Callable[[dict[str, Any]], Coroutine | None]] = {}

        self._invoke_states_lock = asyncio.Lock()
        self._invoke_states: dict[str, InvokeRequestState] = {}

        self.on_ready: Callable[[], Coroutine | None] | None = None
        self.on_end: Callable[[], Coroutine | None] | None = None
    
    @property
    def ready(self):
        return self._protocols.running

    async def _connected_handler(self):
        if self.on_ready:
            call_result = self.on_ready()
            if asyncio.iscoroutine(call_result):
                await call_result
    
    async def _dicconnected_handler(self):
        if self.on_end:
            call_result = self.on_end()
            if asyncio.iscoroutine(call_result):
                await call_result

        await self._invoke_states_lock.acquire()
        for state in self._invoke_states.values():
            state.future.cancel()
        self._invoke_states_lock.release()

    
    async def start(self):

        self._protocols.on_error = lambda e: print(f"[IPC] Error: {e}")
        self._protocols.on_connected = self._connected_handler
        try:
            await self._protocols.start()
        except Exception as e:
            raise IPCConnectError(f"Failed to connect to the IPC server: {e}") from e
        
        await self._dicconnected_handler()
    
    async def stop(self):
        await self._protocols.stop()
    
    def on(self, name: str, handler: Callable[[dict[str, Any]], Coroutine | None], once: bool = False):
        if once:
            self._once_event_handlers[name] = handler
        else:
            self._event_handlers[name] = handler
    
    def register_invoke(self, name: str, handler: Callable[[dict[str, Any]], Coroutine | Any]):
        self._invoke_handlers[name] = handler
    
    async def invoke(self, name: str, args: dict[str, Any] | None = None, timeout: int = 0) -> Any:
        if args is None:
            args = {}
        await self._invoke_states_lock.acquire()
        # 创建请求
        id = str(uuid.uuid4())
        request = InvokeRequest(id=id, method=name, arguments=args)
        self._invoke_states[id] = InvokeRequestState(request)

        # 发送请求
        try:
            await self._protocols.send_message(request)
        except IPCSendError as e:
            del self._invoke_states[id]
            raise IPCSendError(f"Failed to send invoke request: {e}") from e
        finally:
            self._invoke_states_lock.release()

        # 等待响应
        try:
            result = await self._invoke_states[id].wait(timeout)
            return result
        except IPCInvokeError as e:
            raise e
        except asyncio.CancelledError as e:
            raise e
        except asyncio.TimeoutError as e:
            raise InvokeTimeoutError(f"Invoke timeout: {e}") from e
        except Exception as e:
            raise e
        finally:
            del self._invoke_states[id]
            self._invoke_states_lock.release()
        

    async def emit(self, name: str, args: dict[str, Any] | None = None):
        if args is None:
            args = {}
        
        # 创建请求
        event_request = EventRequest(id=str(uuid.uuid4()), name=name, arguments=args)

        # 发送请求
        try:
            await self._protocols.send_message(event_request)
        except IPCSendError as e:
            raise IPCEventRequestError(f"Failed to send event request: {e}") from e
    
    
    async def event_request(self, args: EventRequest):
        # 事件
        handler = self._event_handlers.get(args.name)
        if handler:
            call_result = handler(args.arguments)
            if asyncio.iscoroutine(call_result):
                await call_result
        
        # 一次性事件
        once_handler = self._once_event_handlers.get(args.name)
        if once_handler:
            del self._once_event_handlers[args.name]
            call_result = once_handler(args.arguments)
            if asyncio.iscoroutine(call_result):
                await call_result
    
    async def invoke_request(self, args: InvokeRequest) -> InvokeResponse:
        handler = self._invoke_handlers.get(args.method)
        if not handler:
            return InvokeResponse(id=args.id, message="no handler", code=404)
        
        try:
            res = handler(args.arguments)
            if asyncio.iscoroutine(res):
                res = await res
            return InvokeResponse(id=args.id, message="success", code=0, result=res)
        except IPCInvokeError as e:
            return InvokeResponse(id=args.id, message=str(e), code=1)
        except Exception as e:
            return InvokeResponse(id=args.id, message=str(e), code=-1)
    
    
    async def invoke_response(self, args: InvokeResponse):
        await self._invoke_states_lock.acquire()
        state = self._invoke_states.get(args.id)
        self._invoke_states_lock.release()
        if state:
            if args.code == 0:
                state.set_result(args.result)
            else:
                state.set_exception(IPCInvokeError(args.message))
    
    async def error(self, args: ProtocolError):
        print(f"[IPC] Error: {args.message}, Code: {args.code}")