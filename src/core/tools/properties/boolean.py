from .base_property import BaseProperty
class Boolean(BaseProperty):
    def __init__(self, name: str, description: str, required: bool = True):
        super().__init__(name, "boolean", description, required)
    
    def get_schema(self):
        return {
            "type": self.type,
            "description": self.description
        }