import pathlib
import yaml

from src.components.llm.message_state import MessageState
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry
from .skill.client import Client as SkillsClient
from .types import *

class SkillPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.config = SkillPlugin.read_config(pathlib.Path(__file__).parent / "config.yaml")
        self.client = SkillsClient(self.config["skill_path"])

    @staticmethod
    def read_config(config_path: pathlib.Path) -> SkillConfig:
        if not config_path.parent.exists():
            config_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            return SkillConfig(skill_path="/yunnai/skills")
        try:
            with open(config_path, "r", encoding="utf-8") as fs:
                config = yaml.safe_load(fs)
                if "skill_path" not in config:
                    config["skill_path"] = "/yunnai/skills"
                return SkillConfig(**config)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件格式错误: {config_path}\n详情: {e}")
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState):
        state.skills = [{"name": skill["name"], "desc": skill["description"]} for skill in self.client.get_all_metadata()]
        state.append_dyn("")