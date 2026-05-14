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
        self.llm_done_signal = asyncio.Event()
        self.replying = False
        self.all_text = ""
        self.current_mcp_name = ""
        self.mcp_tools = []
    
    @registry.on_app_initialize()
    def on_app_initialize(self, app: "Application"):
        self.app = app
        self.event_loop = app.event_loop
        self.running = True

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
    def on_ready(self):
        self.event_loop.create_task(self.run())
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState):
        state.tools = self.mcp_tools
        state.is_stream = False
        state.set_output_schema("reply", {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "对用户的自然语言回复。"
                },
                "activate": {
                    "type": ["object", "null"],
                    "description": "如果需要激活 MCP 或 Skill，则填写此对象，否则为 null。",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["mcp", "skill"],
                            "description": "激活类型：mcp 或 skill"
                        },
                        "name": {
                            "type": "string",
                            "description": "MCP Server 名称或 Skill 名称"
                        }
                    },
                    "required": ["type", "name"] # 强制要求这三个字段
                }
            },
            "required": ["content", "activate"]
        })
        state.top_prompt = """
你是一个智能助手。你的唯一任务是输出一个严格的 JSON 对象。

# 绝对约束
1. **严禁**输出任何 Markdown 格式（如 ```json）。
2. **严禁**输出 Schema 中未定义的字段。
3. **严禁**遗漏 Schema 中要求的必填字段。
4. 如果 **activate** 不为 null，它**必须**包含 **type**, **name** 两个字段。
5. **type** 字段**必须**是 "mcp" 或 "skill" 之一。

# 输出格式示例
{
  "content": "好的，正在为您激活...",
  "activate": {
    "type": "mcp",
    "name": "mcd-mcp"
  }
}

# 任务
分析用户输入，决定是否需要激活工具。
- 如果需要，填充 **activate** 对象。
- 如果不需要，**activate** 设为 null。
- 在 **content** 中回复用户。
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
            return
        if isinstance(chat_completion, ChatCompletionChunk):
            if chat_completion.choices[0].delta.content:
                # print(chat_completion.choices[0].delta.content, end="")
                self.all_text += chat_completion.choices[0].delta.content
        else:
            if chat_completion.choices[0].message.content:
                # print(chat_completion.choices[0].message.content, end="")
                self.all_text += chat_completion.choices[0].message.content
        if chat_completion.choices[0].finish_reason == "stop":
            output = json.loads(self.all_text)
            print(output["content"])
            if output["activate"]:
                print(f"[LLM] Activating {output['activate']['type']} {output['activate']['name']}")

                mcp_plugin: Plugin | None = self.app.plugin_manager.get_plugin("mcp_plugin")
                if mcp_plugin is not None and isinstance(mcp_plugin, MCPPlugin):
                    get_tools_result = await mcp_plugin.manager.activate(output["activate"]["name"])
                    self.mcp_tools = get_tools_result["tools"]
                    print(f"[MCP] {output['activate']['name']} find {len(self.mcp_tools)} tools")
            self.all_text = ""
            self.llm_done_signal.set()  # 输出完毕信号
            self.replying = False
            print("[LLM] Done")
            print()
        if chat_completion.usage is not None:
            print(f"Tokens: {chat_completion.usage.total_tokens}")
        
    
    @registry.on_app_will_close()
    def on_app_will_close(self):
        self.running = False
