from abc import ABC, abstractmethod
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

class Message(ABC, BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    @abstractmethod
    def get_message(self) -> ChatCompletionMessageParam:
        ...
