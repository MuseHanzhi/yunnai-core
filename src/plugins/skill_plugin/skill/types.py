from typing import (
    TypedDict,
    NotRequired,
    Literal
)

class ScriptEnvironment(TypedDict):
    type: Literal["python", "nodejs"]
    version: str
    mirror_url: NotRequired[str]
    dependencies: NotRequired[list[str]]

class SkillMetadataOption(TypedDict):
    disabled: NotRequired[bool]
    script_environment: NotRequired[ScriptEnvironment]

class SkillMetadata(TypedDict):
    name: str
    description: str
    version: NotRequired[str]
    author: NotRequired[str]
    license: NotRequired[str]
    metadata: NotRequired[SkillMetadataOption]
    compatibility: NotRequired[str]
    tags: NotRequired[list[str]]


class SkillData(TypedDict):
    metadata: SkillMetadata
    path: str
