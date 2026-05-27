from abc import ABC, abstractmethod
from typing import Literal

class BaseProperty(ABC):
    def __init__(self, name: str, type: str, description: str, required: bool = True):
        self.name = name
        self.description = description
        self.type = type
        self.required = required
    @abstractmethod
    def get_schema(self) -> dict:
        ...
