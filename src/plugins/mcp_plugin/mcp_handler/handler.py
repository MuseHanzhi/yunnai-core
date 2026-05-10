from mcp.types import PaginatedRequestParams, Tool

from ..mcp.mcp_manager import MCPManager

from src.core import LogCreator
from src.components.ipc.ipc import IPCServer

from .types import *
from src.ipc_handlers.types import IPCInvokeResult

from typing import (
    Any
)

logger = LogCreator.instance.create(__name__)

class Handler:
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager
    

    def init(self, ipc: IPCServer):
        ipc.handle("activate-mcp", self.activate_mcp)
        ipc.handle("call-tool", self.call_tool)
        ipc.handle("deactivate-mcp", self.deactivate_mcp)

        ipc.handle("get-mcp-list", self.get_mcp_list)
        ipc.handle("get-tools", self.get_tools)

        ipc.handle("get-all-tools", self.get_all_tools)
        ipc.handle("list-resources", self.list_resources)

    # def load(self, params: dict) -> IPCInvokeResult:
    #     mcp_list: MCPOption | None = params.get("mcp_list", None)
    #     client_info: SysInfo | None = params.get("client_info", None)
    #     if mcp_list is None or client_info is None:
    #         return {
    #             "success": False,
    #             "message": "Invalid parameters"
    #         }
    #     try:
    #         self.mcp_manager.load(mcp_list, client_info)
    #         return {
    #             "success": True,
    #             "message": "MCP activated"
    #         }
    #     except Exception as e:
    #         return {
    #             "success": False,
    #             "message": str(e)
    #         }


    async def activate_mcp(self, params: Any) -> IPCInvokeResult:
        argument: ActivateMCPHandlerParams = params
        logger.info(f"Activating MCP: {argument['mcp_name']}")
        try:
            result = await self.mcp_manager.activate(argument["mcp_name"])
            logger.info(f"Activate MCP: {argument['mcp_name']} Success, discovered {len(result['tools'])} tools")
            return {
                "data": result["tools"],
                "message": result["message"],
                "success": not result["is_error"]
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    

    async def call_tool(self, params: Any) -> IPCInvokeResult:
        arguments: CallToolParams = params
        try:
            res = await self.mcp_manager.call_tool(arguments["mcp_name"], arguments["tool_name"], arguments["arguments"])
            print(res)
            return {
                "data": res["content"],
                "message": res["message"],
                "success": not res["is_error"]
            }
        except Exception as e:
            return {
                "data": None,
                "message": str(e),
                "success": False
            }

    def deactivate_mcp(self, params: Any) -> IPCInvokeResult:
        argument: ActivateMCPHandlerParams = params
        logger.info(f"Deactivate MCP: {params["mcp_name"]}")
        self.mcp_manager.deactivate(argument["mcp_name"])
        return {
            "message": f"MCP '{argument["mcp_name"]}' deactivated",
            "success": True
        }

    async def list_resources(self, params: Any) -> IPCInvokeResult:
        arguments: ResourcesParams = params
        try:
            session = self.mcp_manager.get_mcp_session(arguments["mcp_name"])
            return {
                "data": await session.list_resources(params=PaginatedRequestParams(cursor=arguments["cursor"])),
                "message": "Success",
                "success": True
            }
        except Exception as e:
            return {
                "message": str(e),
                "success": False
            }

    async def get_all_tools(self, params: Any) -> IPCInvokeResult:
        arguments: GetAllToolsParams = params
        tools: dict[str, list[Tool]] = {}
        for mcp_item in self.mcp_manager.mcp_servers:
            if not self.mcp_manager.is_activate(mcp_item["name"]) and arguments["auto_activate"]:
                tools[mcp_item["name"]] = (await self.mcp_manager.activate(mcp_item["name"]))["tools"]
                continue
            tools[mcp_item["name"]] = self.mcp_manager.mcp_infos[mcp_item["name"]]["tools"]
        return {
            "data": tools,
            "message": "success",
            "success": True
        }
    async def get_mcp_list(self, _) -> IPCInvokeResult:
        logger.info("Get MCP List")

        return {
            "data": self.mcp_manager.mcp_servers,
            "message": "success",
            "success": True
        }
    async def get_tools(self, params: Any) -> IPCInvokeResult:
        arguments: GetToolsParams = params

        logger.info(f"Get Tools: {arguments['mcp_name']}")
        if not self.mcp_manager.is_activate(arguments["mcp_name"]):
            if not arguments["auto_activate"]:      # 不自动激活
                raise Exception("MCP is not activated")
            return {
                "data": await self.mcp_manager.activate(arguments["mcp_name"]),
                "success": True,
                "message": "success"
            }

        # 激活后直接返回工具集
        return {
            "success": True,
            "message": "Success",
            "data": self.mcp_manager.mcp_infos[arguments["mcp_name"]]["tools"]
        }
    