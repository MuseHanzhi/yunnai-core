from .base_property import BaseProperty
class Object(BaseProperty):
    def __init__(self, name: str, description: str, properties: list[BaseProperty] | None = None, required: bool = True):
        super().__init__(name, "object", description, required)
        self.properties = properties or []
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "description": self.description,
            "properties": {
                p.name: p.get_schema()
                for p in self.properties
            },
            "required": [p.name for p in self.properties if p.required]
        }