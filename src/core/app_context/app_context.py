import tomllib
import pathlib
import asyncio
import sys
import os

import yaml

from src.core.logger.logger import LogCreator
from .app_config import AppConfig
from .default_configs import (
    app_config as default_app_config,
    gateway_config as default_gateway_config,
    fixed_config as default_fixed_config
)

from typing import (
    Any,
    Literal
)
from .types import (
    LaunchArgs,
    FixedConfigOption
)

logger = LogCreator.instance.create(__name__)
class AppContext:
    """
    程序上下文类，存储了整个程序的类配置等
    """

    event_loop: asyncio.AbstractEventLoop
    def __init__(self):
        self._launch_args = self._parse_args(sys.argv[1:])
        self._fixed_config: FixedConfigOption = self._load_fixed_config()
        self._data_home_path = self._data_home()
        self.__program_data_path = self._program_data_path()
        self._app_config = AppConfig(self._load_config(self._launch_args.config or os.path.join(self._data_home_path, "config.yaml")))
        self._mode: Literal["core", "client"] = "core" if self._launch_args.ipc_url is None else "client"
    
    @property
    def mode(self):
        """
        运行模式
        core: 内核模式
        client: 客户端模式
        """
        return self._mode

    
    @property
    def app_config(self):
        """
        应用程序配置
        """
        return self._app_config
    
    @property
    def program_data_path(self):
        """
        程序数据存储路径
        """
        return self.__program_data_path

    @property
    def data_home(self):
        """
        用户文件目录下的程序配置路径
        """
        return self._data_home_path
    
    @property
    def fixed_config(self):
        """
        固定参数，不可变的固定参数
        """
        return self._fixed_config

    @property
    def launch_args(self):
        """
        启动参数，命令行传参的内容
        """
        return self._launch_args
    
    def _data_home(self) -> str:
        path = pathlib.Path("~", f".{self.fixed_config.system_info.name}").expanduser().absolute()
        path.mkdir(exist_ok=True, parents=True)
        return str(path)
    
    @staticmethod
    def _program_data_path():
        return str(pathlib.Path(".", "data"))
    
    def _load_fixed_config(self) -> FixedConfigOption:
        path = pathlib.Path("./fixed_config.yaml").expanduser()
        if not path.exists():
            path.write_text(default_fixed_config)
            logger.info(f"Created fixed config file: '{path.absolute()}'")
            config = yaml.safe_load(default_fixed_config)
            return FixedConfigOption(**config)
        
        try:
            with open(path, "r", encoding="utf-8") as fs:
                config = yaml.safe_load(fs)
                return FixedConfigOption(**config)
        except PermissionError:
            sys.exit(f"No permission to read fixed config file: '{path.absolute()}'")

    @classmethod
    def _parse_args(cls, args: list[str]) -> LaunchArgs:
        temp_args: dict[str, str] = {}
        for argument in args:
            key_value_pair = argument.split("=", 1)
            if len(key_value_pair) >= 2:
                temp_args[key_value_pair[0]] = key_value_pair[1]
            else:
                logger.warning(f"Invalid argument: {argument}")

        return LaunchArgs(**temp_args)

    def _load_gateway_config(self, config_path: str) -> dict[str, Any]:
        path = pathlib.Path(config_path).expanduser()
        if not path.exists():
            path.write_text(default_gateway_config)
            logger.info(f"Created gateway config file: '{path.absolute()}'")
            config: dict = tomllib.loads(default_gateway_config)
        else:
            try:
                with open(path, "rb") as fs:
                    config: dict = tomllib.load(fs)
            except PermissionError:
                sys.exit(f"No permission to read config file: '{path.absolute()}'")
        try:
            return config
        except:
            raise

    def _load_config(self, path_str: str) -> dict[str, Any]:
        path = pathlib.Path(path_str).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(default_app_config)
            logger.info(f"Created config file: '{path.absolute()}'")
            app_config: dict = yaml.safe_load(default_app_config)
        else:
            try:
                with open(path, "r", encoding="utf-8") as fs:
                    app_config: dict = yaml.safe_load(fs)
            except PermissionError:
                sys.exit(f"No permission to read config file: '{path.absolute()}'")
        
        # 合并配置
        try:
            return app_config
        except Exception as e:
            sys.exit(f"Invalid config file: '{path.absolute()}'\n{e}")

app_context = AppContext()
