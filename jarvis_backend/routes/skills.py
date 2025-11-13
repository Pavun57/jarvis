"""Routes for skills endpoint."""
import sys
from pathlib import Path

# Add jarvis_cli to path for imports
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException
from schemas.general import SkillsResponse, SkillInfo
from core.skill_registry import SkillRegistry

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=SkillsResponse)
async def list_skills():
    """List all available skills."""
    try:
        skills_dir = Path(__file__).parent.parent / "skills"
        skill_registry = SkillRegistry(skills_dir)
        skill_list = skill_registry.list_skills()
        skills_info = []
        
        for skill_name in skill_list:
            skill = skill_registry.get_skill(skill_name)
            if skill:
                skills_info.append(
                    SkillInfo(
                        name=skill_name,
                        description=skill.description
                    )
                )
        
        return SkillsResponse(skills=skills_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

