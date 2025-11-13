"""Schemas for ask endpoint."""
from pydantic import BaseModel
from typing import Dict, Any, List


class AskRequest(BaseModel):
    """Request schema for asking questions."""
    query: str
    verbose: bool = False


class AskResponse(BaseModel):
    """Response schema for ask endpoint."""
    response: str
    intent: Dict[str, Any]
    plan: List[Dict[str, Any]]
    skills_used: List[str]

