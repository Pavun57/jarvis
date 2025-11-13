"""Routes for ask endpoint."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException, Depends
from schemas.ask import AskRequest, AskResponse
from core.brain import Brain
from core.intent import IntentExtractor
from core.planner import Planner
from core.memory import memory_manager
from core.personalization import Personalization
from core.skill_registry import SkillRegistry

router = APIRouter(prefix="/ask", tags=["ask"])

# Global instances (will be injected from server.py)
_brain = None
_intent_extractor = None
_planner = None
_personalization = None


def set_dependencies(brain: Brain, intent_extractor: IntentExtractor, 
                     planner: Planner, personalization: Personalization):
    """Set dependencies for this router."""
    global _brain, _intent_extractor, _planner, _personalization
    _brain = brain
    _intent_extractor = intent_extractor
    _planner = planner
    _personalization = personalization


def execute_plan(plan: list, user_message: str, brain: Brain) -> str:
    """Execute a plan and collect results."""
    from pathlib import Path
    skills_dir = Path(__file__).parent.parent / "skills"
    skill_registry = SkillRegistry(skills_dir)
    
    results = []
    skills_used = []
    
    for step in plan:
        skill_name = step.get("skill", "conversational")
        parameters = step.get("parameters", {})
        description = step.get("description", "")
        
        # Execute skill
        result = skill_registry.execute_skill(skill_name, parameters)
        skills_used.append(skill_name)
        results.append({
            "step": step.get("step", 0),
            "description": description,
            "result": result
        })
    
    # Combine results into a response
    if len(results) == 1 and results[0]["result"].get("success"):
        # Single step - return formatted result
        result = results[0]["result"]
        if "formatted" in result:
            return result["formatted"]
        elif "content" in result:
            return result["content"]
        elif "message" in result:
            return result["message"]
        elif "stdout" in result:
            return result["stdout"]
        else:
            return str(result)
    
    # Multiple steps - use LLM to combine
    results_text = "\n".join([
        f"Step {r['step']}: {r['description']}\nResult: {str(r['result'])}\n"
        for r in results
    ])
    
    prompt = f"""The user requested: "{user_message}"

I executed the following steps:
{results_text}

Provide a clear, concise summary of what was accomplished, combining all the results into a natural response."""
    
    response = brain.generate_response(prompt)
    return response


@router.post("", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Ask Jarvis a question or give a command."""
    global _brain, _intent_extractor, _planner, _personalization
    
    if not all([_brain, _intent_extractor, _planner, _personalization]):
        raise HTTPException(status_code=500, detail="Dependencies not initialized")
    
    try:
        # Load Jarvis identity
        jarvis_identity = load_jarvis_identity()
        
        # Get memory context
        memory_context = memory_manager.get_memory_context(request.query)
        personalization_context = _personalization.get_personalization_context()
        
        # Extract intent
        intent = _intent_extractor.extract_intent(request.query)
        
        # Create plan
        plan = _planner.plan(request.query, intent)
        
        # Execute plan
        if intent["intent"] == "conversational" or not plan:
            # Direct conversational response
            system_instruction = f"""You are Jarvis, an AI assistant. Here is your identity and purpose:

{jarvis_identity}

{personalization_context}

You have access to various skills and can help with tasks, answer questions, and have conversations.
Be helpful, concise, and friendly. Always remember who you are and your purpose."""
            
            context = memory_context if memory_context else None
            response = _brain.generate_response(
                request.query, 
                context=context, 
                system_instruction=system_instruction
            )
        else:
            # Execute skills
            response = execute_plan(plan, request.query, _brain)
        
        # Get skills used
        skills_used = [step.get("skill") for step in plan if step.get("skill")]
        
        # Save to memory
        memory_manager.save_conversation(
            user_message=request.query,
            assistant_response=response,
            intent=intent["intent"],
            skills_used=skills_used if skills_used else None
        )
        
        # Extract and save preferences
        _personalization.extract_and_save_preferences(request.query, response)
        
        # Add to brain history
        _brain.add_to_history(request.query, response)
        
        return AskResponse(
            response=response,
            intent=intent,
            plan=plan,
            skills_used=skills_used
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def load_jarvis_identity() -> str:
    """Load Jarvis identity from jarvis.md file."""
    try:
        jarvis_md_path = Path(__file__).parent.parent / "jarvis.md"
        if jarvis_md_path.exists():
            with open(jarvis_md_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    return "You are Jarvis, an AI assistant designed to help users."

