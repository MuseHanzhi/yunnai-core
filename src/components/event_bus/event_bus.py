import asyncio
from typing import Callable, List, TypeAlias, Union, Coroutine
from openai.types import CompletionUsage
from openai.types.create_embedding_response import Usage as EmbeddingUsage
from .types import ModelUsage, EmbeddingModelUsage, ChatModelUsage
from src.core.logger import LogCreator

_OnModelUsageHandler: TypeAlias = Callable[[ModelUsage], None]
_EventHandler: TypeAlias = Callable[..., Union[Coroutine, None]]

logger = LogCreator.instance.create(__name__)

class EventBus:
    """
    事件总线组件
    """
    def __init__(self):
        self._event_on_model_usage_handlers: List[_OnModelUsageHandler] = []
        self._event_handlers: dict[str, List[_EventHandler]] = {}
    
    def emit_model_usage(self, model_name: str, usage: Union[EmbeddingUsage, CompletionUsage]):
        for handler in self._event_on_model_usage_handlers:
            if isinstance(usage, CompletionUsage):
                handler(ChatModelUsage(type="chat", model_name=model_name, usage=usage))
            elif isinstance(usage, EmbeddingUsage):
                handler(EmbeddingModelUsage(type="embedding", model_name=model_name, usage=usage))

    def on_model_usage(self, handler: _OnModelUsageHandler):
        self._event_on_model_usage_handlers.append(handler)
    
    def on(self, event_name: str, handler: _EventHandler):
        self._event_handlers.setdefault(event_name, []).append(handler)
    
    async def emit(self, event_name: str, *args, **kwargs):
        tasks: list[asyncio.Task] = []
        handlers: list = []
        
        for handler in self._event_handlers.get(event_name, []):
            try:
                result = handler(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    tasks.append(asyncio.create_task(result))
                    handlers.append(handler)
            except Exception as ex:
                logger.exception(f"Error in sync handler {handler} for event '{event_name}': {ex}", exc_info=ex)
                
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result, handler in zip(results, handlers):
                if isinstance(result, BaseException):
                    logger.exception(
                        f"Error in async handler {handler} for event '{event_name}': {result}", 
                        exc_info=result
                    )
        
