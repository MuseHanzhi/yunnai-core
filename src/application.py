from concurrent.futures import ThreadPoolExecutor
import asyncio
import time
import shutil
import sys
import os

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk
)

from src.core.logger.logger import LogCreator
from src.core.tools import ToolFunction

from src.components.llm.client import Client as LLMClient, MessageState
from src.components.plugin_manager.plugin_manager import PluginManager
from src.components.llm.message.tool_message import ToolMessage
from src.components.llm.message.user_message import UserMessage
from src.components.gateway.gateway_client import GatewayClient
from src.ipc_handlers.ipc_handler import IPCHandler
from src.components.gateway.exceptions import InvokeSessionTimeoutError

from src.types.send_message_options import SendMessageOptions
from src.core import app_context

logger = LogCreator.instance.create(__name__)
class Application:
    """
    **核心类**
    """
    def __init__(self, event_loop: asyncio.AbstractEventLoop):
        # 基础
        self.thread_executor = ThreadPoolExecutor(app_context.app_config.system.thread_workers)
        self.event_loop = event_loop
        
        # 组件
        self.plugin_manager = PluginManager(self)
        self.llm_client: LLMClient = LLMClient()
        self.gateway_client = GatewayClient(self.event_loop)
        
        self.ipc_handler: IPCHandler = IPCHandler(self, self.gateway_client)
        self._tool_functions: list[ToolFunction] = []
    
    async def exit(self):
        try:
            await self.plugin_manager.trigger("on_app_will_close", "before")
            await self.gateway_client.emit("on_app_will_close")
            await self.plugin_manager.trigger("on_app_will_close", "after")
            await self.gateway_client.end()
        except:
            ...
        self.event_loop.stop()
        logger.info("event loop stop")
    
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
        
        default_llm: str | None = app_context.launch_args.llm or app_context.app_config.llm.default
        if default_llm is None:
            raise Exception("please specify llm model in config or launch args")
        llm_config = app_context.app_config.llm.models.get(default_llm)

        logger.info(f"use llm: {default_llm}")
        if llm_config is None:
            raise Exception(f"llm model {default_llm} not found")
        
        llm_api_key = os.getenv(llm_config.key_name)
        if llm_api_key is None:
            raise Exception(f"请配置{llm_config.key_name}环境变量")

        self.llm_client.setup_client({
            "api_key": llm_api_key,
            "base_url": llm_config.base_url
        }, llm_config.extra_body)

        logger.info("setup llm client ok")

    def _setup_tools(self):
        quit_app_tool = ToolFunction(
            "self.quit_app",
            "关闭应用，必须询问用户二次确认",
            lambda _: self.exit()
        )
        self._tool_functions.append(quit_app_tool)

    def initialize(self):
        logger.info("application initialize")
        
        self._setup_llm()

        self.ipc_handler.init()

        self._setup_tools()

        async def start_gateway():
            try:
                logger.info("initialize component 'gateway client'")
                self.gateway_client.on_ready = lambda: logger.info("component 'gateway' initialized")
                await self.gateway_client.start()
            except Exception as ex:
                logger.error("initialize component 'gateway client' error", exc_info=ex)
        self.event_loop.create_task(start_gateway())
        
        logger.info("initialize component 'plugin manager'")
        self.plugin_manager.initialize(app_context.fixed_config.plugin_config)
        logger.info("initialized component 'plugin manager'")

        # 触发插件对应时机
        asyncio.gather(
                self.plugin_manager.trigger("on_ready", "before"),
                self.plugin_manager.trigger("on_ready", "after")
            )
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
                        chat_completion = chunk
                    )
                    try:
                        await self.gateway_client.emit("llm_response", {
                            "is_stream": True,
                            "chunk": chunk.model_dump(),
                            "additional": gateway_additional
                        })
                    except Exception as ex:
                        logger.error(f"llm_response gateway exception: {ex}", exc_info=ex)
                    await self.plugin_manager.trigger(
                        "on_llm_response",
                        "after",
                        chat_completion = chunk
                    )
            else:
                # 非流式响应
                completion: ChatCompletion = await self.llm_client.non_stream_response(state)
                logger.info(f"llm non_stream response start: {(time.time() * 1000) - start_ms}ms")
                await self.plugin_manager.trigger(
                    "on_llm_response",
                    "before",
                    chat_completion = completion
                )

                try:
                    await self.gateway_client.emit("llm_response", {
                            "is_stream": False,
                            "chat_completion": completion.model_dump(),
                            "additional": gateway_additional
                        })
                except Exception as ex:
                    logger.error(f"llm_response gateway exception: {ex}", exc_info=ex)
                
                await self.plugin_manager.trigger(
                    "on_llm_response",
                    "after",
                    chat_completion = completion
                )
            logger.info("llm response end")
        except Exception as ex:
            await self.plugin_manager.trigger(
                "on_llm_response",
                "before",
                chat_completion = ex
            )
            try:
                await self.gateway_client.emit("llm_response", {
                        "is_stream": False,
                        "error": str(ex),
                        "additional": gateway_additional
                    })
            except Exception as ex:
                logger.error(f"llm_response gateway exception: {ex}", exc_info=ex)
            
            await self.plugin_manager.trigger(
                "on_llm_response",
                "after",
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
        
        # 触发发送消息前事件/hook
        await self.plugin_manager.trigger("on_message_before_send", "before", state=state, additional=option.get("additional"))
        try:
            result: dict | None = await self.gateway_client.invoke("on_message_before_send", {
                "state": state.to_dict(),
                "additional": option.get("additional")
            }, timeout=20000)
            if result is not None and (n_state := result.get("state")):
                state.update(n_state)
        except InvokeSessionTimeoutError:
            logger.warning("invoke响应超时")
        except Exception as ex:
            logger.error(f"gateway or 'MessageState.model_validate' exception: {ex}", exc_info=ex)
            state.cancel()
        await self.plugin_manager.trigger("on_message_before_send", "after", state=state)

        # 检查是否被取消
        if state.canceled:
            await self.plugin_manager.trigger("on_canceled", "before", state=state)
            try:
                await self.gateway_client.emit("on_canceled", {
                    "state": state.to_dict(),
                    "additional": option.get("additional")
                })
            except Exception as ex:
                logger.error(f"gateway exception: {ex}", exc_info=ex)
            await self.plugin_manager.trigger("on_canceled", "after", state=state)
            return
        
        # 开始响应任务
        self.event_loop.create_task(self._start_response(state, option.get("additional")))
        
        # 触发消息发送完成事件/hook
        await self.plugin_manager.trigger("on_message_after_sended", "before", state=state)
        try:
            await self.gateway_client.emit("on_message_after_sended", {
                "state": state.to_dict()
            })
        except Exception as ex:
            logger.error(f"gateway exception: {ex}", exc_info=ex)
        await self.plugin_manager.trigger("on_message_after_sended", "after", state=state)
