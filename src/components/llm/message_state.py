from openai.types.chat import ChatCompletionMessageParam
from typing import Any
from .types import *
from .message.message import Message
from .message.user_message import UserMessage
from .message.tool_message import ToolMessage
from mcp.types import Tool
from pydantic import BaseModel, Field, field_validator


class MessageState(BaseModel):
    is_stream: bool = True
    canceled: bool = False
    output_schema: OutputShema | None = None
    model_name: str
    message: Message
    messages: list[ChatCompletionMessageParam] = Field(default_factory=list)
    extra_body: dict[str, Any] = Field(default_factory=dict)
    dyn_prompt: str = ""
    top_prompt: str = ""
    mcp_list: list[MCPData] = Field(default_factory=list)
    skills: list[SkillData] = Field(default_factory=list)
    tools: list[Tool] = Field(default_factory=list)
    option: dict = Field(default_factory=dict)

    @field_validator('message', mode='before')
    @classmethod
    def validate_message(cls, v):
        """根据消息字典数据自动转换为对应的Message子类实例"""
        if isinstance(v, Message):
            return v
        
        if isinstance(v, dict):
            # 判断消息类型，默认创建UserMessage
            # 如果有tool_call_id字段，则是ToolMessage
            if 'id' in v or 'tool_call_id' in v:
                return ToolMessage.model_validate(v)
            else:
                # 处理content字段，可能是字符串或包含resource的字典
                if isinstance(v.get('content'), dict):
                    content_dict = v['content']
                    content_text = content_dict.get('text', '')
                    resource = content_dict.get('resource', [])
                    return UserMessage(content=content_text, resource=resource)
                else:
                    content = v.get('content', '')
                    return UserMessage(content=content)
        
        raise ValueError(f"无法解析的消息类型: {type(v)}")

    @classmethod
    def create(cls, model_name: str, message: Message, messages: list[ChatCompletionMessageParam] | None = None, is_stream: bool = True) -> "MessageState":
        return cls(
            is_stream=is_stream,
            canceled=False,
            output_schema=None,
            model_name=model_name,
            message=message,
            messages=messages if messages else [],
            extra_body={},
            dyn_prompt="",
            top_prompt="",
            mcp_list=[],
            skills=[],
            tools=[],
            option={}
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