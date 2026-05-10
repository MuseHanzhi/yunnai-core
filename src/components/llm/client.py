from typing import AsyncGenerator, Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from .message_state import MessageState
from .types import *

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
    
    def _build_last_message(self, state: MessageState):
        message = f"# User Question  \n{state.input}"
        if state.type == "tool":
            message = f"# Call Result  \n{state.input}"

        return {
            "role": "user",
            "content": [
                *state.resources,
                {
                    "type": "text",
                    "text": message
                },
                {
                    "type": "text",
                    "text": f"# Support MCP Servers \n{ '\n'.join([f'{mcp["name"]}: {mcp["desc"]}' for mcp in state.mcp_list]) }"
                },
                {
                    "type": "text",
                    "text": f"# Available Agent Skills  \n{ '\n'.join([f'{skill["name"]}: {skill["desc"]}' for skill in state.skills if 'name' in skill and 'desc' in skill]) }"
                },
                {
                    "type": "text",
                    "text": f"# Additional Information  \n{state.dyn_prompt}"
                }
            ]
        }

    def _build_params(self, state: MessageState):
        params = {
            "model": state.model_name,
            "stream": state.is_stream,
            "messages": [
                {
                    "role": "system",
                    "content": state.top_prompt
                },
                *state.messages
            ]
        }

        last_message = self._build_last_message(state)
        params["messages"].append(last_message)
        
        if state.extra_body:
            params["extra_body"] = state.extra_body
        
        state.messages = params["messages"]
        return params
    
    def create_state(self, model_name: str, input: str, is_stream: bool = True):
        state = MessageState(model_name, input=input, is_stream=is_stream)
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
        