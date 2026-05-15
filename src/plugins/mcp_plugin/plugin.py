import pathlib
import tomllib
from typing import TYPE_CHECKING

from mcp.types import Tool
from openai.types.chat import ChatCompletionChunk, ChatCompletion

from .mcp.types import MCPOption
from .mcp.mcp_manager import MCPManager
from .mcp_handler.handler import Handler
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry
from src.core.logger.logger import LogCreator
from src.components.ipc.ipc import IPCServer
from src.components.llm.message_state import MessageState
from src.core import app_context

if TYPE_CHECKING:
    from src.application import Application

logger = LogCreator.instance.create(__name__)
class MCPPlugin(Plugin):
    app: "Application"
    ipc: IPCServer
    handler: Handler
    def __init__(self):
        super().__init__()
        self.manager = MCPManager(app_context.fixed_config["system_info"])
        self.handler = Handler(self.manager)
        self.activated_mcp_servers = []
        self.llm_reply_text = ""
    
    @staticmethod
    def read_mcp_config(path: pathlib.Path) -> dict[str, MCPOption]:
        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except FileNotFoundError:
            logger.info("MCP config not found, creating...")
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
            return {}
        except tomllib.TOMLDecodeError:
            logger.error("MCP config is invalid, please check your config.")
            return {}
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {}
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState):
        # state.mcp_list = self.manager.mcp_servers
        tools: list[Tool] = []
        for mcp_name in self.activated_mcp_servers:
            mcp_info = self.manager.mcp_infos.get(mcp_name)
            if mcp_info is None:
                continue
            tools.extend([
                Tool(
                    name=f"{mcp_name}.{tool.name}",
                    description=tool.description,
                    inputSchema=tool.inputSchema
                )
                for tool in mcp_info['tools']
            ])
        state.tools = tools
    
    @registry.on_ready()
    async def on_ready(self, app: "Application"):
        self.app = app
        self.ipc = app.ipc_server

        config_path = pathlib.Path(app_context.data_home) / "mcp_config.toml"
        try:
            config: dict[str, MCPOption] = self.read_mcp_config(config_path)
            self.manager.load(config)
            await self.manager.activate("WebSearch")
            self.activated_mcp_servers = ["WebSearch"]
            self.handler.init(self.ipc)
            logger.info("mcp 处理方法初始化成功")
        except Exception as e:
            logger.error(f"加载MCP配置失败: {e}")
    
    @registry.on_llm_response()
    def on_llm_response(self, chat_completion):
        if isinstance(chat_completion, Exception):
            return
    
    def emit(self, name: str, arguments: dict):
        # 不要在这里调用mcp，通过插件管理器，得到本插件实例，然后通过manager访问调用（其实是偷懒）
        ...
