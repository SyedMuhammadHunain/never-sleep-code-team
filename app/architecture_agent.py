import os
from typing import List

from pydantic import BaseModel
from google.adk.agents import LlmAgent

OUTPUT_DIR = "planning_docs"


def _load_software_architecture_skill() -> str:
    """Loads the core instructions from the software-architecture skill file."""
    skill_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        ".agents", "skills", "software-architecture", "SKILL.md"
    )
    
    if not os.path.exists(skill_path):
        raise FileNotFoundError(
            f"CRITICAL ERROR: Required skill file not found at {skill_path}. "
            "The agent cannot function without this skill."
        )
        
    with open(skill_path, "r") as skill_file:
        return skill_file.read()


class FileToWrite(BaseModel):
    filename: str
    content: str


class AgentResponse(BaseModel):
    files_to_write: List[FileToWrite]
    clarifying_questions: List[str]
    message_to_user: str


instruction = f"""You are the Architecture Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{_load_software_architecture_skill()}
</SKILL_DOCUMENT>

Based on the user's task and the existing planning documents (e.g., PRD.md, TechSpec.md), design a robust architecture. You must provide the full content for the generated architecture file (e.g., Architecture.md) in `files_to_write`.
"""

architecture_agent = LlmAgent(
    name="architecture_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
