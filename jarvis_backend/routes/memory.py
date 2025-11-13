"""Routes for memory endpoints."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException
from schemas.memory import (
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryItem,
    MemoryShowResponse,
    ConversationHistory
)
from schemas.general import MessageResponse
from core.memory import memory_manager

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/show", response_model=MemoryShowResponse)
async def show_memory():
    """Show memory contents."""
    try:
        prefs = memory_manager.get_all_preferences()
        conversations = memory_manager.get_recent_conversations(limit=10)
        
        conv_list = [
            ConversationHistory(
                user_message=c["user_message"],
                assistant_response=c["assistant_response"],
                intent=c.get("intent"),
                skills_used=c.get("skills_used", []),
                created_at=c["created_at"]
            )
            for c in conversations
        ]
        
        return MemoryShowResponse(
            preferences=prefs,
            conversations=conv_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(request: MemorySearchRequest):
    """Search semantic memory."""
    try:
        results = memory_manager.search_semantic_memory(
            request.query, 
            n_results=request.limit
        )
        
        memory_items = [
            MemoryItem(
                content=r["content"],
                metadata=r.get("metadata", {}),
                distance=r.get("distance")
            )
            for r in results
        ]
        
        return MemorySearchResponse(results=memory_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear", response_model=MessageResponse)
async def clear_memory():
    """Clear conversation history from session."""
    try:
        from core.brain import Brain
        brain = Brain()
        brain.clear_history()
        return MessageResponse(message="Conversation history cleared from session memory")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

