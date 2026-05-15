class SkillMetadataParseError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class SkillNotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class SkillScriptNotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
