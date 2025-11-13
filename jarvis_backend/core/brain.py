"""Gemini LLM brain for Jarvis."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

import google.generativeai as genai
from typing import List, Dict, Optional
from config.settings import settings


class Brain:
    """Main LLM interface using Google Gemini."""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.conversation_history: List[Dict[str, str]] = []
    
    def generate_response(self, prompt: str, context: Optional[str] = None, 
                         system_instruction: Optional[str] = None) -> str:
        """Generate a response from the LLM."""
        full_prompt = self._build_prompt(prompt, context, system_instruction)
        
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": settings.TEMPERATURE,
                    "max_output_tokens": settings.MAX_TOKENS,
                }
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None,
                     system_instruction: Optional[str] = None) -> str:
        """Build the full prompt with context and system instructions."""
        parts = []
        
        if system_instruction:
            parts.append(f"System Instructions:\n{system_instruction}\n")
        
        if context:
            parts.append(f"Context:\n{context}\n")
        
        # Add recent conversation history
        if self.conversation_history:
            parts.append("Recent Conversation:")
            for msg in self.conversation_history[-5:]:  # Last 5 turns
                parts.append(f"{msg['role']}: {msg['content']}")
            parts.append("")
        
        parts.append(f"User: {prompt}")
        parts.append("Assistant:")
        
        return "\n".join(parts)
    
    def add_to_history(self, user_message: str, assistant_response: str):
        """Add a conversation turn to history."""
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # Keep history within limit
        if len(self.conversation_history) > settings.MAX_CONVERSATION_HISTORY:
            self.conversation_history = self.conversation_history[-settings.MAX_CONVERSATION_HISTORY:]
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

