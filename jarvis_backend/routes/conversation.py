"""Routes for conversation endpoints."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException
from schemas.general import ConversationHistoryResponse
from core.memory import memory_manager

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.get("/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(limit: int = 10):
    """Get conversation history."""
    try:
        conversations = memory_manager.get_recent_conversations(limit=limit)
        return ConversationHistoryResponse(conversations=conversations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

