from typing import TypedDict, Literal

class PluginManifest(TypedDict):
    description: str
    name: str
    author: str
    version: str
    entry: str
    type: Literal["system", "normal"]
    order: int
