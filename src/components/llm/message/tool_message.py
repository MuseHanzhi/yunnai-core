from .message import Message
from openai.types.chat import ChatCompletionMessageParam

class ToolMessage(Message):
    id: str
    content: str
    def __init__(self, id: str, content: str) -> None:
        super().__init__(
            id = id,
            content = content
        )
    
    def get_message(self) -> ChatCompletionMessageParam:
        return {
            "role": "tool",
            "tool_call_id": self.id,
            "content": self.content
        }

    
