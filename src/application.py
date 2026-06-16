from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import asyncio
import time
import os

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk
)

from src.core.logger.logger import LogCreator
from src.core.tools import ToolFunction
from .types.configs import *

from src.components.ipc_com.exceptions import InvokeTimeoutError
from src.components.llm.client import Client as LLMClient, MessageState
from src.components.plugin_manager.plugin_manager import PluginManager
from src.components.llm.message.tool_message import ToolMessage
from src.components.llm.message.user_message import UserMessage
from src.components.ipc_com.ipc import IPC
from src.ipc_handlers.ipc_handler import IPCHandler

from src.types.send_message_options import SendMessageOptions
from src.core import app_context

logger = LogCreator.instance.create(__name__)
class Application:
    """
    **核心类**
    """
    def __init__(self, event_loop: asyncio.AbstractEventLoop):
        # 基础
        sys_config: SystemConfig = SystemConfig.model_validate(app_context.app_config["system"])
        self.thread_executor = ThreadPoolExecutor(sys_config.thread_workers)
        self.event_loop = event_loop
        self.running: bool = False
        
        # 组件
        self.plugin_manager = PluginManager(self)
        self.llm_client: LLMClient = LLMClient()
        # self.gateway_client = GatewayClient(self.event_loop)
        self.ipc: IPC | None = self._create_ipc()
        
        self.ipc_handler: IPCHandler = IPCHandler(self, self.ipc)
        self._tool_functions: list[ToolFunction] = []
        self._identity = str(uuid4())

    
    @staticmethod
    def _create_ipc():
        ipc_url = app_context.launch_args.ipc_url
        if ipc_url is None:
            return None
        return IPC(ipc_url)

    
    async def exit(self):
        try:
            await self.plugin_manager.trigger("on_app_will_close", "before", "event")
            if self.ipc and self.ipc.ready:
                await self.ipc.emit("on_app_will_close")
            # await self.gateway_client.emit("on_app_will_close")
            await self.plugin_manager.trigger("on_app_will_close", "after", "event")
            if self.ipc and self.ipc.ready:
                await self.ipc.stop()
            # await self.gateway_client.end()
        except:
            ...
        logger.info("app exit")
    
    async def run_in_thread(self, func, *args, **kwargs):
        try:
            await self.event_loop.run_in_executor(
                self.thread_executor,
                lambda: func(*args, **kwargs)
            )
        except Exception as ex:
            raise ex

    def _setup_llm(self):
        logger.info("setup llm client")
        llm_config: LLMConfigOption = LLMConfigOption.model_validate(app_context.app_config["llm"])
        
        default_llm: str | None = app_context.launch_args.llm or llm_config.default
        if default_llm is None:
            raise Exception("please specify llm model in config or launch args")
        model_config = llm_config.models.get(default_llm)

        logger.info(f"use llm: {default_llm}")
        if model_config is None:
            raise Exception(f"llm model {default_llm} not found")
        
        llm_api_key = os.getenv(model_config.key_name)
        if llm_api_key is None:
            raise Exception(f"请配置{model_config.key_name}环境变量")

        self.llm_client.setup_client({
            "api_key": llm_api_key,
            "base_url": model_config.base_url
        }, model_config.extra_body)

        logger.info("setup llm client ok")

    def _setup_tools(self):
        quit_app_tool = ToolFunction(
            "self.quit_app",
            "关闭应用，必须询问用户二次确认",
            lambda _: self.exit()
        )
        self._tool_functions.append(quit_app_tool)

    async def initialize(self):
        logger.info("application initialize")
        
        self._setup_llm()

        self._setup_tools()

        if self.ipc:
            logger.info("initialize component 'ipc'")
            self.ipc.on_end = lambda: logger.info("component 'ipc' stopped")
            self.ipc.on_ready = lambda: logger.info("component 'ipc' initialized")
            self.event_loop.create_task(self.ipc.start())
            self.ipc_handler.init()
        
        logger.info("initialize component 'plugin manager'")
        self.plugin_manager.initialize(app_context.fixed_config.plugin_config)
        logger.info("initialized component 'plugin manager'")

        # 触发插件对应时机
        await self.plugin_manager.trigger("on_ready", "before", "event")
        await self.plugin_manager.trigger("on_ready", "after", "event")
        asyncio.set_event_loop(self.event_loop)
        logger.info("app ready")
    
    async def _start_response(self, state: MessageState, gateway_additional: dict | None = None):
        is_start = False
        start_ms = time.time() * 1000
        try:
            if state.is_stream:
                # 流式响应
                async for chunk in self.llm_client.stream_response(state):
                    chunk: ChatCompletionChunk
                    if not is_start:
                        logger.info(f"llm stream response start: {(time.time() * 1000) - start_ms}ms")
                        is_start = True
                    await self.plugin_manager.trigger(
                        "on_llm_response",
                        "before",
                        "event",
                        chat_completion = chunk
                    )
                    try:
                        if self.ipc and self.ipc.ready:
                            await self.ipc.emit("llm_response", {
                                "is_stream": True,
                                "chunk": chunk.model_dump(),
                                "additional": gateway_additional
                            })
                    except Exception as ex:
                        logger.error(f"llm_response gateway exception: {ex}", exc_info=ex)
                    await self.plugin_manager.trigger(
                        "on_llm_response",
                        "after",
                        "event",
                        chat_completion = chunk
                    )
            else:
                # 非流式响应
                completion: ChatCompletion = await self.llm_client.non_stream_response(state)
                logger.info(f"llm non_stream response start: {(time.time() * 1000) - start_ms}ms")
                await self.plugin_manager.trigger(
                    "on_llm_response",
                    "before",
                    "event",
                    chat_completion = completion
                )

                try:
                    if self.ipc and self.ipc.ready:
                        await self.ipc.emit("llm_response", {
                            "is_stream": False,
                            "chat_completion": completion.model_dump(),
                            "additional": gateway_additional
                        })
                except Exception as ex:
                    logger.error(f"llm_response gateway exception: {ex}", exc_info=ex)
                
                await self.plugin_manager.trigger(
                    "on_llm_response",
                    "after",
                    "event",
                    chat_completion = completion
                )
            logger.info("llm response end")
        except Exception as ex:
            await self.plugin_manager.trigger(
                "on_llm_response",
                "before",
                "event",
                chat_completion = ex
            )
            try:
                if self.ipc and self.ipc.ready:
                    await self.ipc.emit("llm_response", {
                        "is_stream": False,
                        "error": str(ex),
                        "additional": gateway_additional
                    })
            except Exception as ex:
                logger.error(f"llm_response gateway exception: {ex}", exc_info=ex)
            
            await self.plugin_manager.trigger(
                "on_llm_response",
                "after",
                "event",
                chat_completion = ex
            )
    
    def add_tool(self, tool: ToolFunction):
        self._tool_functions.append(tool)

    async def send_message(self, message: str, option: SendMessageOptions):
        logger.info(f"start handle message: {message}")
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        msg = UserMessage(message)
        if option.get("type") == "tool":
            if "tool_call_id" in option:
                msg = ToolMessage(option["tool_call_id"], message)
            else:
                raise Exception("未提供工具调用ID")
        else:
            msg.add_image(*option.get("image_urls", []))
        state: MessageState = self.llm_client.create_state(option["model_name"], msg, option.get("stream", True))
        state.data.function_calls = [item.get_schema() for item in self._tool_functions]

        # 取消发送插件验证
        def state_cancel_validate(name: str, _: str):
            if name in self.plugin_manager.plugins or self._identity == name:
                return
            return f"'{name}'不在已注册的插件列表中"

        state.cancel_validate_handler = state_cancel_validate
        
        # 触发发送消息前事件/hook
        await self.plugin_manager.trigger("on_message_before_send", "before", state=state, additional=option.get("additional"))
        # 触发IPC
        try:
            if self.ipc and self.ipc.ready:
                result: dict | None
                result = await self.ipc.invoke(
                    "on_message_before_send",
                    {"state": state.to_dict(), "additional": option.get("additional")},
                    3)
                if result is not None and (n_state := result.get("state")):
                    state.update(n_state)
        except InvokeTimeoutError:
            logger.warning("invoke 'on_message_before_send' response timeout")
        except asyncio.CancelledError:
            logger.warning("invoke 'on_message_before_send' cancelled")
        except Exception as ex:
            logger.error(f"invoke 'on_message_before_send' exception: {ex}", exc_info=ex)
            state.cancel(self._identity, f"[Application]invoke 'on_message_before_send' exception: {ex}")
        # 触发发送消息后事件/hook
        await self.plugin_manager.trigger("on_message_before_send", "after", state=state)

        # 检查是否被取消
        if state.canceled:
            logger.warning(f"向大模型发送消息在 '{state.canceller}' 取消, 原因: {state.cancel_reason}")
            await self.plugin_manager.trigger("on_canceled", "before", "event", state=state)
            try:
                if self.ipc and self.ipc.ready:
                    await self.ipc.emit("on_canceled", {
                        "state": state.to_dict(),
                        "additional": option.get("additional")
                    })
                # await self.gateway_client.emit("on_canceled", {
                #     "state": state.to_dict(),
                #     "additional": option.get("additional")
                # })
            except Exception as ex:
                logger.error(f"gateway exception: {ex}", exc_info=ex)
            await self.plugin_manager.trigger("on_canceled", "after", "event", state=state)
            return
        
        # 开始响应任务
        self.event_loop.create_task(self._start_response(state, option.get("additional")))
        
        # 触发消息发送完成事件/hook
        await self.plugin_manager.trigger("on_message_after_sended", "before", "event", state=state)
        try:
            if self.ipc and self.ipc.ready:
                await self.ipc.emit("on_message_after_sended", {
                    "state": state.to_dict()
                })
            # await self.gateway_client.emit("on_message_after_sended", {
            #     "state": state.to_dict()
            # })
        except Exception as ex:
            logger.error(f"gateway exception: {ex}", exc_info=ex)
        await self.plugin_manager.trigger("on_message_after_sended", "after", "event", state=state)

    async def run(self):
        self.running = True
        while self.running:
            await asyncio.sleep(500)
