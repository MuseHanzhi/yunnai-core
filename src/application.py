from concurrent.futures import ThreadPoolExecutor
import asyncio
import time
import sys
import os

from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk
)

from src.components.llm.client import Client as LLMClient, MessageState
from src.components.plugin_manager.plugin_manager import PluginManager
from src.core.logger.logger import LogCreator
from src.components.ipc.ipc import IPCServer
from src.ipc_handlers.ipc_handler import IPCHandler
from src.core import app_context

from src.types.send_message_options import SendMessageOptions

logger = LogCreator.instance.create(__name__)
class Application:
    """
    **核心类**

    - 异步事件循环  : 完成度(100%)
    - 触发插件Hooks : 完成度(100%)
    - LLM       : 完成度(100%)
    - 插件管理  : 完成度(100%) 
    """
    def __init__(self):
        # 基础
        self.thread_executor = ThreadPoolExecutor(app_context.app_config["system"]["thread_workers"])
        self.event_loop = asyncio.new_event_loop()
        
        # 组件
        self.plugin_manager = PluginManager()
        self.llm_client: LLMClient = LLMClient()
        self.ipc_server: IPCServer = self._setup_ipc()
        
        # 全局变量
        self.completed_text = ""
    
    def on_ipc_ready(self):
        self.plugin_manager.trigger("on_ready", "before")
        self.plugin_manager.trigger("on_ready", "after")
        if self.ipc_server.is_connected:
            logger.info(f"connect ipc -> {self.ipc_server.ipc_uri}")
            handler = IPCHandler(self, self.ipc_server)
            handler.init()

    def on_ipc_error(self, error: Exception):
        logger.error(f"IPC服务启动异常: {error}", exc_info=error)
        sys.exit(1)
    
    def _setup_ipc(self) -> IPCServer :
        launch_ipc_uri = app_context.launch_args.get("ipc_uri")
        ipc_config = app_context.app_config["system"].get("ipc")
            
        uri = launch_ipc_uri if launch_ipc_uri else ipc_config.get("uri")
        if not uri:
            return IPCServer(uri, self.event_loop)
        
        ipc_server = IPCServer(uri, self.event_loop)
        ipc_server.on_ipc_ready = self.on_ipc_ready
        ipc_server.on_ipc_error = self.on_ipc_error

        if launch_ipc_uri is None and not ipc_config.get("enable", False):
            return ipc_server
        self.event_loop.create_task(ipc_server.start())     # 需要等run_forever启动后才能工作
        return ipc_server
    
    def exit(self):
        if self.ipc_server.is_connected:
            self.event_loop.run_until_complete(self.ipc_server.emit("on_app_will_close"))
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
        
        default_llm = app_context.launch_args["default_llm"]
        if default_llm is None:
            default_llm = app_context.app_config["llm"]["default"]
        models = app_context.app_config["llm"]["models"]
        llm_config = models.get(default_llm)

        logger.info(f"use llm: {default_llm}")
        if llm_config is None:
            raise Exception(f"llm model {default_llm} not found")
        
        llm_api_key = os.getenv(llm_config["key_name"])
        if llm_api_key is None:
            raise Exception(f"请配置{llm_config['key_name']}环境变量")

        self.llm_client.setup_client({
            "api_key": llm_api_key,
            "base_url": llm_config["base_url"]
        }, llm_config.get("extra_body", {}))

        logger.info("setup llm client ok")

    def initialize(self):
        logger.info("application initialize")
        app_context.event_loop = self.event_loop
        
        self._setup_llm()

        # 异步事件循环
        asyncio.set_event_loop(self.event_loop)
        
        logger.info("setup plugin manager")
        self.plugin_manager.initialize(app_context.app_config["plugin_config"])
        logger.info("setup plugin manager ok")

        self.plugin_manager.trigger(
            "on_app_before_initialize",
            "before",
            app = self
            )
        self.plugin_manager.trigger(
            "on_app_before_initialize",
            "after",
            app = self
            )

        # 触发插件对应时机
        self.plugin_manager.trigger(
            "on_app_after_initialized",
            "before"
            )
        self.plugin_manager.trigger(
            "on_app_after_initialized",
            "after"
            )
        logger.info("app initialized")
    
    async def _start_response(self, state: MessageState, ipc_request_id: str | None = None):
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
                    self.plugin_manager.trigger(
                        "on_llm_response",
                        "before",
                        chat_completion = chunk
                    )
                    if self.ipc_server.is_connected:
                        await self.ipc_server.emit(
                            "llm_response",
                            chat_completion = chunk.model_dump(),
                            request_id = ipc_request_id
                        )
                    self.plugin_manager.trigger(
                        "on_llm_response",
                        "after",
                        chat_completion = chunk
                    )
            else:
                # 非流式响应
                completion: ChatCompletion = await self.llm_client.non_stream_response(state)
                logger.info(f"llm non_stream response start: {(time.time() * 1000) - start_ms}ms")
                self.plugin_manager.trigger(
                    "on_llm_response",
                    "before",
                    chat_completion = completion
                )
                if self.ipc_server.is_connected:
                    await self.ipc_server.emit(
                        "llm_response",
                        chat_completion = completion.model_dump(),
                            request_id = ipc_request_id
                    )
                self.plugin_manager.trigger(
                    "on_llm_response",
                    "after",
                    chat_completion = completion
                )
            logger.info("llm response end")
        except Exception as ex:
            logger.info(f"llm response exception: {ex}", exc_info=ex)
    
    async def send_message(self, message: str, option: SendMessageOptions):
        logger.info(f"start handle message: {message}")
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        state = self.llm_client.create_state(option["model_name"], message, option.get("stream", True))
        
        # 触发发送消息前事件/hook
        self.plugin_manager.trigger("on_message_before_send", "before", state=state)
        if self.ipc_server.is_connected:
            result_state = await self.ipc_server.invoke(
                "on_message_before_send",
                state = state.to_dict(),
                request_id = option.get("request_id")
            )
            new_state = result_state.get('state')
            if new_state is not None:
                state.change_from_dict(new_state)
        self.plugin_manager.trigger("on_message_before_send", "after", state=state)

        # 检查是否被取消
        if state.canceled:
            return
        
        # 开始响应任务
        self.event_loop.create_task(self._start_response(state, option.get("request_id")))
        
        # 触发消息发送完成事件/hook
        self.plugin_manager.trigger("on_message_after_sended", "before", state=state)
        if self.ipc_server.is_connected:
            await self.ipc_server.emit(
                "on_message_after_sended",
                state = state.to_dict(),
                request_id = option.get("request_id")
            )
        self.plugin_manager.trigger("on_message_after_sended", "after", state=state)

    def run(self):
        try:
            if not self.ipc_server.is_connected:
                self.plugin_manager.trigger("on_ready", "before")
                self.plugin_manager.trigger("on_ready", "after")
            logger.info("start event loop")
            self.event_loop.run_forever()
        except KeyboardInterrupt:
            logger.info("keyboard interrupt detected, exiting...")
            self.exit()
            return 0
        except Exception as e:
            logger.error(f"running exception: {e}")
            return 1
        try:
            self.plugin_manager.trigger("on_app_will_close", "before",)
            self.plugin_manager.trigger("on_app_will_close", "after",)
            return 0
        except Exception as err:
            logger.error(f"running exception: {err}")
            return 1
