import pathlib
import tomllib
from typing import TYPE_CHECKING

from .mcp.types import MCPOption
from .mcp.mcp_manager import MCPManager
from .mcp_handler.handler import Handler
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry
from src.core.logger.logger import LogCreator
from src.components.ipc.ipc import IPCServer
from src.components.llm.message_state import MessageState

if TYPE_CHECKING:
    from src.application import Application

logger = LogCreator.instance.create(__name__)
class MCPPlugin(Plugin):
    app: "Application"
    ipc: IPCServer
    handler: Handler
    def __init__(self):
        super().__init__()
        self.manager = MCPManager({
            "name": "yunnai-core",
            "version": "1.0.0"
        })
        self.handler = Handler(self.manager)
    
    @staticmethod
    def read_mcp_config(path: pathlib.Path) -> dict[str, MCPOption]:
        path.parent.mkdir(parents=True, exist_ok=True)
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
        state.mcp_list = self.manager.mcp_servers

    @registry.on_app_initialize()
    def on_app_initialize(self, app: "Application"):
        self.app = app
        self.ipc = app.ipc_server

        config_path = pathlib.Path(__file__).parent / "mcp_config.toml"
        try:
            config: dict[str, MCPOption] = self.read_mcp_config(config_path)
            self.manager.load(config)
        except Exception as e:
            logger.error(f"加载MCP配置失败: {e}")
    
    @registry.on_ready()
    def on_ready(self):
        # self.ipc.invoke()
        self.handler.init(self.ipc)
        logger.info("mcp 处理方法初始化成功")
    
    def emit(self, name: str, arguments: dict):
        # 不要在这里调用mcp，通过插件管理器，得到本插件实例，然后通过manager访问调用（其实是偷懒）
        ...
