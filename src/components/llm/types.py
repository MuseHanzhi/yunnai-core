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
