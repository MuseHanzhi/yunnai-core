import os

from src.core import app_context
from src.components.llm.message_state import MessageState
from src.plugins.plugin import Plugin
from src.plugins.hook_registry import registry
from .skill.client import Client as SkillsClient
from .skill.error import SkillNotFoundError
from .types import *

class SkillPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = SkillsClient(os.path.join(app_context.data_home, "skills"))
        self.current_skill_content = ""
        self.current_skill_name = ""
        self.references = []
    
    @registry.on_message_before_send()
    def on_message_before_send(self, state: MessageState, additional: dict | None):
        # state.skills = [{"name": skill["name"], "desc": skill["description"]} for skill in self.client.get_all_metadata()]
        raw_content = state.data.message.content
        msg = raw_content.split(" ")
        if msg[0].startswith("/skill:"):
            _, skill_name = msg[0].split(":")
            try:
                self.current_skill_content = self.client.activate(skill_name)
                self.current_skill_name = skill_name
                print(f"[SkillPlugin] Activated skill:'{skill_name}'")
                state.data.message.set_content(msg[-1])
            except SkillNotFoundError:
                print(f"[SkillPlugin] Skill not found:'{skill_name}'")
                state.canceled = True
                return
        elif msg[0].startswith("/skill:end"):
            skill_name = self.current_skill_name
            self.current_skill_content = ""
            self.current_skill_name = ""
            self.references = []
            print(f"[SkillPlugin] Deactivated skill:'{skill_name}'")
            state.canceled = True
            
        if self.current_skill_content:
            state.append_dyn(self.current_skill_content)
            print(f"[SkillPlugin] skill: {self.current_skill_name}")
