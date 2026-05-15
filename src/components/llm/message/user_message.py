from .message import Message
from openai.types.chat import ChatCompletionContentPartParam, ChatCompletionMessageParam
from pydantic import PrivateAttr

class UserMessage(Message):
    _resource: list[ChatCompletionContentPartParam] = PrivateAttr(default_factory=list)
    def __init__(self, content: str, resource: list[ChatCompletionContentPartParam] = [], **kwargs):
        super().__init__(content=content, **kwargs)
        self._resource: list[ChatCompletionContentPartParam] = resource if resource is not None else []

    @property
    def type(self) -> str:
        return "user"
    
    def add_image(self, *urls: str) -> "UserMessage":
        self._resource = self._resource + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": url
                    }
                }
                for url in urls
            ]
        return self

    def get_message(self) -> ChatCompletionMessageParam:
        return {
            "role": "user",
            "content": self._resource + [
                {
                    "type": "text",
                    "text": self.content
                }
            ]
        }

    def set_content(self, content: str) -> "UserMessage":
        super().set_content(content)
        return self