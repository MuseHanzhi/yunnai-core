from typing import TypedDict

from .base_property import BaseProperty

class _Default(TypedDict):
    value: bool

class Boolean(BaseProperty):
    def __init__(self, name: str, description: str, allow_none: bool = False, default: _Default | None = None):
        super().__init__(name, "boolean", description, allow_none, default)
    
    def get_schema(self):
        return {
            "type": self.type,
            "description": self.description
        }
    