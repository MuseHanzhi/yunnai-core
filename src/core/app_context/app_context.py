import pathlib
import asyncio
import sys
import os

import yaml

from src.core.logger.logger import LogCreator

from typing import TypeVar
from .types import (
    AppConfigOption,
    LaunchArgs,
    FixedConfigOption
)

T = TypeVar("T")
logger = LogCreator.instance.create(__name__)
class AppContext:
    event_loop: asyncio.AbstractEventLoop
    def __init__(self):
        self.launch_args = self._parse_args(sys.argv[1:])
        self.fixed_config: FixedConfigOption = self._load_config("./fixed_config.yaml")
        self.data_home = self._get_data_home()
        self.app_config: AppConfigOption = self._load_config(self.launch_args["config_path"] or os.path.join(self.data_home, "config.yaml"))
    
    def _get_data_home(self) -> str:
        path = pathlib.Path("~", f".{self.fixed_config["system_info"]["name"]}").expanduser().absolute()
        path.mkdir(exist_ok=True)
        return str(path)
    
    @classmethod
    def _parse_args(cls, args: list[str]) -> LaunchArgs:
        temp_args = {}
        for argument in args:
            key_value_pair = argument.split("=")
            if len(key_value_pair) >= 2:
                temp_args[key_value_pair[0]] = "=".join(key_value_pair[1:])
            else:
                logger.warning(f"Invalid argument: {argument}")

        default_llm: str | None = temp_args.get("default_llm")

        return LaunchArgs(
            ipc_uri=temp_args.get("ipc_uri"),
            default_llm=default_llm,
            config_path=temp_args.get("config_path")
        )

    def _load_config(self, path_str: str) -> T:
        path = pathlib.Path(path_str).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            sys.exit(f"Config file {path} not found")

        try:
            with open(path, "r", encoding="utf-8") as fs:
                return yaml.safe_load(fs)
        except PermissionError:
            sys.exit(f"No permission to read config file: '{path.absolute()}'")

app_context = AppContext()
