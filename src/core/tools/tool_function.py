from .properties.base_property import BaseProperty
from .property_map import PropertyMap

import asyncio
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from typing import Callable, Any

class ToolFunction:
    async def __call__(self, arguments: dict) -> Any:
        property_map = PropertyMap(self.properties)
        try:
            property_map.validate(arguments)
        except Exception as ex:
            return f"# Call '{self.name}' result  \nCall function error: {ex}"
        
        try:
            call_res = self.func(property_map)
            if asyncio.iscoroutine(call_res):
                result = await call_res
            else:
                result = call_res
        except Exception as ex:
            return f"# Call '{self.name}' result  \nCall function exception: {ex}"
        return f"# Call '{self.name}' result  \n{result}"

    def __init__(self, name: str, description: str, func: Callable[[PropertyMap], Any], properties: list[BaseProperty] | None = None):
        self.name = name
        self.description = description
        self.func: Callable[[PropertyMap], Any] = func
        self.properties: list[BaseProperty] = properties or []
    
    def add_property(self, *properties: BaseProperty):
        self.properties.extend(properties)
    
    def get_schema(self)-> ChatCompletionToolParam:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        item.name: item.get_schema()
                        for item in self.properties
                    },
                    "required": [item.name for item in self.properties if item.required]
                }
            }
        }
