import os

from src.core import app_context
from src.components.llm.message_state import MessageState
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry
from .skill.client import Client as SkillsClient
from .skill.error import SkillNotFoundError
from .types import *



class SkillPlugin(Plugin):
    def __init__(self, *args, **keywords):
        super().__init__(*args, **keywords)
        self.enable = False
        self.client = SkillsClient(os.path.join(app_context.data_home, "skills"))
        self.current_skill_content = ""
        self.current_skill_name = ""
        self.references = []
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState, additional: dict | None):
        # state.skills = [{"name": skill["name"], "desc": skill["description"]} for skill in self.client.get_all_metadata()]

        if self.current_skill_content:
            state.append_dyn(self.current_skill_content)
            print(f"[SkillPlugin] skill: {self.current_skill_name}")
            
        if additional is None or "skill" not in additional:
            return
        
        command: Command = additional["skill"]
        
        if command["command"] == "activate" and (skill_name := command.get("skill_name")):
            try:
                self.current_skill_content = self.client.activate(skill_name)
                self.current_skill_name = skill_name
                print(f"[SkillPlugin] Activated skill:'{skill_name}'")
            except SkillNotFoundError:
                print(f"[SkillPlugin] Skill not found:'{skill_name}'")
                state.cancel(self.info.name, f"Skill not found:'{skill_name}'")
                return
        elif command["command"] == "deactivate":
            skill_name = self.current_skill_name
            self.current_skill_content = ""
            self.current_skill_name = ""
            self.references = []
            print(f"[SkillPlugin] Deactivated skill:'{skill_name}'")
            state.cancel(self.info.name, f"Deactivated skill:'{skill_name}'")
        
