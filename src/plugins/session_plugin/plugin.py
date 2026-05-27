from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionChunk

class SessionPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.messages: list[ChatCompletionMessageParam] = []
        self.replying_text: str = ""
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state, additional):
        if state.data.messages:
            self.messages.append(*state.data.messages)
        state.data.messages = self.messages
    
    @registry.on_message_after_sended()
    def on_message_after_sended(self, state):
        self.messages.append(state.data.message.get_message())
    
    @registry.on_llm_response()
    def on_llm_response(self, chat_completion):
        if isinstance(chat_completion, Exception):
            return
        
        if not chat_completion.choices:
            return

        if isinstance(chat_completion, ChatCompletionChunk):
            self.replying_text += (chat_completion.choices[0].delta.content or "")
        else:
            self.replying_text = (chat_completion.choices[0].message.content or "")
        
        if chat_completion.choices[0].finish_reason == "stop":
            self.messages.append({
                "role": "assistant",
                "content": self.replying_text
            })
            self.replying_text = ""
