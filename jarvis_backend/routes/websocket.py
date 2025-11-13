"""WebSocket routes for real-time chat."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import WebSocket, WebSocketDisconnect
from core.brain import Brain
from core.intent import IntentExtractor
from core.planner import Planner
from core.memory import memory_manager
from core.personalization import Personalization
from core.skill_registry import SkillRegistry
from routes.ask import execute_plan, load_jarvis_identity


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    # Initialize components
    brain = Brain()
    intent_extractor = IntentExtractor(brain)
    personalization = Personalization(brain)
    skills_dir = Path(__file__).parent.parent / "skills"
    skill_registry = SkillRegistry(skills_dir)
    planner = Planner(brain, skill_registry.list_skills())
    jarvis_identity = load_jarvis_identity()
    
    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("query", "")
            
            if not query:
                await websocket.send_json({"error": "Query is required"})
                continue
            
            # Send processing status
            await websocket.send_json({"status": "processing", "message": "Thinking..."})
            
            # Get memory context
            memory_context = memory_manager.get_memory_context(query)
            personalization_context = personalization.get_personalization_context()
            
            # Extract intent
            intent = intent_extractor.extract_intent(query)
            await websocket.send_json({
                "status": "intent_extracted",
                "intent": intent
            })
            
            # Create plan
            plan = planner.plan(query, intent)
            await websocket.send_json({
                "status": "plan_created",
                "plan": plan
            })
            
            # Execute plan
            if intent["intent"] == "conversational" or not plan:
                system_instruction = f"""You are Jarvis, an AI assistant. Here is your identity and purpose:

{jarvis_identity}

{personalization_context}

You have access to various skills and can help with tasks, answer questions, and have conversations.
Be helpful, concise, and friendly. Always remember who you are and your purpose."""
                
                context = memory_context if memory_context else None
                response = brain.generate_response(
                    query, 
                    context=context, 
                    system_instruction=system_instruction
                )
            else:
                response = execute_plan(plan, query, brain)
            
            # Send final response
            skills_used = [step.get("skill") for step in plan if step.get("skill")]
            
            await websocket.send_json({
                "status": "complete",
                "response": response,
                "intent": intent,
                "skills_used": skills_used
            })
            
            # Save to memory
            memory_manager.save_conversation(
                user_message=query,
                assistant_response=response,
                intent=intent["intent"],
                skills_used=skills_used if skills_used else None
            )
            
            # Extract and save preferences
            personalization.extract_and_save_preferences(query, response)
            
            # Add to brain history
            brain.add_to_history(query, response)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})

