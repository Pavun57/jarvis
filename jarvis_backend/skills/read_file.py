"""Skill to read files."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_registry import Skill
from core.executor import Executor
from typing import Dict, Any


class ReadFileSkill(Skill):
    """Reads file contents."""
    
    name = "read_file"
    description = "Reads and returns the contents of a file"
    
    def __init__(self):
        self.executor = Executor()
    
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the read file skill."""
        file_path = parameters.get("file_path")
        if not file_path:
            return {"success": False, "error": "file_path parameter required"}
        
        result = self.executor.read_file(file_path)
        return result

