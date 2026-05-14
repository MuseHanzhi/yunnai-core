from pydantic import BaseModel
from typing import (
    TypedDict,
    Required,
    Literal,
    Union
)

class Credential(TypedDict):
    api_key: Required[str]
    base_url: Required[str]

class ImageResourceOptions(TypedDict):
    type: Literal["image"]
    image_url: str

class AudioResourceOptions(TypedDict):
    type: Literal["audio"]
    input_audio: str

class FileResourceOptions(TypedDict):
    type: Literal["file"]
    file: str

class TextResourceOptions(TypedDict):
    type: Literal["text"]
    text: str

ResourceOptions = Union[ImageResourceOptions, AudioResourceOptions, FileResourceOptions, TextResourceOptions]


# MCP
class MCPData(TypedDict):
    name: str
    desc: str

# Skill
class SkillData(TypedDict):
    name: str
    desc: str

class OutputShema(BaseModel):
    name: str
    json_schema: dict
    strict: bool
