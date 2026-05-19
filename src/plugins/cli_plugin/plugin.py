import asyncio
import json

from openai.types.chat import ChatCompletion, ChatCompletionChunk

from src.components.llm.message_state import MessageState
from src.plugins import Plugin, registry

class CliPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.llm_done_signal = asyncio.Event()
        self.replying = False

    async def run(self):
        # 初始化时确保信号是关闭的
        self.llm_done_signal.clear()
        
        while self.running:
            try:
                # 1. 等待用户输入
                user_input: str = await asyncio.to_thread(input, "> ")
                # 2. 【关键优化】在发起新请求前，再次确保信号是关闭的
                # 这样可以防止上一轮极快的响应“污染”这一轮的等待
                self.llm_done_signal.clear()
                self.replying = False # 重置回复状态
                
                # 3. 发送消息（触发流式回调）
                await self.application.send_message(user_input, {
                    "model_name": "qwen3.6-plus",
                    "stream": True,
                })
                
                # 4. 安心等待大模型输出完毕
                await self.llm_done_signal.wait()
                
            except KeyboardInterrupt:
                await self.application.exit()
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
        self.running = True
        self.event_loop.create_task(self.run())
    
    @registry.on_canceled()
    def on_canceled(self, state: MessageState):
        self.llm_done_signal.set()
        print("[CliPlugin]: 取消发送")

    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState, additional: dict | None):
        # 检查是否有可用工具
        # state.is_stream = False   
        state.top_prompt = """
你叫云乃，是一个智能助手

# 绝对遵守原则
1. **不要**输出任何Markdown格式，使用纯文本输出

# 实时性信息处理规范（强制执行）

## 必须联网搜索的情况
当用户询问以下类型的信息时，你必须先调用WebSearch工具进行搜索，然后基于搜索结果回答：
- 新闻事件、时事动态
- 天气信息、气象预报
- 股票价格、金融市场数据
- 科技产品发布、软件版本更新
- 体育赛事结果、比分
- 最新政策、法规变动
- 任何可能在训练数据之后发生变化的信息

## 判断标准
**核心原则**：如果答案可能在你的训练数据截止后发生变化，就必须搜索！

具体判断：
- 涉及具体时间点的信息（如"今天"、"最近"、"当前"）→ 必须搜索
- 询问实时状态（如"现在股价多少"、"今天天气如何"）→ 必须搜索
- 最新动态类问题（如"某某公司最新消息"）→ 必须搜索
- 不确定信息是否过时 → 宁可搜索，不要猜测

## 执行流程
收到用户问题后，严格按以下步骤执行：
1. **判断**：是否需要实时信息？
2. **搜索**：如需实时信息，立即调用WebSearch工具
3. **回答**：基于搜索结果组织答案，并注明信息来源时间

## 保守策略
**宁可多搜，不可错答**：
- 当你不确定信息是否需要实时更新时，优先选择搜索
- 避免凭记忆提供可能已过时的信息
- 如果无法确定答案的时效性，明确告知用户并建议搜索
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
