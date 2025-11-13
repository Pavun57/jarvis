"""Skill to write/create files."""
import sys
from pathlib import Path

# Add jarvis_backend to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_registry import Skill
from typing import Dict, Any


class WriteFileSkill(Skill):
    """Creates or writes to files."""
    
    name = "write_file"
    description = "Creates or writes content to a file"
    
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the write file skill."""
        file_path = parameters.get("file_path")
        content = parameters.get("content", "")
        
        if not file_path:
            return {"success": False, "error": "file_path parameter required"}
        
        try:
            path = Path(file_path)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"Created/wrote to file: {file_path}",
                "file_path": str(path.absolute())
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to write file: {str(e)}"}

