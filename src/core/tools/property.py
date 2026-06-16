from typing import Any

class Property:
    def __str__(self):
        return str(self.value)
    
    def __bool__(self):
        return bool(self.value)
    
    def __int__(self):
        return int(self.value)
    
    def __float__(self):
        return float(self.value)
    
    def __iter__(self):
        return iter(self.value)

    def __init__(self, value: Any):
        self.value = value


class PropertyMap:
    def __getitem__(self, key: str)->Property | None:
        return self._property_map.get(key)
    
    def __init__(self, arguments: dict[str, Any]):
        self._property_map: dict[str, Property] = {
            k: Property(v)
            for k,v in arguments.items()
        }
    
    @property
    def raw_data(self):
        return self._property_map
