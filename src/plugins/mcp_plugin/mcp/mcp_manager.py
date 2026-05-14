from typing import Any, Union
import asyncio

from .mcp_client import MCPClient
from .types import MCPOption
from src.core.logger.logger import LogCreator

from .types import *


logger = LogCreator().instance.create(__name__)
class MCPManager:
    def __init__(self, client_info: ClientInfo):
        self.client_info = client_info
        self.mcp_servers: list[dict[str, str]] = []
        self.mcp_infos: dict[str, MCPInfo] = {}

    def is_activate(self, mcp_name: str):
        mcp_info = self.mcp_infos.get(mcp_name)
        if not mcp_info:
            return False
        return mcp_info["session"] is not None

    def push(self, name: str, mcp: MCPOption):
        self.mcp_infos[name] = {
            "name": name,
            "client": MCPClient(self.client_info, mcp),
            "session": None,
            "tools": []
        }
        self.mcp_servers.append({
            "name": name,
            "desc": mcp["desc"]
        })
        logger.info(f"新增MCP: {name}")

    def load(self, servers: dict[str, Union[MCPStreamableHTTPOption, MCPStdioOption]]):
        for mcp_name in servers if servers else []:
            if servers is None or not servers[mcp_name].get("enable"):
                continue
            mcp_server = servers[mcp_name]
            self.mcp_infos[mcp_name] = {
                "name": mcp_name,
                "session": None,
                "client": MCPClient(self.client_info, mcp_server),
                "tools": []
            }
            self.mcp_servers.append({
                "name": mcp_name,
                "desc": mcp_server["desc"]
            })
            logger.info(f"'{mcp_name}'加载完成")
    
    async def activate(self, mcp_name: str) -> GetToolResult:
        """
        激活MCP，激活成功后返回该MCP的工具列表
        """
        if mcp_name not in self.mcp_infos:
            raise ValueError(f"MCP Server '{mcp_name}'不存在或者未开启")
        
        mcp_info = self.mcp_infos[mcp_name]
        client = mcp_info["client"]
        session = mcp_info.get("session")

        if session:
            return {
                "message": "OK",
                "is_error": False,
                "tools": mcp_info["tools"]
            }

        event_loop = asyncio.get_running_loop()
        future = asyncio.Future()

        def on_connected():
            future.set_result(None)
            client.on_connect_error = None
            client.on_connected = None
        
        def on_connect_error(ex: Exception):
            future.set_exception(ex)
            client.on_connect_error = None
            client.on_connected = None

        client.on_connected = on_connected
        client.on_connect_error = on_connect_error
        event_loop.create_task(client.connect())
        try:
            await future
        except Exception as ex:
            raise ex
        session = client.get_session()
        self.mcp_infos[mcp_name]["session"] = session
        tools = (await session.list_tools()).tools
        mcp_info["tools"] = tools
        return {
            "message": "OK",
            "is_error": False,
            "tools": tools
        }
    
    def deactivate(self, mcp_name: str):
        mcp_info = self.mcp_infos[mcp_name]
        mcp_info["client"].disconnect()
    
    async def call_tool(self, mcp_name: str, tool_name: str, arguments: dict[str, Any] | None = None) -> CallResult:
        logger.info(f"调用MCP '{mcp_name}' 工具 '{tool_name}' 参数 '{arguments}'")
        session = self.mcp_infos[mcp_name]["session"]
        if not session:
            return {
                "message": f"MCP '{mcp_name}' 未激活",
                "is_error": True,
                "content": None
            }
        try:
            call_result = await session.call_tool(tool_name, arguments)
            logger.info(f"调用MCP '{mcp_name}' 工具 '{tool_name}' 结果 '{ 'ERROR' if call_result.isError else 'OK' }'")
            result_text = ""
            for line in call_result.content:
                if line.type == "text":
                    result_text += line.text
            return {
                "message": "OK",
                "is_error": call_result.isError,
                "content": result_text
            }
        except Exception as ex:
            logger.error(f"调用MCP '{mcp_name}' 错误: {ex}", exc_info=ex)
            return {
                "message": str(ex),
                "is_error": True,
                "content": None
            }

    def get_mcp_session(self, mcp_name: str):
        session = self.mcp_infos[mcp_name]["session"]
        if not session:
            raise ConnectionError(f"MCP '{mcp_name}' 未激活")
        return session
