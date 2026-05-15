from typing import (
    TypedDict,
    Literal,
    Any
)

# 大模型配置
class LLMOption(TypedDict):
    name: str
    key_name: str
    base_url: str
    stream: bool | None
    extra_body: dict[str, Any]

class LLMConfigOption(TypedDict):
    default: str
    models: dict[str, LLMOption]

# 日志配置
class LoggingHandlerOptions(TypedDict):
    type: Literal["console", "file"]
    log_path: str | None
    format: str

class LoggingOption(TypedDict):
    default: str
    handlers: dict[str, list[LoggingHandlerOptions]]

# 系统配置

class ReconnectOption(TypedDict):
    enable: bool
    try_interval: int
    max_retry: int

class IPCOption(TypedDict):
    enable: bool
    uri: str
    reconnect: ReconnectOption

class SysInfo(TypedDict):
    name: str
    version: str
    

class SystemOption(TypedDict):
    require_env: list[str]
    thread_workers: int | None
    ipc: IPCOption

# 插件配置
class PluginOption(TypedDict):
    module_path: str
    class_name: str | None

class PluginConfigOption(TypedDict):
    search_path: str

# 顶级配置结构
class AppConfigOption(TypedDict):
    logging: Any
    system: SystemOption
    llm: LLMConfigOption

class FixedConfigOption(TypedDict):
    """
    Fixed configuration for the core.
    """
    plugin_config: PluginConfigOption
    system_info: SysInfo

# 启动参数
class LaunchArgs(TypedDict):
    """
    Launch arguments for the core.
    """
    ipc_uri: str | None
    default_llm: str | None
    config_path: str | None
