"""Skill to open applications."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_registry import Skill
from core.executor import Executor
from typing import Dict, Any


class OpenAppSkill(Skill):
    """Opens applications on the system."""
    
    name = "open_app"
    description = "Opens an application by name"
    
    def __init__(self):
        self.executor = Executor()
    
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the open app skill."""
        app_name = parameters.get("app_name")
        if not app_name:
            return {"success": False, "error": "app_name parameter required"}
        
        result = self.executor.open_app(app_name)
        return result

