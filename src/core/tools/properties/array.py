from .base_property import BaseProperty
from .object import Object
from typing import Literal, TypeAlias


_ArrayItemType: TypeAlias = Literal["string", "integer", "number", "boolean"] | Object
class Array(BaseProperty):
    def __init__(self, name: str, description: str, item_type: _ArrayItemType, required: bool = True):
        super().__init__(name, "array", description, required)
        self.item_type = item_type

    def get_schema(self):
        shema: dict 
        if isinstance(self.item_type, str):
            shema = {
                "type": self.item_type
            }
        else:
            shema = self.item_type.get_schema()
            del shema["description"]
        return {
            "type": self.type,
            "description": self.description,
            "items": shema
        }
