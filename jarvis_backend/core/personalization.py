"""User personalization management."""
import sys
import re
import json
from pathlib import Path
from typing import Dict, Optional

# Add jarvis_backend to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory import memory_manager
from core.brain import Brain


class Personalization:
    """Manages user personalization and automatic preference extraction."""
    
    def __init__(self, brain: Brain):
        self.brain = brain
        self.memory = memory_manager
    
    def get_personalization_context(self) -> str:
        """Get personalization context for prompts."""
        context_parts = []
        
        # Get user name
        name = self.memory.get_preference("user_name")
        if name:
            context_parts.append(f"User's name: {name}")
        
        # Get tone preference
        tone = self.memory.get_preference("tone_style")
        if tone:
            context_parts.append(f"Preferred tone: {tone}")
        
        # Get frequently used apps
        apps = self.memory.get_preference("frequent_apps")
        if apps:
            context_parts.append(f"Frequently used apps: {apps}")
        
        # Get user facts
        from sqlmodel import Session, select
        from core.memory import UserFact
        
        with Session(self.memory.engine) as session:
            facts = session.exec(select(UserFact)).all()
            if facts:
                context_parts.append("User Facts:")
                for fact in facts:
                    context_parts.append(f"- {fact.fact_key}: {fact.fact_value}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def extract_and_save_preferences(self, user_message: str, assistant_response: str):
        """Automatically extract preferences from conversation and save them."""
        # Extract user name
        name_patterns = [
            r"my name is ([A-Z][a-z]+)",
            r"call me ([A-Z][a-z]+)",
            r"i'm ([A-Z][a-z]+)",
            r"i am ([A-Z][a-z]+)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_message, re.IGNORECASE)
            if match:
                name = match.group(1)
                self.memory.save_preference("user_name", name)
                break
        
        # Extract tone preferences
        tone_keywords = {
            "formal": ["formal", "professional", "business"],
            "casual": ["casual", "relaxed", "friendly"],
            "technical": ["technical", "detailed", "precise"],
        }
        
        for tone, keywords in tone_keywords.items():
            if any(keyword in user_message.lower() for keyword in keywords):
                self.memory.save_preference("tone_style", tone)
                break
        
        # Use LLM to extract other preferences
        self._llm_extract_preferences(user_message, assistant_response)
    
    def _llm_extract_preferences(self, user_message: str, assistant_response: str):
        """Use LLM to extract preferences and facts from conversation."""
        prompt = f"""Analyze this conversation and extract any user preferences, facts, or information that should be remembered.

User: {user_message}
Assistant: {assistant_response}

Extract:
1. User preferences (tone, style, tools, etc.)
2. Facts about the user (job, location, interests, etc.)
3. Corrections the user made

Respond in JSON format:
{{
  "preferences": {{"key": "value"}},
  "facts": {{"key": "value"}},
  "corrections": ["correction1", "correction2"]
}}

If nothing to extract, return {{"preferences": {{}}, "facts": {{}}, "corrections": []}}

Respond with ONLY valid JSON, no other text:"""

        response = self.brain.generate_response(prompt)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                
                # Save preferences
                for key, value in data.get("preferences", {}).items():
                    self.memory.save_preference(key, str(value))
                
                # Save facts
                for key, value in data.get("facts", {}).items():
                    self.memory.save_fact(key, str(value))
        except (json.JSONDecodeError, KeyError, AttributeError):
            # Silently fail if JSON parsing fails or data structure is unexpected
            pass

