from openai.types.chat import ChatCompletionChunk, ChatCompletion

from src.components.llm.message_state import MessageState

from typing import (
    TYPE_CHECKING,
    Literal,
    Any
)
if TYPE_CHECKING:
    from src.application import Application

IPCTiming = Literal["before", "after"]
class PluginInfo:
    def __init__(self, name: str, author: str, version: str, description: str, type: str):
        self.name = name
        self.author = author
        self.version = version
        self.description = description
        self.type = type

class Plugin:
    info: PluginInfo
    def __init__(self):
        self.enable = True


    def deinit(self):
        """
        插件被移除时触发
        """
        ...
    
    def on_llm_response(self, chat_completion: ChatCompletionChunk | ChatCompletion | Exception):
        """
        **大模型响应时触发**  
        建议不要在此Hook执行的过程中调用主程序的send_message操作，因为插件机制的原因可能会导致深度递归

        在此Hook中，可以收集到大模型回复的流式数据，并做相应的处理  
        结合finish_reason参数可以判断大模型回复是否结束

        如果需要在此调用大模型，可以访问主程序的llm_client属性，调用create_state方法创建一个MessageState对象  
        然后调用lllm_client.stream_response方法获取大模型回复的流式数据，non_stream_response为非流式响应

        
        :param chat_completion: 大模型回复的内容
        """
        ...
    
    def on_message_before_send(self, state: MessageState):
        """
        向智能体发送信息前触发
        
        :param state: 消息状态
        """
        ...
    
    def on_message_after_sended(self, state: MessageState):
        """
        向智能体发送信息后触发
        """
        ...

    def on_ready(self, app: "Application"):
        """
        程序就绪时触发
        """
        ...
    
    def on_app_will_close(self):
        """
        向智能体发送信息前触发
        
        :param self: 插件实例
        """
        ...

    def emit(self, name: str, arguments: dict) -> Any:
        """
        用于插件与插件之间的通信
        :param name: 命令
        :type name: str
        :param arguments: 参数
        :type arguments: dict
        """
        ...
