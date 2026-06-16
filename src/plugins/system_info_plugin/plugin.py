from src.components.llm.message_state import MessageState
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry

import requests
import datetime
import platform

class SystemInfoPlugin(Plugin):
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.enable = False

    def get_datetime(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_ip(self):
        return requests.get("https://checkip.amazonaws.com/").text

    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState, additional: dict | None):
        ip = self.get_ip()

        state.append_dyn(f"""
## 系统信息
当前时间: {self.get_datetime()}
操作系统: {platform.system()} - {platform.version()}
""")
    