from typing import Any, TypedDict

from .base_property import BaseProperty

class _Default(TypedDict):
    value: dict

class Object(BaseProperty):
    def __init__(self, name: str, description: str, properties: list[BaseProperty] | None = None, allow_none: bool = False, default: _Default | None = None):
        super().__init__(name, "object", description, allow_none, default)
        self.properties = {
            p.name: p
            for p in properties or []
        }
        if default:
            self.validate(default["value"])
    
    def get_schema(self) -> dict:
        return {
            "type": self.type,
            "description": self.description,
            "properties": {
                p.name: p.get_schema()
                for p in self.properties.values()
            },
            "required": [name for name, p in self.properties.items() if p.required]
        }
    
    def validate(self, value: Any):
        if not isinstance(value, dict):
            return False
        temp_arguments = {**value}
        validate_properties = {**self.properties}
        
        for arg, v in value.items():
            if arg not in self.properties:
                continue
            
            prop = validate_properties[arg]
            if v is None:
                if prop.allow_none:
                    del validate_properties[arg]
                    continue
                raise ValueError(f"The parameter '{self.name}' cannot be null")
            
            prop.validate(v)
            del validate_properties[arg]
        
        error_msgs: list[str] = []
        for prop in validate_properties.values():
            if not prop.required:
                temp_arguments[prop.name] = prop.default
            else:
                error_msgs.append(f"The parameter '{prop.name}' is required.")
                
        if error_msgs:
            raise Exception("\n".join(error_msgs))