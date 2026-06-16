import pydantic
from pydantic import BaseModel
from typing import (
    Literal,
    Any
)
# region 应用配置

# 大模型配置
class LLMOption(BaseModel):
    name: str
    key_name: str
    base_url: str
    stream: bool = pydantic.Field(default_factory=lambda: True)
    extra_body: dict[str, Any] = pydantic.Field(default_factory=lambda: {})

class LLMConfigOption(BaseModel):
    default: str | None
    models: dict[str, LLMOption] = pydantic.Field(default_factory=lambda: {})

# 日志配置
class LoggingHandlerOption(BaseModel):
    type: Literal["console", "file"]
    format: str

class LoggingOption(BaseModel):
    default: str
    log_path: str = pydantic.Field(default_factory=lambda: "logs")
    handlers: dict[str, list[LoggingHandlerOption]] = pydantic.Field(default_factory=lambda: {})

# 系统配置
class SystemConfig(BaseModel):
    require_env: list[str] = pydantic.Field(default_factory=lambda: [])
    thread_workers: int | None
# endregion