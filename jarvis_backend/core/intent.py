"""Intent extraction module."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Optional
from core.brain import Brain


class IntentExtractor:
    """Extracts user intent from messages."""
    
    def __init__(self, brain: Brain):
        self.brain = brain
    
    def extract_intent(self, message: str) -> Dict[str, any]:
        """Extract intent and parameters from user message."""
        # First try rule-based extraction
        intent = self._rule_based_extraction(message)
        
        # If unclear, use LLM to assist
        if intent["confidence"] < 0.7:
            intent = self._llm_assisted_extraction(message)
        
        return intent
    
    def _rule_based_extraction(self, message: str) -> Dict[str, any]:
        """Rule-based intent extraction."""
        message_lower = message.lower()
        
        # Open app intent
        if any(keyword in message_lower for keyword in ["open", "launch", "start"]):
            app_name = self._extract_app_name(message)
            if app_name:
                return {
                    "intent": "open_app",
                    "confidence": 0.9,
                    "parameters": {"app_name": app_name}
                }
        
        # Play intent - treat as YouTube search
        if "play" in message_lower:
            query = self._extract_search_query(message)
            return {
                "intent": "web_search",
                "confidence": 0.95,
                "parameters": {"query": query}
            }
        
        # Web search intent (including YouTube, Google, etc.)
        if any(keyword in message_lower for keyword in ["search", "find", "look up", "google", "youtube"]):
            query = self._extract_search_query(message)
            return {
                "intent": "web_search",
                "confidence": 0.9 if "youtube" in message_lower else 0.85,
                "parameters": {"query": query}
            }
        
        # Run command intent
        if any(keyword in message_lower for keyword in ["run", "execute", "command", "terminal"]):
            command = self._extract_command(message)
            if command:
                return {
                    "intent": "run_command",
                    "confidence": 0.9,
                    "parameters": {"command": command}
                }
        
        # Read file intent
        if any(keyword in message_lower for keyword in ["read", "show", "display", "file"]):
            file_path = self._extract_file_path(message)
            if file_path:
                return {
                    "intent": "read_file",
                    "confidence": 0.8,
                    "parameters": {"file_path": file_path}
                }
        
        # Default to conversational
        return {
            "intent": "conversational",
            "confidence": 0.5,
            "parameters": {}
        }
    
    def _llm_assisted_extraction(self, message: str) -> Dict[str, any]:
        """Use LLM to extract intent when rules are unclear."""
        prompt = f"""Analyze this user message and extract the intent and parameters.

User message: "{message}"

Respond in JSON format with:
- intent: one of ["open_app", "web_search", "run_command", "read_file", "conversational", "multi_step"]
- confidence: float between 0 and 1
- parameters: object with relevant parameters

Examples:
- "open vscode" -> {{"intent": "open_app", "confidence": 0.95, "parameters": {{"app_name": "vscode"}}}}
- "search python decorators" -> {{"intent": "web_search", "confidence": 0.95, "parameters": {{"query": "python decorators"}}}}
- "what's the weather?" -> {{"intent": "conversational", "confidence": 0.9, "parameters": {{}}}}

Respond with ONLY valid JSON, no other text:"""

        response = self.brain.generate_response(prompt)
        
        try:
            import json
            # Try to extract JSON from response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                intent_data = json.loads(response[json_start:json_end])
                return intent_data
        except:
            pass
        
        # Fallback
        return {
            "intent": "conversational",
            "confidence": 0.5,
            "parameters": {}
        }
    
    def _extract_app_name(self, message: str) -> Optional[str]:
        """Extract app name from message."""
        message_lower = message.lower()
        keywords = ["open", "launch", "start"]
        
        for keyword in keywords:
            if keyword in message_lower:
                parts = message_lower.split(keyword, 1)
                if len(parts) > 1:
                    # Get the text after the keyword
                    remaining = parts[1].strip()
                    
                    # Handle multi-word app names (e.g., "VS Code", "Visual Studio Code")
                    # Check for common app name patterns
                    app_patterns = {
                        "vs code": "vscode",
                        "visual studio code": "vscode",
                        "vs": "vscode",
                        "code": "vscode",
                    }
                    
                    # Check if remaining text starts with any known pattern
                    for pattern, app_name in app_patterns.items():
                        if remaining.startswith(pattern):
                            return app_name
                    
                    # Otherwise, get the first word or first few words
                    words = remaining.split()
                    if words:
                        # If first word is "the", "a", "an", skip it
                        if words[0] in ["the", "a", "an"] and len(words) > 1:
                            # Check if it's a multi-word app name
                            if len(words) >= 2:
                                # Check for "vs code" or "visual studio"
                                if words[0] == "vs" and words[1] == "code":
                                    return "vscode"
                                elif len(words) >= 3 and " ".join(words[:3]) == "visual studio code":
                                    return "vscode"
                                return " ".join(words[:2])  # Return first two words
                            return words[1]
                        else:
                            # Check if it's "vs code" pattern
                            if len(words) >= 2 and words[0] == "vs" and words[1] == "code":
                                return "vscode"
                            return words[0]
        
        return None
    
    def _extract_search_query(self, message: str) -> str:
        """Extract search query from message."""
        message_lower = message.lower()
        
        # Handle "play" commands - extract everything after "play"
        if "play" in message_lower:
            parts = message_lower.split("play", 1)
            if len(parts) > 1:
                return parts[1].strip()
        
        # Handle other search keywords
        keywords = ["search", "find", "look up", "google", "youtube"]
        
        for keyword in keywords:
            if keyword in message_lower:
                parts = message_lower.split(keyword, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return message
    
    def _extract_command(self, message: str) -> Optional[str]:
        """Extract command from message."""
        message_lower = message.lower()
        keywords = ["run", "execute", "command"]
        
        for keyword in keywords:
            if keyword in message_lower:
                parts = message_lower.split(keyword, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        # Check if message looks like a command
        if message.startswith("$") or message.startswith("`"):
            return message.strip("$`").strip()
        
        return None
    
    def _extract_file_path(self, message: str) -> Optional[str]:
        """Extract file path from message."""
        import re
        # Look for file paths (quoted or unquoted)
        patterns = [
            r'["\']([^"\']+\.(txt|py|json|md|yaml|yml|xml|html|css|js))["\']',
            r'\b([a-zA-Z]:[\\/][^\s]+\.\w+)',
            r'\b([./][^\s]+\.\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        
        return None

