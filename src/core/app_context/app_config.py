import json
import yaml
import tomllib
import pathlib
from typing import (
    Any
)

class AppConfig:
    def __getitem__(self, key: str) -> dict[str, Any] | None:
        return self.get_section(key)

    def __init__(self, config_content: dict):
        self.app_config: dict = config_content
    
    def get_section(self, path: str) -> dict[str, Any] | None:
        current_config: dict | None = self.app_config
        for key in path.split("."):
            if current_config is None:
                return None
            current_config = current_config.get(key, None)
        return current_config
    
    def get_raw_config(self) -> dict:
        return self.app_config

    @classmethod
    def from_file(cls, path: str, default_config: str | None = None) -> 'AppConfig':
        target_path = pathlib.Path(path).expanduser()
        config_data = {}
        
        if target_path.exists():
            with target_path.open("r", encoding="utf-8") as file:
                content = file.read()
                if content.strip():
                    if target_path.suffix == ".json":
                        config_data = json.loads(content)
                    elif target_path.suffix == ".yaml":
                        config_data = yaml.safe_load(content) or {}
                    elif target_path.suffix == ".toml":
                        try:
                            config_data = tomllib.loads(content)
                        except tomllib.TOMLDecodeError:
                            if not content.strip():
                                config_data = {}
                            else:
                                raise
        elif default_config:
            with target_path.open("w", encoding="utf-8") as file:
                file.write(default_config)
        else:
            raise FileNotFoundError(path)
            
        return cls(config_data)
