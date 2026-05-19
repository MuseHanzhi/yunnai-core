import pydantic
from pydantic import BaseModel
from typing import (
    Literal,
    NotRequired,
    Any
)

#region 网关配置
class GatewayServerOption(BaseModel):
    host: str = pydantic.Field(default_factory=lambda: "0.0.0.0")
    port: int = pydantic.Field(default_factory=lambda: 8866)
    token: str = pydantic.Field(default_factory=lambda: "token_123456")
    max_count: int = pydantic.Field(default_factory=lambda: 5)
    timeout_ms: int = pydantic.Field(default_factory=lambda: 5000)

class GatewayClientOption(BaseModel):
    protocol: Literal["ws", "wss"] = pydantic.Field(default_factory=lambda: "wss")
    host: str = pydantic.Field(default_factory=lambda: "127.0.0.1")
    port: int = pydantic.Field(default_factory=lambda: 8866)
    token: str | None
    heartbeat_ms: int = pydantic.Field(default_factory=lambda: 5000)

class GatewayAppOption(BaseModel):
    appid: str
    name: str

# 网关配置顶级结构
class GatewayOption(BaseModel):
    mode: Literal["server", "client"] = pydantic.Field(default_factory=lambda: "server")
    server: GatewayServerOption
    client: GatewayClientOption | None
    apps: list[GatewayAppOption] = pydantic.Field(default_factory=lambda: [])

# endregion

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

class SystemOption(BaseModel):
    require_env: list[str] = pydantic.Field(default_factory=lambda: [])
    thread_workers: int | None

# 应用配置顶级配置结构
class AppConfigOption(BaseModel):
    logging: LoggingOption
    system: SystemOption
    gateway: GatewayOption
    llm: LLMConfigOption

# endregion


# region 固定配置(不会在用户配置中生成的配置)
class PluginConfigOption(BaseModel):
    search_path: str

# 系统配置
class SysInfo(BaseModel):
    name: str
    version: str

class FixedConfigOption(BaseModel):
    """
    Fixed configuration for the core.
    """
    plugin_config: PluginConfigOption
    system_info: SysInfo

# endregion


# region 启动参数
class LaunchArgs(BaseModel):
    """
    Launch arguments for the core.
    """
    model_config = pydantic.ConfigDict(extra="ignore")
    llm: str | None = None
    config: str | None = None
    gateway: str | None = None

# endregion