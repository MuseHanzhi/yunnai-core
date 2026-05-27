from .base_property import BaseProperty
class Array(BaseProperty):
    def __init__(self, name: str, description: str, item_type: str, required: bool = True):
        super().__init__(name, "array", description, required)
        self.item_type = item_type

    def get_schema(self):
        return {
            "type": "array",
            "description": self.description,
            "items": {"type": self.item_type}
        }
    