import asyncio
from typing import Callable

from src.core import app_context
from src.types.lfecycle_hooks import Hooks
from .plugin import Plugin

class HookMetadata:

    def __init__(self, hook_name: Hooks, hook_func: Callable, plugin: Plugin):
        self.hook_func = hook_func
        self.hook_name: Hooks = hook_name
        self.plugin = plugin
    async def run(self, *args, **arguments):
        call = self.hook_func(self.plugin, *args, **arguments)
        if asyncio.iscoroutine(call):
            await call
