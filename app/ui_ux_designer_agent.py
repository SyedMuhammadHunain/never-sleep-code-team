import os
from google.adk.agents import LlmAgent
from app.schemas import AgentResponse


def _load_ui_ux_skill() -> str:
    skill_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        ".agents", "skills", "ui-ux-designer", "SKILL.md"
    )
    
    if not os.path.exists(skill_path):
        return "You are the UI/UX Designer Agent. Focus on creating beautiful, accessible, and user-friendly interfaces."
        
    with open(skill_path, "r") as skill_file:
        return skill_file.read()


instruction = f"""You are the UI/UX Designer Agent.

<SKILL_DOCUMENT>
{_load_ui_ux_skill()}
</SKILL_DOCUMENT>

Based on the generated planning and architecture documents (e.g., PRD.md, Architecture.md), design the UI/UX specifications, wireframes, or component breakdown. You must provide the full content for the generated design file (e.g., UI_UX_Design.md) in `files_to_write`.
"""

ui_ux_designer_agent = LlmAgent(
    name="ui_ux_designer_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
