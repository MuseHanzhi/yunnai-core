from typing import (
    TypedDict,
    Literal,
    NotRequired
)

class SkillConfig(TypedDict):
    py_executable: str
    js_executable: str

class Command(TypedDict):
    command: Literal["activate", "deactivate"]
    skill_name: NotRequired[str]
