"""Schemas for memory endpoints."""
from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class MemorySearchRequest(BaseModel):
    """Request schema for memory search."""
    query: str
    limit: int = 5


class MemoryItem(BaseModel):
    """Schema for a memory item."""
    content: str
    metadata: Dict[str, Any]
    distance: Optional[float] = None


class MemorySearchResponse(BaseModel):
    """Response schema for memory search."""
    results: List[MemoryItem]


class ConversationHistory(BaseModel):
    """Schema for conversation history item."""
    user_message: str
    assistant_response: str
    intent: Optional[str]
    skills_used: List[str]
    created_at: str


class MemoryShowResponse(BaseModel):
    """Response schema for memory show."""
    preferences: Dict[str, str]
    conversations: List[ConversationHistory]

