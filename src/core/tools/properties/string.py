from .base_property import BaseProperty
from typing import Any, TypedDict

class _Default(TypedDict):
    value: str

class String(BaseProperty):
    def __init__(self, name: str, description: str, enum: list[str] | None = None, allow_none: bool = False, default: _Default | None = None):
        super().__init__(name, "string", description, allow_none, default)
        self.enum = enum
        if default:
            self.validate(default["value"])
    
    def get_schema(self):
        schema: dict = {
            "type": self.type,
            "description": self.description,
        }
        if self.enum:
            schema["enum"] = self.enum
        return schema
    
    def validate(self, value: Any) -> bool:
        super().validate(value)

        if self.enum and value not in self.enum:
            raise ValueError(f"The value of the parameter '{self.name}' must be selected from one of '{','.join(self.enum)}'")
        
        return True
