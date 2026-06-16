from .message.message import Message
from .message.user_message import UserMessage
from .message.tool_message import ToolMessage

from mcp.types import Tool
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import (
    TypedDict,
    Required,
    Literal,
    Union,
    Any
)

class Credential(TypedDict):
    api_key: Required[str]
    base_url: Required[str]

class ImageResourceOptions(TypedDict):
    type: Literal["image"]
    image_url: str

class AudioResourceOptions(TypedDict):
    type: Literal["audio"]
    input_audio: str

class FileResourceOptions(TypedDict):
    type: Literal["file"]
    file: str

class TextResourceOptions(TypedDict):
    type: Literal["text"]
    text: str

ResourceOptions = Union[ImageResourceOptions, AudioResourceOptions, FileResourceOptions, TextResourceOptions]


# MCP
class MCPData(TypedDict):
    name: str
    desc: str

# Skill
class SkillData(TypedDict):
    name: str
    desc: str

class OutputShema(BaseModel):
    name: str
    json_schema: dict
    strict: bool

class MessageStateData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    is_stream: bool = True
    canceled: bool = Field(default_factory=lambda: False)
    canceller: str | None = Field(default_factory=lambda: None)
    cancel_reason: str | None = Field(default_factory=lambda: None)
    output_schema: OutputShema | None = Field(default_factory=lambda: None)
    model_name: str
    message: Message
    messages: list[ChatCompletionMessageParam] = Field(default_factory=list)
    extra_body: dict[str, Any] = Field(default_factory=dict)
    dyn_prompt: str = Field(default_factory=lambda: "")
    top_prompt: str = Field(default_factory=lambda: "")
    mcp_list: list[MCPData] = Field(default_factory=list)
    skills: list[SkillData] = Field(default_factory=list)
    tools: list[Tool] = Field(default_factory=list)
    option: dict = Field(default_factory=dict)
    function_calls: list[ChatCompletionToolParam] = Field(default_factory=list)

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
