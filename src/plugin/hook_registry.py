from src.types import Hooks
from .plugin import Timing

class HookRegistry:
    def hook(self, hook_name: Hooks, timing: Timing):
        def decorator(func):
            setattr(func, "_hook_name", hook_name)
            setattr(func, "_hook_timing", timing)
            return func
        return decorator
    
    def on_canceled(self, timing: Timing = "before"):
        return self.hook("on_canceled", timing)

    def on_app_will_close(self, timing: Timing = "before"):
        return self.hook("on_app_will_close", timing)
    
    def on_ready(self, timing: Timing = "before"):
        return self.hook("on_ready", timing)

    def on_llm_response(self, timing: Timing = "before"):
        return self.hook("on_llm_response", timing)
    
    def on_message_after_sended(self, timing: Timing = "before"):
        return self.hook("on_message_after_sended", timing)
    
    def on_message_before_send(self, timing: Timing = "before"):
        return self.hook("on_message_before_send", timing)

registry = HookRegistry()
