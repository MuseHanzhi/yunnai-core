from abc import ABC, abstractmethod
from typing import Any

class BaseProperty(ABC):
    def __init__(self, name: str, type: str, description: str, allow_none: bool = False, default: Any | None = None):
        self.name = name
        self.description = description
        self.type = type
        self.raw_type = self._get_raw_type(type)

        self.allow_none = allow_none
        self.required = False
        if default is not None and "value" in default:
            setattr(self, "_default", default["value"])
        else:
            self.required = True
    
    @property
    def default(self):
        if hasattr(self, "_default"):
            return getattr(self, "_default")
        raise ValueError(f"The parameter '{self.name}' is required")
    
    @staticmethod
    def _get_raw_type(type: str) -> type:
        if type == "string":
            return str
        elif type == "integer":
            return int
        elif type == "number":
            return float
        elif type == "boolean":
            return bool
        elif type == "object":
            return dict
        elif type == "array":
            return list
        raise TypeError(f"不支持的类型'{type}'")

    @abstractmethod
    def get_schema(self) -> dict:
        ...
    
    def validate(self, value: Any) -> bool:
        if not self.raw_type:
            return True
        if not isinstance(value, self.raw_type):
            raise TypeError(f"The '{self.name}' parameter is of the wrong type. It should be of type '{self.type}'")
        return True
