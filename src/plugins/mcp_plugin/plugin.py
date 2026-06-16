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
            mcp_config_path.write_text(content)
            return {}
        config_content: str
        try:
            config_content = mcp_config_path.read_text("utf-8")
        except UnicodeEncodeError:
            try:
                config_content = mcp_config_path.read_text("gbk")
            except:
                logger.warning("配置文件使用了不支持的编码保存")
                return {}
        
        try:
            return tomllib.loads(config_content)
        except Exception as ex:
            logger.error("解析配置文件失败", exc_info=ex)
            return {}
    
    @registry.on_ready()
    async def on_ready(self):
        config = self._read_config()
        try:
            await self.mcp_manager.load(config)
        except Exception as ex:
            logger.error("mcp load exception", exc_info=ex)
    
    # @registry.on_message_before_send()
    async def on_message_before_send(self, state: MessageState, additional: dict | None):
        state.data.tools = self.mcp_manager.get_tools()
        
        if additional is None or "mcp" not in additional:
            return

        mcp: dict[str, Any] = additional["mcp"]
        type: str | None = mcp.get("type")
        name: str | None = mcp.get("name")
        if type == "call_tool" and name:
            mcp_server, tool_name = name.split(".")
            args = mcp.get("args")
            state.cancel(self.info.name, f"call tool '{name}'")
        print("")

