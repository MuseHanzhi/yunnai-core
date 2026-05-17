import asyncio
from typing import TYPE_CHECKING, TypedDict, Literal

from openai.types.chat import ChatCompletion, ChatCompletionChunk
import json

from src.components.llm.message_state import MessageState
from src.plugins import Plugin, registry
from src.plugins.mcp_plugin.plugin import MCPPlugin

if TYPE_CHECKING:
    from src.application import Application

class CliPlugin(Plugin):
    app: "Application"
    event_loop: asyncio.AbstractEventLoop
    def __init__(self):
        super().__init__()
        self.enable = False
        self.llm_done_signal = asyncio.Event()
        self.replying = False
        

    async def run(self):
        # 初始化时确保信号是关闭的
        self.llm_done_signal.clear()
        
        while self.running:
            try:
                # 1. 等待用户输入
                user_input = input("> ")
                
                # 2. 【关键优化】在发起新请求前，再次确保信号是关闭的
                # 这样可以防止上一轮极快的响应“污染”这一轮的等待
                self.llm_done_signal.clear()
                self.replying = False # 重置回复状态
                
                # 3. 发送消息（触发流式回调）
                await self.app.send_message(user_input, {
                    "model_name": "qwen3.6-plus",
                    "stream": True
                })
                
                # 4. 安心等待大模型输出完毕
                await self.llm_done_signal.wait()
                
            except KeyboardInterrupt:
                self.app.exit()
                self.running = False
                print("\nExiting...")
                break
            except Exception as e:
                print(f"发生错误: {e}")
                # 发生异常时也要记得清除信号，防止影响下一轮
                self.llm_done_signal.clear()
                self.replying = False

    @registry.on_ready()
    def on_ready(self, app: "Application"):
        self.app = app
        self.event_loop = app.event_loop
        self.running = True
        self.event_loop.create_task(self.run())
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState):
        # 检查是否有可用工具
        # state.is_stream = False   
        state.top_prompt = """
你叫云乃，是一个智能助手

# 绝对指令
1. **不要**输出任何Markdown格式，使用纯文本输出

"""     
    
    @registry.on_llm_response()
    async def on_llm_response(self, chat_completion: ChatCompletionChunk | ChatCompletion | Exception):
        if isinstance(chat_completion, Exception):
            print(f"[LLM] Error: {chat_completion}")
            self.llm_done_signal.set()
            return

        if not self.replying:
            print("思考中...")
            self.replying = True
        
        if len(chat_completion.choices) == 0:
            if chat_completion.usage:
                if chat_completion.usage is not None:
                    print(f"Token Usage:")
                    print(f"    Prompt Token: {chat_completion.usage.prompt_tokens}")
                    print(f"    Completion Token: {chat_completion.usage.completion_tokens}")
                    print(f"    Total Token: {chat_completion.usage.total_tokens}")
            return
        
        # 处理流式响应
        if isinstance(chat_completion, ChatCompletionChunk):
            delta = chat_completion.choices[0].delta
            # 打印文本内容
            if delta.content:
                print(delta.content, end="", flush=True)
        
        # 处理完整响应
        else:
            message = chat_completion.choices[0].message
            # 普通文本回复或 JSON 响应（激活 MCP 模式）
            print(message.content)
        
        # 响应完成
        if chat_completion.choices[0].finish_reason:
            print("\n[LLM] Done")
            self.llm_done_signal.set()
            self.replying = False
            print()
        
    
    @registry.on_app_will_close()
    def on_app_will_close(self):
        self.running = False
