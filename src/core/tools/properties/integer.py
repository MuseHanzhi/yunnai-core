from typing import Any, TypedDict

from .base_property import BaseProperty

class _Default(TypedDict):
    value: int

class Integer(BaseProperty):
    def __init__(self, name: str, description: str, range: tuple[int, int] | None = None, allow_none: bool = False, default: _Default | None = None):
        if range:
            if range[0] > range[1]:
                raise ValueError("range[0] must be less than range[1]")

        super().__init__(name, "integer", description, allow_none, default)
        self.range = range
        if default:
            self.validate(default["value"])

    def get_schema(self):
        schema: dict = {
            "type": "integer",
            "description": self.description,
        }
        if self.range:
            schema["minimum"] = self.range[0]
            schema["maximum"] = self.range[1]
        return schema
    
    def validate(self, value: Any) -> bool:
        super().validate(value)
        if self.range:
            if not (self.range[0] <= value <= self.range[1]):
                raise ValueError(f"The parameter '{self.name}' must be between {self.range[0]} and {self.range[1]}")
        return True

    