"""Task planning and decomposition module."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Any
from core.brain import Brain
import json


class Planner:
    """Decomposes complex tasks into steps and selects appropriate skills."""
    
    def __init__(self, brain: Brain, available_skills: List[str]):
        self.brain = brain
        self.available_skills = available_skills
    
    def plan(self, user_request: str, intent: Dict[str, any]) -> List[Dict[str, Any]]:
        """Create a plan for executing a user request."""
        # If intent is multi_step or complex, use LLM to plan
        if intent["intent"] == "multi_step" or self._is_complex_request(user_request):
            return self._llm_plan(user_request, intent)
        
        # Simple single-step plan
        return [{
            "step": 1,
            "skill": self._map_intent_to_skill(intent["intent"]),
            "parameters": intent["parameters"],
            "description": f"Execute {intent['intent']}"
        }]
    
    def _is_complex_request(self, request: str) -> bool:
        """Check if request requires multiple steps."""
        complex_indicators = ["and", "then", "after", "also", "plus", ","]
        return any(indicator in request.lower() for indicator in complex_indicators)
    
    def _llm_plan(self, user_request: str, intent: Dict[str, any]) -> List[Dict[str, Any]]:
        """Use LLM to create a detailed plan."""
        skills_list = ", ".join(self.available_skills)
        
        # Check if request involves file creation
        file_keywords = ["create", "write", "make", "file", "java", "python", "code", "program"]
        has_file_creation = any(keyword in user_request.lower() for keyword in file_keywords)
        
        file_creation_note = ""
        if has_file_creation:
            file_creation_note = "\n\nCRITICAL: If the request involves creating or writing a file, you MUST use the 'write_file' skill with 'file_path' and 'content' parameters. NEVER use 'run_command' with echo for file creation as it doesn't work reliably on Windows."
        
        prompt = f"""Break down this user request into a step-by-step plan.

User Request: "{user_request}"
Intent: {intent['intent']}

Available Skills: {skills_list}
{file_creation_note}

Create a plan with multiple steps. For each step, specify:
- step: step number
- skill: which skill to use (must be one of the available skills)
- parameters: parameters needed for that skill (for write_file, use "file_path" and "content")
- description: what this step does

For file creation, ALWAYS use write_file skill. Example for creating a Java file:
{{"step": 2, "skill": "write_file", "parameters": {{"file_path": "HelloWorld.java", "content": "public class HelloWorld {{\\n    public static void main(String[] args) {{\\n        System.out.println(\\\"Hello, World!\\\");\\n    }}\\n}}"}}, "description": "Create HelloWorld.java file"}}

Respond in JSON format as an array of step objects. Example:
[
  {{"step": 1, "skill": "open_app", "parameters": {{"app_name": "vscode"}}, "description": "Open VS Code"}},
  {{"step": 2, "skill": "write_file", "parameters": {{"file_path": "HelloWorld.java", "content": "public class HelloWorld {{\\n    public static void main(String[] args) {{\\n        System.out.println(\\\"Hello, World!\\\");\\n    }}\\n}}"}}, "description": "Create HelloWorld.java file"}}
]

Respond with ONLY valid JSON array, no other text:"""

        response = self.brain.generate_response(prompt)
        
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                plan = json.loads(response[json_start:json_end])
                if isinstance(plan, list):
                    return plan
        except Exception as e:
            pass
        
        # Fallback: create simple plan
        return [{
            "step": 1,
            "skill": self._map_intent_to_skill(intent["intent"]),
            "parameters": intent["parameters"],
            "description": f"Execute {intent['intent']}"
        }]
    
    def _map_intent_to_skill(self, intent: str) -> str:
        """Map intent to skill name."""
        mapping = {
            "open_app": "open_app",
            "web_search": "web_search",
            "run_command": "run_command",
            "read_file": "read_file",
            "conversational": "conversational"
        }
        return mapping.get(intent, "conversational")

