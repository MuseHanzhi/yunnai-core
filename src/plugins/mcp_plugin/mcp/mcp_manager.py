import asyncio
from mcp.types import Tool, Resource, Prompt
from .mcp_client import MCPClient
from .types import *
from pydantic import BaseModel
from typing import Any

from src.core.logger import LogCreator

class MCPServerResources(BaseModel):
    tools: list[Tool]
    resources: list[Resource]
    prompts: list[Prompt]


logger = LogCreator.instance.create(__name__)
class MCPManager:
    def __init__(self, client_info: ClientInfo):
        self.servers: dict[str, MCPOption] = {}
        self.mcp_clients: dict[str, MCPClient] = {}
        self.client_info: ClientInfo = client_info
        self.resources: dict[str, MCPServerResources] = {}
        self._initialized: bool = False
    
    async def _activate_mcp(self, client: MCPClient):
        future = asyncio.Future()
        def on_connected():
            client.on_connect_error = lambda error: None
            client.on_connected = lambda: None
            if not future.done():
                future.set_result(None)
                
        def on_connect_error(error: Exception):
            client.on_connect_error = lambda error: None
            client.on_connected = lambda: None
            if not future.done():
                future.set_exception(error)
        client.on_connected = on_connected
        client.on_connect_error = on_connect_error
        asyncio.create_task(client.connect())
        
        try:
            await future
            return client.get_session()
        except Exception as e:
            logger.warning(f"activate failed: {e}")
            return None
    
    async def _setup_server(self, mcp_name: str, timeout: int = 20000):
        client = self.mcp_clients[mcp_name]
        session = client.get_session()
        
        tasks = []
        if client.tools:
            tasks.append(asyncio.wait_for(session.list_tools(), timeout))
        if client.resources:
            tasks.append(asyncio.wait_for(session.list_resources(), timeout))
        if client.prompts:
            tasks.append(asyncio.wait_for(session.list_prompts(), timeout))
        
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        tools = []
        resources = []
        prompts = []

        if client.tools:
            tool_results = results[0]
            if isinstance(tool_results, BaseException):
                logger.warning(f"Failed to obtain the list of '{mcp_name}' tools, error: {tool_results}")
            else:
                tools = tool_results.tools
                logger.info(f"[{mcp_name}]: {len(tools)} tools have been obtained")

        if client.resources:
            resource_results = results[1]
            if isinstance(resource_results, BaseException):
                logger.warning(f"Failed to obtain the list of '{mcp_name}' resources, error: {tool_results}")
            else:
                resources = resource_results.resources
                logger.info(f"[{mcp_name}]: {len(resources)} resources have been obtained")

        if client.prompts:
            prompt_results = results[2]
            if isinstance(prompt_results, BaseException):
                logger.warning(f"Failed to obtain the list of '{mcp_name}' prompts, error: {tool_results}")
            else:
                prompts = prompt_results.prompts
                logger.info(f"[{mcp_name}]: {len(prompts)} prompts have been obtained")
        
        self.resources[mcp_name] = MCPServerResources(
            tools=tools,
            resources=resources,
            prompts=prompts
        )
        
    
    
    def deactivate_mcp(self, mcp_name: str):
        client = self.mcp_clients.get(mcp_name)
        if client:
            del self.mcp_clients[mcp_name]
            client.disconnect()
        
        if mcp_name in self.resources:
            del self.resources[mcp_name]

    async def load(self, servers: dict[str, MCPOption]):
        new_servers: dict[str, MCPOption] = {}
        if self._initialized:
            # 需要跟更新或者删除的MCP Server
            will_unload = [mcp_name for mcp_name in self.servers if mcp_name not in servers or servers[mcp_name] != self.servers[mcp_name]]

            # 新的MCP Server
            new_servers = {mcp_name: servers[mcp_name] for mcp_name in servers if mcp_name not in self.servers}

            for mcp_name in will_unload:
                self.unload_server(mcp_name)
        else:
            new_servers = servers


        for mcp_name, mcp_option in new_servers.items():
            self.servers[mcp_name] = mcp_option

            client = MCPClient(self.client_info, mcp_option)
            self.mcp_clients[mcp_name] = client

            if not mcp_option.get("disabled", False):
                session = await self._activate_mcp(client)
                if session:
                    asyncio.create_task(self._setup_server(mcp_name))

        self._initialized = True
    
    def unload_server(self, mcp_name: str):
        self.deactivate_mcp(mcp_name)
        if mcp_name in self.servers:
            del self.servers[mcp_name]
    
    def unload(self):
        for mcp_name in self.servers.keys():
            self.unload_server(mcp_name)
    
    async def _try_get_session(self, mcp_name: str):
        if mcp_name not in self.servers or mcp_name not in self.mcp_clients:
            raise ValueError("MCP not found")
        
        client = self.mcp_clients[mcp_name]
        try:
            return client.get_session()
        except ConnectionError:
            try:
                await self._activate_mcp(client)
                return client.get_session()
            except Exception as e:
                raise e
        except Exception as e:
            raise e
    
    def get_tools(self, mcp_name: str | None = None) -> list[Tool]:
        if mcp_name:
            return [
                Tool(
                    name=f"{mcp_name}.{tool.name}",
                    description=tool.description,
                    inputSchema=tool.inputSchema,
                    icons=tool.icons,
                    annotations=tool.annotations
                    )
                for tool in self.resources[mcp_name].tools
            ]
        tools: list[Tool] = []
        for mcp, resource in self.resources.items():
            tools.extend([
                Tool(
                    name=f"{mcp}.{tool.name}",
                    description=tool.description,
                    inputSchema=tool.inputSchema,
                    icons=tool.icons,
                    annotations=tool.annotations)
                    for tool in resource.tools])
        return tools
    
    def get_resources(self, mcp_name: str | None = None):
        if mcp_name:
            return [
                Resource(
                    name=f"{mcp_name}.{resource.name}",
                    uri=resource.uri,
                    description=resource.description,
                    mimeType=resource.mimeType,
                    size=resource.size,
                    icons=resource.icons,
                    annotations=resource.annotations)
                    for resource in self.resources[mcp_name].resources
            ]
        
        resources: list[Resource] = []
        for mcp, resource in self.resources.items():
            resources.extend([Resource(name=f"{mcp}.{resource.name}",
                                       uri=resource.uri,
                                       description=resource.description,
                                       mimeType=resource.mimeType,
                                       size=resource.size,
                                       icons=resource.icons,
                                       annotations=resource.annotations)
                                       for resource in resource.resources])
        return resources
    
    def get_prompts(self, mcp_name: str | None = None):
        if mcp_name:
            return [
                Prompt(
                    name=f"{mcp_name}.{prompt.name}",
                    description=prompt.description,
                    arguments=prompt.arguments,
                    icons=prompt.icons)
                    for prompt in self.resources[mcp_name].prompts
            ]
        
        resources: list[Prompt] = []
        for mcp, resource in self.resources.items():
            resources.extend([Prompt(
                name=f"{mcp}.{prompt.name}",
                description=prompt.description,
                arguments=prompt.arguments,
                icons=prompt.icons)
                for prompt in resource.prompts])
        return resources
    
    async def call_tool(self, mcp_name: str, tool_name: str, args: dict[str, Any]):
        session = await self._try_get_session(mcp_name)
        return await session.call_tool(tool_name, args)
    
    async def get_session(self, mcp_name: str):
        try:
            return await self._try_get_session(mcp_name)
        except:
            raise
