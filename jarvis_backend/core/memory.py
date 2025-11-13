"""Memory management system using PostgreSQL and ChromaDB."""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, Field, Session, create_engine, select
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

# Add jarvis_backend to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


# SQLModel Definitions
class UserPreference(SQLModel, table=True):
    """Stores user preferences as key-value pairs."""
    __tablename__ = "user_preferences"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True)
    value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(SQLModel, table=True):
    """Stores conversation history."""
    __tablename__ = "conversation_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_message: str
    assistant_response: str
    intent: Optional[str] = None
    skills_used: Optional[str] = None  # JSON array of skill names
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserFact(SQLModel, table=True):
    """Stores factual information about the user."""
    __tablename__ = "user_facts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    fact_key: str = Field(index=True)
    fact_value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryManager:
    """Manages both structured (PostgreSQL) and semantic (ChromaDB) memory."""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL, echo=False)
        self._init_database()
        self._init_chroma()
    
    def _init_database(self):
        """Initialize PostgreSQL database tables."""
        SQLModel.metadata.create_all(self.engine)
    
    def _init_chroma(self):
        """Initialize ChromaDB for semantic memory."""
        Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.memory_collection = self.chroma_client.get_or_create_collection(
            name="semantic_memory",
            embedding_function=self.embedding_function
        )
    
    def save_preference(self, key: str, value: str):
        """Save or update a user preference."""
        with Session(self.engine) as session:
            existing = session.exec(
                select(UserPreference).where(UserPreference.key == key)
            ).first()
            
            if existing:
                existing.value = value
                existing.updated_at = datetime.utcnow()
            else:
                existing = UserPreference(key=key, value=value)
                session.add(existing)
            
            session.commit()
    
    def get_preference(self, key: str) -> Optional[str]:
        """Get a user preference by key."""
        with Session(self.engine) as session:
            pref = session.exec(
                select(UserPreference).where(UserPreference.key == key)
            ).first()
            return pref.value if pref else None
    
    def get_all_preferences(self) -> Dict[str, str]:
        """Get all user preferences as a dictionary."""
        with Session(self.engine) as session:
            prefs = session.exec(select(UserPreference)).all()
            return {p.key: p.value for p in prefs}
    
    def save_fact(self, fact_key: str, fact_value: str):
        """Save or update a user fact."""
        with Session(self.engine) as session:
            existing = session.exec(
                select(UserFact).where(UserFact.fact_key == fact_key)
            ).first()
            
            if existing:
                existing.fact_value = fact_value
                existing.updated_at = datetime.utcnow()
            else:
                existing = UserFact(fact_key=fact_key, fact_value=fact_value)
                session.add(existing)
            
            session.commit()
    
    def get_fact(self, fact_key: str) -> Optional[str]:
        """Get a user fact by key."""
        with Session(self.engine) as session:
            fact = session.exec(
                select(UserFact).where(UserFact.fact_key == fact_key)
            ).first()
            return fact.fact_value if fact else None
    
    def save_conversation(self, user_message: str, assistant_response: str, 
                         intent: Optional[str] = None, skills_used: Optional[List[str]] = None):
        """Save a conversation turn to history."""
        with Session(self.engine) as session:
            conv = ConversationHistory(
                user_message=user_message,
                assistant_response=assistant_response,
                intent=intent,
                skills_used=json.dumps(skills_used) if skills_used else None
            )
            session.add(conv)
            session.commit()
        
        # Also save to semantic memory
        conversation_text = f"User: {user_message}\nAssistant: {assistant_response}"
        self.memory_collection.add(
            documents=[conversation_text],
            metadatas=[{
                "intent": intent or "unknown",
                "timestamp": datetime.utcnow().isoformat(),
                "skills": json.dumps(skills_used) if skills_used else ""
            }],
            ids=[f"conv_{datetime.utcnow().timestamp()}"]
        )
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        with Session(self.engine) as session:
            convs = session.exec(
                select(ConversationHistory)
                .order_by(ConversationHistory.created_at.desc())
                .limit(limit)
            ).all()
            
            return [
                {
                    "user_message": c.user_message,
                    "assistant_response": c.assistant_response,
                    "intent": c.intent,
                    "skills_used": json.loads(c.skills_used) if c.skills_used else [],
                    "created_at": c.created_at.isoformat()
                }
                for c in reversed(convs)
            ]
    
    def search_semantic_memory(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search semantic memory using ChromaDB."""
        results = self.memory_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        memories = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                memories.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        return memories
    
    def get_memory_context(self, query: str) -> str:
        """Get relevant memory context for a query."""
        context_parts = []
        
        # Get relevant semantic memories
        semantic_memories = self.search_semantic_memory(query, n_results=3)
        if semantic_memories:
            context_parts.append("## Relevant Past Conversations:")
            for mem in semantic_memories:
                context_parts.append(f"- {mem['content']}")
        
        # Get user preferences
        prefs = self.get_all_preferences()
        if prefs:
            context_parts.append("\n## User Preferences:")
            for key, value in prefs.items():
                context_parts.append(f"- {key}: {value}")
        
        # Get recent conversation history
        recent = self.get_recent_conversations(limit=5)
        if recent:
            context_parts.append("\n## Recent Conversation History:")
            for conv in recent:
                context_parts.append(f"User: {conv['user_message']}")
                context_parts.append(f"Assistant: {conv['assistant_response']}")
        
        return "\n".join(context_parts) if context_parts else ""


# Global memory manager instance
memory_manager = MemoryManager()

