import pydantic
from pydantic import BaseModel
from typing import (
    TypedDict,
    NotRequired,
    Literal,
    Any   
)

# 生命周期Hook
Hooks = Literal[
    "on_canceled",
    "on_llm_response",
    "on_app_will_close",
    "on_message_before_send",
    "on_message_after_sended",
    "on_ready"
]

# 应用信息
class ApplicationInfo(BaseModel):
    name: str
    version: str

# 消息发送结构
class SendMessageOptions(TypedDict):
    model_name: str
    type: NotRequired[Literal["user", "tool"]]
    tool_call_id: NotRequired[str]
    stream: NotRequired[bool]
    image_urls: NotRequired[list[str]]
    additional: NotRequired[dict[str, Any]]


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

# region 固定配置(不会在用户配置中生成的配置)

class PluginConfigOption(BaseModel):
    search_path: str

class FixedConfigOption(BaseModel):
    """
    Fixed configuration for the core.
    """
    plugin_config: PluginConfigOption
    application_info: ApplicationInfo

# endregion


# region 启动参数
class LaunchArgs(BaseModel):
    """
    Launch arguments for the core.
    """
    model_config = pydantic.ConfigDict(extra="ignore")
    llm: str | None = pydantic.Field(default_factory=lambda: None)
    config: str | None = pydantic.Field(default_factory=lambda: None)
    ipc_url: str | None = pydantic.Field(default_factory=lambda: None)
    pwd: str | None = pydantic.Field(default_factory=lambda: None)

# endregion