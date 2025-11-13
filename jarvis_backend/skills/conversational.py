"""Conversational skill for general chat."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_registry import Skill
from typing import Dict, Any


class ConversationalSkill(Skill):
    """Handles general conversational requests."""
    
    name = "conversational"
    description = "Handles general conversation and questions"
    
    def run(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the conversational skill."""
        # This skill doesn't do anything itself - it's handled by the brain
        return {
            "success": True,
            "message": "Conversational request handled by LLM"
        }

