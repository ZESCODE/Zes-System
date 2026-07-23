"""Unified Skill Registry — load, register, and execute all skills."""
from typing import Dict, Any, Optional
import os, importlib, inspect


class SkillRegistry:
    def __init__(self):
        self.skills: Dict[str, Any] = {}

    def register(self, name: str, skill_instance) -> None:
        self.skills[name] = skill_instance

    async def execute(self, skill_name: str, method: str, **kwargs) -> Dict[str, Any]:
        skill = self.skills.get(skill_name)
        if not skill:
            return {"success": False, "error": f"Skill '{skill_name}' not found"}
        func = getattr(skill, method, None)
        if not func or not callable(func):
            return {"success": False, "error": f"Method '{method}' not found in {skill_name}"}
        try:
            if inspect.iscoroutinefunction(func):
                return await func(**kwargs)
            return func(**kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_skills(self) -> Dict[str, list]:
        return {name: [m for m in dir(skill) if not m.startswith("_") and callable(getattr(skill, m, None))]
                for name, skill in self.skills.items()}


def create_registry() -> SkillRegistry:
    """Create and populate the full skill registry."""
    registry = SkillRegistry()

    # Chrome CDP
    try:
        from .chrome_cdp import ChromeCDPSkill
        registry.register("chrome_cdp", ChromeCDPSkill(headless=True))
    except ImportError:
        pass

    # Filesystem
    from .filesystem import FileSystemSkill
    registry.register("filesystem", FileSystemSkill())

    # REST API
    from .restapi import RESTAPISkill
    registry.register("rest", RESTAPISkill())

    # Email
    # Requires credentials — registered with placeholder, configure before use
    # registry.register("email", EmailSkill(...))

    # Database
    # Requires db_url — registered with placeholder
    # registry.register("db", DatabaseSkill(...))

    # System Commands
    from .system_cmds import SystemCommandsSkill
    registry.register("system", SystemCommandsSkill())

    # PDF
    try:
        from .pdf_gen import PDFGenerationSkill
        registry.register("pdf", PDFGenerationSkill())
    except ImportError:
        pass

    # Spreadsheet
    try:
        from .spreadsheet import SpreadsheetSkill
        registry.register("spreadsheet", SpreadsheetSkill())
    except ImportError:
        pass

    # OCR
    try:
        from .ocr import OCRSkill
        registry.register("ocr", OCRSkill())
    except ImportError:
        pass

    # Slack
    # Requires token — register after injection
    # registry.register("slack", SlackSkill(...))

    # Calendar
    # Requires Google credentials
    # registry.register("calendar", CalendarSkill(...))

    # SSH
    # Requires host/username/password
    # registry.register("ssh", SSHSkill(...))

    return registry
