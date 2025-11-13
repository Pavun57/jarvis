"""FastAPI server for Jarvis CLI."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.brain import Brain
from core.intent import IntentExtractor
from core.planner import Planner
from core.memory import memory_manager
from core.personalization import Personalization
from core.skill_registry import SkillRegistry
from routes import ask, memory, skills, conversation, websocket

app = FastAPI(title="Jarvis API", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
brain = Brain()
intent_extractor = IntentExtractor(brain)
personalization = Personalization(brain)
skills_dir = Path(__file__).parent / "skills"
skill_registry = SkillRegistry(skills_dir)
planner = Planner(brain, skill_registry.list_skills())


# Dependency injection for routes
def get_brain() -> Brain:
    return brain


def get_intent_extractor() -> IntentExtractor:
    return intent_extractor


def get_planner() -> Planner:
    return planner


def get_personalization() -> Personalization:
    return personalization


# Set dependencies for ask router
ask.set_dependencies(brain, intent_extractor, planner, personalization)

# Include routers
app.include_router(ask.router)
app.include_router(memory.router)
app.include_router(skills.router)
app.include_router(conversation.router)

# WebSocket route
app.add_websocket_route("/ws", websocket.websocket_endpoint)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Jarvis API Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
