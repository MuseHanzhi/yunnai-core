import pathlib
import asyncio
import sys

import yaml

from src.core.logger.logger import LogCreator
from .types import (
    AppConfigOption,
    LaunchArgs
)


logger = LogCreator.instance.create(__name__)
class AppContext:
    event_loop: asyncio.AbstractEventLoop
    def __init__(self):
        self.app_config = self._load_config("~/.yunnai/config.yaml")
        self.launch_args = self._parse_args(sys.argv[1:])
    
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
            default_llm=default_llm
        )

    def _load_config(self, path_str: str) -> AppConfigOption:
        path = pathlib.Path(path_str).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            sys.exit(f"Config file {path} not found")

        with open(path, "r", encoding="utf-8") as fs:
            return yaml.safe_load(fs)

app_context = AppContext()
