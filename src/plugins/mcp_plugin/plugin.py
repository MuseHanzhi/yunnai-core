import pathlib
import tomllib
import asyncio
import json

from mcp.types import Tool
from openai.types.chat import ChatCompletionChunk, ChatCompletion

from src.plugins.plugin import Plugin
from src.components.ipc_com.ipc import IPC
# from src.components.gateway.gateway_client import GatewayClient
from src.plugins.hook_registry import registry
from src.core.logger.logger import LogCreator
from src.components.llm.message_state import MessageState
from src.plugins.mcp_plugin import ipc_handlers
from src.core import app_context

from .mcp.types import MCPOption
from .mcp.mcp_manager import MCPManager
from typing import Any

logger = LogCreator.instance.create(__name__)
class MCPPlugin(Plugin):
    
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.mcp_manager = MCPManager({
            "name": app_context.fixed_config.system_info.name,
            "version": app_context.fixed_config.system_info.version
        })
    
    def _read_config(self) -> dict[str, MCPOption]:
        mcp_config_path = self.config_home_path / "mcp_config.toml"
        if not mcp_config_path.exists():
            from .config_templates.mcp_config import content
            logger.info(f"配置文件'{mcp_config_path.absolute()}'不存在，已创建空的配置文件")
            mcp_config_path.write_text(content, encoding="utf-8")
            return {}
        config_content: str
        try:
            config_content = mcp_config_path.read_text("utf-8")
        except UnicodeEncodeError:
            try:
                config_content = mcp_config_path.read_text("gbk")
            except:
                logger.error("config file encoding error")
                return {}
        
        try:
            return tomllib.loads(config_content)
        except Exception as ex:
            logger.error("prase configure failed", exc_info=ex)
            return {}
    
    @registry.on_ready()
    async def on_ready(self):
        try:
            config = self._read_config()
            await self.mcp_manager.load(config)
            logger.info("mcp load success")
        except Exception as ex:
            logger.error("mcp load exception", exc_info=ex)
            return
        
        if self.application.ipc is not None:
            ipc_handlers.setup(self.application.ipc, self.mcp_manager)
            logger.info("mcp ipc setup success")

    
    @registry.on_message_before_send()
    async def on_message_before_send(self, state: MessageState, additional: dict):
        state.data.tools = self.mcp_manager.get_tools()
