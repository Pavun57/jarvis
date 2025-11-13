"""Dynamic skill registry and loader."""
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
import sys


class Skill:
    """Base class for all skills."""
    
    name: str = "unknown"
    description: str = "No description"
    
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill. Must be implemented by subclasses."""
        raise NotImplementedError


class SkillRegistry:
    """Registry for dynamically loaded skills."""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
        self._load_skills()
    
    def _load_skills(self):
        """Dynamically load all skills from the skills directory."""
        if not self.skills_dir.exists():
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            return
        
        # Add skills directory to path
        skills_path = str(self.skills_dir)
        if skills_path not in sys.path:
            sys.path.insert(0, skills_path)
        
        # Load all Python files in skills directory
        for skill_file in self.skills_dir.glob("*.py"):
            if skill_file.name.startswith("_"):
                continue
            
            try:
                module_name = skill_file.stem
                spec = importlib.util.spec_from_file_location(module_name, skill_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find Skill classes in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Skill) and 
                            obj != Skill):
                            skill_instance = obj()
                            self.skills[skill_instance.name] = skill_instance
            except Exception as e:
                print(f"Warning: Failed to load skill {skill_file.name}: {e}")
    
    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(skill_name)
    
    def list_skills(self) -> List[str]:
        """List all available skill names."""
        return list(self.skills.keys())
    
    def execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a skill with given parameters."""
        skill = self.get_skill(skill_name)
        if not skill:
            return {"success": False, "error": f"Skill '{skill_name}' not found"}
        
        try:
            return skill.run(parameters)
        except Exception as e:
            return {"success": False, "error": str(e)}

