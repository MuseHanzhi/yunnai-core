from .base_property import BaseProperty

class String(BaseProperty):
    def __init__(self, name: str, description: str, enum: list[str] | None = None, required: bool = True):
        super().__init__(name, "string", description, required)
        self.enum = enum
    
    def get_schema(self):
        schema: dict = {
            "type": "string",
            "description": self.description,
        }
        if self.enum:
            schema["enum"] = self.enum
        return schema