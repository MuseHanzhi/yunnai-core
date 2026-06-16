import json
import websockets
import asyncio

from src.core.logger.logger import LogCreator
from src.components.ipc_com.ipc_base import IPCBase
from src.components.ipc_com.exceptions import *

from .types import *
from typing import (
    Callable,
    Coroutine
)

# region 消息重发任务
# class ACKResendTask:
#     def __init__(self, message: str, timeout: float, protocols: 'Protocols'):
#         self.message = message
#         self.protocols = protocols
#         self.timeout = timeout
#         self.state: Literal["timeout", "pendding", "ok"] = "pendding"

#     async def run(self, ack_timeout: float):
#         await asyncio.sleep(ack_timeout)
#         current_time = ack_timeout
#         while self.state == "pendding" and current_time < self.timeout:
#             await self.protocols.send_message(self.message)
#             await asyncio.sleep(ack_timeout)
#             current_time += ack_timeout
#         if self.state == "pendding":
#             self.state = "timeout"
#             raise ACKTimeoutError("No ACK received within a certain period of time")
        
#     def ok(self):
#         self.state = "ok"
# endregion


logger = LogCreator.instance.create(__name__)
class Protocols:
    def __init__(self, url: str, ipc: IPCBase):
        self.ipc = ipc
        self.url = url
        self.running = False
        self._conn: websockets.ClientConnection | None = None
        self._event_loop = asyncio.get_event_loop()
        self._ping_interval = 5

        self._pong_timeout_reconnect_interval = 3
        self._pong_timeout_reconnect_times = 3
        self._pong_timeout = 5
        self._pong_signal = asyncio.Event()
        
        self.on_connected: Callable[[], Coroutine | None] | None = None
        self.on_disconnected: Callable[[], Coroutine | None] | None = None
        self.on_error: Callable[[Exception], Coroutine | None] | None = None

        # region ACK相关属性
        # self.default_ack_timeout = 30
        # self._request_ack: dict[str, ACKResendTask] = {}
        # self._response_ack: dict[str, ACKResendTask] = {}
        # self._event_ack: dict[str, ACKResendTask] = {}
        # self._error_ack: dict[str, ACKResendTask] = {}
        # endregion
    
    async def _heartbeat_task(self):
        while self.running and self._conn is not None:
            try:
                await self.send_message(HeartbeatMessage(id="", method="ping"))
            except IPCSendError:
                break
            self._pong_signal.clear()

            try:
                await asyncio.wait_for(self._pong_signal.wait(), self._pong_timeout)
                await asyncio.sleep(self._ping_interval)
            except asyncio.TimeoutError:
                try:
                    await self.stop()
                except:
                    pass

                logger.warning("pong timeout")
                exception: Exception
                for i in range(self._pong_timeout_reconnect_times):
                    try:
                        logger.info(f"start reconnect [{i + 1}/{self._pong_timeout_reconnect_times}]")
                        await self.start()
                        break
                    except Exception as e:
                        logger.error("reconnect failed, will retry in 3 seconds", exc_info=e)
                        exception = e
                        if i < self._pong_timeout_reconnect_times - 1:
                            await asyncio.sleep(self._pong_timeout_reconnect_interval)
                
                if self.running:
                    logger.info("reconnect success")
                else:
                    logger.error("reconnect failed", exc_info=exception)
                break

    @staticmethod
    def _try_parse_json(json_data: str | bytes) -> dict[str, Any] | None:
        try:
            json_string: str | bytes = json_data
            if isinstance(json_string, bytes):
                json_string = json_string.decode("utf-8")

            if isinstance(json_string, str) and not (json_string.startswith("{") and json_string.endswith("}")):
                return None
            return json.loads(json_string)
        except json.JSONDecodeError:
            return None

    async def send_message(self, raw_message: BaseProtocol | str):
        if not self.running or self._conn is None:
            raise IPCSendError("The current instance has not been started")
        
        try:
            message = raw_message
            if not isinstance(message, str):
                message = message.model_dump_json()
            await self._conn.send(message)
        except websockets.ConnectionClosedError:
            raise IPCSendError("The connection has been closed")
    
    async def _handle_message(self, raw_message: dict[str, Any] | None):
        if raw_message is None:
            try:
                await self.send_message(ProtocolError(id="", message="The request message is invalid", code=400))
            except IPCSendError as e:
                raise e
            return
        
        message: BaseProtocol
        try:
            message = BaseProtocol.model_validate(raw_message)
        except pydantic.ValidationError:
            try:
                await self.send_message(ProtocolError(id=raw_message.get("id", ""), message="The request message is invalid", code=400))
            except IPCSendError as e:
                raise e
            return
        # region ACK发送与处理
        # ACK
        # try:
        #     await self.send_message(ACKMessage(id=str(uuid.uuid4()), content=message))
        # except IPCSendError as e:
        #     return
        # if message.type == "ack":
        #     ack_message: ACKMessage
        #     try:
        #         ack_message = ACKMessage.model_validate(message)
        #     except pydantic.ValidationError:
        #         try:
                #     await self.send_message(ProtocolError(id="", message="The request message is invalid", code=400))
                # except IPCSendError as e:
                #     raise e
        #         return
        #     type = ack_message.content.type
        #     if type == "event":
        #         self._event_ack[ack_message.content.id].ok()
        #     elif type == "invoke-request":
        #         self._request_ack[ack_message.content.id].ok()
        #     elif type == "ack":
        #         self._response_ack[ack_message.content.id].ok()
        #     else:
        #         try:
        #             await self.send_message(ProtocolError(id="", message="Invalid ACK message", code=400))
        #         except IPCSendError as e:
        #             raise e
        # endregion
            
        if message.type == "invoke-request":
            invoke_request_args: InvokeRequest
            try:
                invoke_request_args = InvokeRequest.model_validate(raw_message)
            except pydantic.ValidationError:
                try:
                    await self.send_message(ProtocolError(id=message.id, message="The request message is invalid", code=400))
                except IPCSendError as e:
                    raise e
                return
            
            try:
                invoke_response = await self.ipc.invoke_request(invoke_request_args)
                await self.send_message(invoke_response)
                # ack_task = ACKResendTask(invoke_response.model_dump_json(), self.default_ack_timeout, self)
                # self._request_ack[invoke_response.id]  = ack_task
            except IPCSendError as e:
                return
            except Exception as e:
                await self.send_message(InvokeResponse(id=message.id, message=f"handler error: {e}", code=500))
                return

        elif message.type == "invoke-response":
            invoke_response_data: InvokeResponse
            try:
                invoke_response_data = InvokeResponse.model_validate(raw_message)
            except pydantic.ValidationError:
                try:
                    await self.send_message(ProtocolError(id=message.id, message="The request message is invalid", code=400))
                except IPCSendError as e:
                    raise e
                return
            
            try:
                await self.ipc.invoke_response(invoke_response_data)
            except Exception as e:
                logger.error(f"error: {e}", exc_info=e)
                return
            
        elif message.type == "event":
            event_request_args: EventRequest
            try:
                event_request_args = EventRequest.model_validate(raw_message)
            except pydantic.ValidationError:
                try:
                    await self.send_message(ProtocolError(id=message.id, message="The request message is invalid", code=400))
                except IPCSendError as e:
                    raise e
                return
            
            try:
                await self.ipc.event_request(event_request_args)
            except Exception as e:
                logger.error(f"error: {e}", exc_info=e)
                return
        elif message.type == "error":

            error_args: ProtocolError
            try:
                error_args = ProtocolError.model_validate(raw_message)
            except pydantic.ValidationError:
                try:
                    await self.send_message(ProtocolError(id=message.id, message="The request message is invalid", code=400))
                except IPCSendError as e:
                    raise e
                return
            
            await self.ipc.error(error_args)
        
        elif message.type == "heartbeat":
            self._pong_signal.set()
    
    async def _receive_message(self, conn: websockets.ClientConnection):
        try:
            async for received_data in conn:
                message = received_data
                json_data: dict[str, Any] | None = self._try_parse_json(message)
                self._event_loop.create_task(self._handle_message(json_data))
        except websockets.ConnectionClosedError | websockets.ConnectionClosedOK:
            self.running = False
        except Exception as e:
            if self.on_error:
                call_result = self.on_error(e)
                if asyncio.iscoroutine(call_result):
                    await call_result

    
    async def start(self):
        if self.running:
            raise RuntimeError("The current instance has been started")
        try:
            async with websockets.connect(self.url) as conn:
                self.running = True
                self._conn = conn
                if self.on_connected:
                    call_result = self.on_connected()
                    if asyncio.iscoroutine(call_result):
                        await call_result

                self._event_loop.create_task(self._heartbeat_task())
                await self._receive_message(conn)
                self.running = False
                if self.on_disconnected:
                    call_result = self.on_disconnected()
                    if asyncio.iscoroutine(call_result):
                        await call_result
        except Exception as e:
            raise IPCConnectError(f"Failed to connect to the IPC server: {e}") from e
    
    async def stop(self):
        if not self.running or self._conn is None:
            return
        await self._conn.close(websockets.CloseCode.NORMAL_CLOSURE, "normal close")
        self.running = False