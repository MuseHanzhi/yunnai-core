from openai.types.chat import ChatCompletionMessageParam
from typing import Any, Literal
from .types import *

class MessageState:
    def __init__(self, model_name, input: str, type: Literal["user", "tool"] = "user", messages: list[ChatCompletionMessageParam] | None = None, is_stream: bool = True):
        self.messages = messages if messages else []
        self.model_name = model_name
        self.is_stream = is_stream
        self.extra_body: dict[str, Any] = {}
        self.canceled = False
        self.dyn_prompt = ""
        self.top_prompt = ""
        self.input = input
        self.mcp_list: list[dict] = []
        self.skills: list[dict[str, str]] = []
        self.type: Literal["user", "tool"] = type
        self.resources: list[ResourceOptions] = []
    
    def set_mcp_list(self, mcp_list: list[dict]):
        self.mcp_list = mcp_list
    
    def to_dict(self) -> dict:
        return {
            "messages": self.messages,
            "model_name": self.model_name,
            "is_stream": self.is_stream,
            "extra_body": self.extra_body,
            "canceled": self.canceled,
            "dyn_prompt": self.dyn_prompt,
            "top_prompt": self.top_prompt,
            "input": self.input,
            "mcp_list": self.mcp_list,
            "skills": self.skills,
            "type": self.type,
            "resources": self.resources
        }
    
    def change_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Invalid key: {key}")

    def cancel(self):
        self.canceled = True

    def append_dyn(self, content: str):
        prompt = content if content.endswith("\n") else content + "\n"
        self.dyn_prompt += prompt
    
    def set_extra_body(self, key: str, value: Any):
        self.extra_body[key] = value
