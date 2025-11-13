"""Skill to run system commands."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_registry import Skill
from core.executor import Executor
from typing import Dict, Any


class RunCommandSkill(Skill):
    """Executes system commands."""
    
    name = "run_command"
    description = "Runs system commands and returns output"
    
    def __init__(self):
        self.executor = Executor()
    
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the run command skill."""
        command = parameters.get("command")
        if not command:
            return {"success": False, "error": "command parameter required"}
        
        result = self.executor.run_command(command)
        return result

