import asyncio
from typing import TYPE_CHECKING

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from src.components.llm.message_state import MessageState
from src.plugins import Plugin, registry

if TYPE_CHECKING:
    from src.application import Application

class CliPlugin(Plugin):
    app: "Application"
    event_loop: asyncio.AbstractEventLoop
    def __init__(self):
        super().__init__()
        self.llm_done_signal = asyncio.Event()
        self.replying = False
    
    @registry.on_app_before_initialize()
    def on_app_before_initialize(self, app: "Application"):
        self.app = app
        self.event_loop = app.event_loop
        self.running = True

    async def run(self):
        while self.running:
            try:
                await self.app.send_message(input("> "), {
                    "model_name": "qwen3.6-plus",
                    "stream": True
                })
                await self.llm_done_signal.wait()
                self.llm_done_signal.clear()
            except KeyboardInterrupt:
                self.app.exit()
                self.running = False
                print("Exiting...")
                break
            except Exception as e:
                print(e)

    @registry.on_ready()
    def on_ready(self):
        self.event_loop.create_task(self.run())
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState):
        state.top_prompt = """
你是一个智能助手
# 输出要求
<thinking>
这里输出思考过程
</thinking>
这里输出回复内容
"""
        # state.set_extra_body("enable_thinking", True)
    
    @registry.on_llm_response()
    def on_llm_response(self, chat_completion: ChatCompletionChunk | ChatCompletion):
        if not self.replying:
            print("思考中...")
            self.replying = True
        if len(chat_completion.choices) == 0:
            return
        if isinstance(chat_completion, ChatCompletionChunk):
            if chat_completion.choices[0].delta.content:
                print(chat_completion.choices[0].delta.content, end="")
        else:
            if chat_completion.choices[0].message.content:
                print(chat_completion.choices[0].message.content, end="")
        if chat_completion.choices[0].finish_reason == "stop":
            self.llm_done_signal.set()
            self.replying = False
            print("[LLM] Done")
            print()
    
    @registry.on_app_will_close()
    def on_app_will_close(self):
        self.running = False