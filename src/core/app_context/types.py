import pydantic
from pydantic import BaseModel


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
    ipc_url: str | None = None

# endregion