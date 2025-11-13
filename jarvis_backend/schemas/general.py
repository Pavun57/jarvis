"""General schemas."""
from pydantic import BaseModel
from typing import List, Dict, Any


class SkillInfo(BaseModel):
    """Schema for skill information."""
    name: str
    description: str


class SkillsResponse(BaseModel):
    """Response schema for skills list."""
    skills: List[SkillInfo]


class ConversationHistoryResponse(BaseModel):
    """Response schema for conversation history."""
    conversations: List[Dict[str, Any]]


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str

