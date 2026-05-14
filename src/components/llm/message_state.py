from openai.types.chat import ChatCompletionMessageParam
from typing import Any
from .types import *
from .message.message import Message
from mcp.types import Tool
from pydantic import BaseModel

class MessageState(BaseModel):
    is_stream: bool
    canceled: bool = False

    output_schema: OutputShema | None
    model_name: str
    message: Message
    messages: list[ChatCompletionMessageParam]
    extra_body: dict[str, Any]
    dyn_prompt: str
    top_prompt: str
    mcp_list: list[MCPData]
    skills: list[SkillData]
    tools: list[Tool]


    def __init__(self, model_name, message: Message, messages: list[ChatCompletionMessageParam] | None = None, is_stream: bool = True):
        super().__init__(
            is_stream=is_stream,
            cancel=False,
            output_schema=None,
            model_name=model_name,
            message=message,
            messages=messages if messages else [],
            extra_body={},
            dyn_prompt="",
            top_prompt="",
            mcp_list=[],
            skills=[],
            tools=[]
        )

    def set_output_schema(self, name: str, json_schema: dict, strict: bool = True):
        self.output_schema = OutputShema(name=name, json_schema=json_schema, strict=strict)

    def cancel(self):
        self.canceled = True

    def append_dyn(self, content: str):
        prompt = content if content.endswith("\n") else content + "\n"
        self.dyn_prompt += prompt
    
    def set_extra_body(self, key: str, value: Any):
        self.extra_body[key] = value
