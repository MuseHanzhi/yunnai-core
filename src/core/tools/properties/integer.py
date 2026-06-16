from .base_property import BaseProperty

class Integer(BaseProperty):
    def __init__(self, name: str, description: str, range: tuple[int, int] | None = None, required: bool = True):
        if range:
            if range[0] > range[1]:
                raise ValueError("range[0] must be less than range[1]")

        super().__init__(name, "integer", description, required)
        self.range = range

    def get_schema(self):
        schema: dict = {
            "type": "integer",
            "description": self.description,
        }
        if self.range:
            schema["minimum"] = self.range[0]
            schema["maximum"] = self.range[1]
        return schema