from .properties.base_property import BaseProperty
from typing import Any

class PropertyMap:
    def __init__(self, properties: list[BaseProperty]):
        self._property_map: dict[str, Any] = {}
        self.properties: dict[str, BaseProperty] = {
            p.name: p for p in properties
        }
    
    def __getitem__(self, key: str) -> Any:
        if key not in self._property_map:
            raise KeyError(f"The key '{key}' is not found.")
        return self._property_map[key]
    
    def validate(self, arguments: dict[str, Any]) -> "PropertyMap":
        temp_arguments = {**arguments}
        validate_properties = {**self.properties}
        
        for arg, v in arguments.items():
            if arg not in self.properties:
                continue
            
            prop = validate_properties[arg]
            if v is None:
                if prop.allow_none:
                    del validate_properties[arg]
                    continue
                raise ValueError(f"The parameter '{prop.name}' cannot be null")
            
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

        self._property_map = temp_arguments
        return self
            
    @property
    def raw_data(self):
        return {**self._property_map}