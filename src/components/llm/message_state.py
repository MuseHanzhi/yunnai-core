from openai.types.chat import ChatCompletionMessageParam
from typing import Any
from .types import *
from .message.message import Message



class MessageState:
    def __init__(self, model_name: str, message: Message, messages: list[ChatCompletionMessageParam] | None = None, is_stream: bool = True):
        self.data: MessageStateData = MessageStateData(
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
    
    @property
    def is_stream(self) -> bool:
        return self.data.is_stream

    def update(self, dict_data: dict):
        self.data = MessageStateData.model_validate(dict_data)
    
    def to_dict(self):
        return self.data.model_dump()

    def set_output_schema(self, name: str, json_schema: dict, strict: bool = True):
        self.output_schema = OutputShema(name=name, json_schema=json_schema, strict=strict)

    def cancel(self):
        self.canceled = True

    def append_dyn(self, content: str):
        prompt = content if content.endswith("\n") else content + "\n"
        self.data.dyn_prompt += prompt
    
    def set_extra_body(self, key: str, value: Any):
        self.data.extra_body[key] = value
