from .types import *
from .error import *
import pathlib
import yaml
import re
from src.core.logger.logger import LogCreator

logger = LogCreator.instance.create(__name__)
class Client:
    def __getitem__(self, skill_name: str):
        if skill_name not in self.skills:
            raise SkillNotFoundError(skill_name)
        return self.skills[skill_name]
    
    def __contains__(self, skill_name: str):
        return skill_name in self.skills
    
    def __len__(self):
        return len(self.skills)
    
    def __str__(self):
        return "\n".join([f"- `{metadata['metadata']['name']}`: {metadata['metadata']['description']}" for metadata in self.skills.values()])

    def __init__(self, skill_path: str):
        self.skill_path = pathlib.Path(skill_path)
        self.skill_path.expanduser().mkdir(exist_ok=True, parents=True)
        self.skills = Client.discover(self.skill_path.expanduser())
    
    @staticmethod
    def discover(path: pathlib.Path) -> dict[str, SkillData]:
        skill_dirs = [(d, (d / "SKILL.md")) for d in path.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
        skills: dict[str, SkillData] = {}
        for dir, skill_file in skill_dirs:
            try:
                skill_metadata = Client.parse_skill_metadata(skill_file)
                skills[skill_metadata.get('name') or dir.name] = {
                    "metadata": skill_metadata,
                    "path": str(dir.absolute())
                }
                logger.info(f"found skill: {skill_metadata.get('name') or dir.name}")
            except SkillMetadataParseError as e:
                logger.warning(f"Skill metadata parse error: {e}")
                continue

        return skills
    
    @staticmethod
    def parse_skill_metadata(path: pathlib.Path) -> SkillMetadata:
        REGEX = re.compile(r"^---\s*\n(?P<content>[\s\S]*?)\n---", re.MULTILINE)
        content: str
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        match = REGEX.match(content)
        if match is None:
            raise SkillMetadataParseError("Invalid skill metadata") from None
        
        yaml_content = match.group("content")
        try:
            metadata: SkillMetadata = yaml.safe_load(yaml_content)
            if "name" not in metadata or "description" not in metadata:
                raise SkillMetadataParseError("Invalid skill metadata")
            return metadata
        except yaml.YAMLError as e:
            raise SkillMetadataParseError("Invalid skill metadata") from e

    def get_all_metadata(self) -> list[SkillMetadata]:
        return [skill["metadata"] for skill in self.skills.values()]

    def activate(self, skill_name: str) -> str:
        if skill_name not in self.skills:
            raise SkillNotFoundError(skill_name)
        REGEX = re.compile(r"^---\s*\n(?P<content>[\s\S]*?)\n---", re.MULTILINE)
        skill_content: str

        target_skill_md = pathlib.Path(self.skills[skill_name]["path"], "SKILL.md")
        if not target_skill_md.exists():
            self.skills.pop(skill_name)
            raise SkillNotFoundError(skill_name)
        
        with open(target_skill_md, "r", encoding="utf-8") as f:
            skill_content = f.read()
        content = REGEX.sub("", skill_content)
        return content

    def script_runner(self, skill_name: str, script: str, *args: str):
        skill = self.skills.get(skill_name)
        if skill is None:
            raise SkillNotFoundError(skill_name)
        script_path = pathlib.Path(skill["path"], "scripts", script)
        if not script_path.exists():
            script_path = pathlib.Path(skill["path"], script)
            if not script_path.exists():
                raise SkillScriptNotFoundError(f"{skill_name} not found script: {script}")
        
        cmd_components = []