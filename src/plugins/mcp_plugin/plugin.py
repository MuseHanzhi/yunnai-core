import pathlib
import tomllib
import asyncio
import json

from mcp.types import Tool
from openai.types.chat import ChatCompletionChunk, ChatCompletion

from src.plugins.plugin import Plugin
from src.components.gateway.gateway_client import GatewayClient
from src.plugins.hook_registry import registry
from src.core.logger.logger import LogCreator
from src.components.llm.message_state import MessageState
from src.core import app_context

from .mcp.types import MCPOption
from .mcp.mcp_manager import MCPManager
from .mcp_handler.handler import Handler

logger = LogCreator.instance.create(__name__)
class MCPPlugin(Plugin):
    ipc: GatewayClient
    handler: Handler
    def __init__(self):
        super().__init__()
        self.manager = MCPManager({
            "name": app_context.fixed_config.system_info.name,
            "version": app_context.fixed_config.system_info.version
        })
        self.handler = Handler(self.manager)
        self.activated_mcp_servers = ["z-image", "WebSearch"]
        self.tool: dict[str, str] = {}
        self.running = False
        self.signal = asyncio.Event()
    
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
    def on_message_before_send(self, state: MessageState, additional: dict | None):
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
        state.data.tools = tools

        if self.tool:
            state.data.messages.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": self.tool["id"],
                        "type": "function",
                        "function": {
                            "name": self.tool["name"],
                            "arguments": self.tool["args"]
                        },
                        "type": "function"
                    }
                ]
            })
            self.tool = {}
    
    async def tool_caller(self):
        logger.info("等待工具调用...")
        while self.running:
            self.signal.clear()
            await self.signal.wait()
            if not self.tool:
                continue
            mcp_name, tool_name = self.tool["name"].split(".")
            call_id = self.tool["id"]
            args = self.tool["args"]
            logger.info(f"id: {call_id} 调用工具 '{mcp_name}.{tool_name}'")
            result = await self.manager.call_tool(mcp_name, tool_name, json.loads(args))
            if result["is_error"]:
                logger.error(f"id: {call_id} 调用工具 '{mcp_name}.{tool_name}' 失败: {result["message"]}")
            else:
                content = result["content"]
                if not isinstance(content, str):
                    content = json.dumps(content)
                await self.application.send_message(content, {
                    "tool_call_id": call_id,
                    "type": "tool",
                    "model_name": "qwen3.6-plus",
                })
            
    
    @registry.on_ready()
    async def on_ready(self):
        self.ipc = self.application.gateway_client
        config_path = pathlib.Path(app_context.data_home) / "mcp_config.toml"
        try:
            config: dict[str, MCPOption] = self.read_mcp_config(config_path)
            self.manager.load(config)
            for mcp_server_infos in self.manager.mcp_servers:
                mcp_name = mcp_server_infos["name"]
                await self.manager.activate(mcp_name)
                self.activated_mcp_servers.append(mcp_name)
            self.handler.init(self.ipc)
            logger.info("mcp 处理方法初始化成功")
            self.running = True
            app_context.event_loop.create_task(self.tool_caller())
        except Exception as e:
            logger.error(f"加载MCP配置失败: {e}")
        
    
    @registry.on_llm_response()
    def on_llm_response(self, chat_completion):
        if isinstance(chat_completion, Exception) or not chat_completion.choices:
            return

        if isinstance(chat_completion, ChatCompletionChunk):
            if chat_completion.choices[0].delta.tool_calls:
                tool = chat_completion.choices[0].delta.tool_calls[0]
                if tool.id:
                    self.tool.setdefault("id", "")
                    self.tool['id'] += (tool.id or "")
                if tool.function:
                    self.tool.setdefault("name", "")
                    self.tool['name'] += (tool.function.name or "")
                    self.tool.setdefault("args", "")
                    self.tool['args'] += (tool.function.arguments or "")
        elif isinstance(chat_completion, ChatCompletion):
            if chat_completion.choices[0].message.tool_calls:
                tool = chat_completion.choices[0].message.tool_calls[0]
                function = tool.function # type: ignore
                self.tool["id"] = tool.id
                self.tool["name"] = function.name
                self.tool["args"] = function.arguments
    
        if chat_completion.choices[0].finish_reason == "tool_calls":
            self.signal.set()

    def emit(self, name: str, arguments: dict):
        # 不要在这里调用mcp，通过插件管理器，得到本插件实例，然后通过manager访问调用（其实是偷懒）
        ...
    
    def deinit(self):
        self.running = False
        self.signal.set()

    @registry.on_app_will_close()
    def on_app_will_close(self):
        self.deinit()
