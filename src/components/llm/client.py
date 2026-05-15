from typing import AsyncGenerator, Any

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from mcp.types import Tool

from .message.message import Message
from .message.user_message import UserMessage
from .message.tool_message import ToolMessage
from .message_state import MessageState
from .types import *

from pydantic import BaseModel
class User(BaseModel):
    username: str
    nickname: str

class Client:
    def __init__(self):
        self._client: AsyncOpenAI = AsyncOpenAI(
            api_key=""
        )
        self.default_extra_body: dict[str, Any] = {}
    
    def setup_client(self, credential: Credential, extra_body: dict[str, Any] = {}):
        self._client.api_key = credential["api_key"]
        self._client.base_url = credential["base_url"]
        self.default_extra_body = extra_body

    def _map_tools(self, tools: list[Tool]):
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "No description provided.",
                    "parameters": tool.inputSchema
                }
            }
            for tool in tools
        ]

    def _build_sys_prompt(self, top_prompt: str, dyn_prompt: str, mcp_list: list[MCPData], skill_list: list[SkillData]):
        mcp_prompt = ""
        skill_prompt = ""
        t_dyn_prompt = ""

        if mcp_list:
            mcp_prompt = f"# Support MCP Servers \n{ '\n'.join([f'{mcp["name"]}: {mcp["desc"]}' for mcp in mcp_list]) }\n"
        if skill_list:
            skill_prompt = f"# Available Agent Skills  \n{ '\n'.join([f'{skill["name"]}: {skill["desc"]}' for skill in skill_list if 'name' in skill and 'desc' in skill]) }\n"
        if dyn_prompt:
            t_dyn_prompt = dyn_prompt

        return f"""{top_prompt}
{t_dyn_prompt}
{mcp_prompt}
{skill_prompt}
"""

    def _build_params(self, state: MessageState):
        params = {
            "model": state.model_name,
            "stream": state.is_stream,
            "tools": self._map_tools(state.tools),
            "messages": [
                {
                    "role": "system",
                    "content": self._build_sys_prompt(state.top_prompt, state.dyn_prompt, state.mcp_list, state.skills)
                },
                *state.messages,
                state.message.get_message()
            ],
        }

        if state.output_schema is not None:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": state.output_schema.name,
                    "schema": state.output_schema.json_schema,
                    "strict": state.output_schema.strict
                }
            }
        
        if state.extra_body:
            params["extra_body"] = state.extra_body
        
        state.messages = params["messages"]
        return params

    def create_user_state(self, model_name: str, message: UserMessage, is_stream: bool = True):
        return self.create_state(model_name, message, is_stream)
    
    def create_tool_state(self, model_name: str, message: ToolMessage, is_stream: bool = True):
        return self.create_state(model_name, message, is_stream)
    
    def create_state(self, model_name: str, message: Message, is_stream: bool = True):
        state = MessageState(model_name, message=message, is_stream=is_stream)
        state.extra_body = self.default_extra_body
        return state

    async def non_stream_response(self, state: MessageState) -> ChatCompletion:
        if state.is_stream:
            raise ValueError("当前消息状态为流式响应，请使用'stream_response'方法")
        params = self._build_params(state)
        try:
            completion: ChatCompletion = await self._client.chat.completions.create(**params)
            return completion
        except:
            raise
    
    async def stream_response(self, state: MessageState) -> AsyncGenerator[Any, ChatCompletionChunk]:
        if not state.is_stream:
            raise ValueError("当前消息状态为非流式响应，请使用'non_stream_response'方法")
        params = self._build_params(state)
        try:
            completion = await self._client.chat.completions.create(**params)
            async for chunk in completion:
                yield chunk
        except:
            raise
