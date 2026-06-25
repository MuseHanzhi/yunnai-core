from .base_property import BaseProperty
from .object import Object
from typing import Any, Literal, TypeAlias, TypedDict

class _Default(TypedDict):
    value: list

_ArrayItemType: TypeAlias = Literal["string", "integer", "number", "boolean"] | Object | "Array"
class Array(BaseProperty):
    def __init__(self, name: str, description: str, item_type: _ArrayItemType, allow_none: bool = False, default: _Default | None = None):
        super().__init__(name, "array", description, allow_none, default)
        self.item_type = item_type
        if default:
            self.validate(default["value"])

    def get_schema(self):
        schema: dict 
        if isinstance(self.item_type, str):
            schema = {
                "type": self.item_type
            }
        else:
            schema = {** self.item_type.get_schema()}
            del schema["description"]
        return {
            "type": self.type,
            "description": self.description,
            "items": schema
        }
    
    def validate(self, value: Any) -> bool:
        if not isinstance(value, list):
            raise TypeError(f"The parameter '{self.name}' must be of type '{self.type}'")
        for item in value:
            if isinstance(self.item_type, str):
                if self.item_type == "boolean":
                    if not isinstance(item, bool): raise TypeError(f"The parameter '{self.name}' requires that all element types must be of type 'boolean'")
                elif self.item_type == "integer":
                    if not isinstance(item, int) or isinstance(item, bool): raise TypeError(f"The parameter '{self.name}' requires that all element types must be of type 'integer'")
                elif self.item_type == "number":
                    if not isinstance(item, (int, float)) or isinstance(item, bool): raise TypeError(f"The parameter '{self.name}' requires that all element types must be of type 'number'")
                elif self.item_type == "string":
                    if not isinstance(item, str): raise TypeError(f"The parameter '{self.name}' requires that all element types must be of type 'string'")
                else:
                    raise TypeError(f"Unknown element data type")
            elif isinstance(self.item_type, Object):
                self.item_type.validate(item)
            else:
                raise TypeError(f"Unknown element data type")
        return True
