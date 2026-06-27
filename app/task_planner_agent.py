import os
from google.adk.agents import LlmAgent
from app.schemas import AgentResponse


def _load_conductor_new_track_skill() -> str:
    skill_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        ".agents", "skills", "conductor-new-track", "SKILL.md"
    )
    
    if not os.path.exists(skill_path):
        raise FileNotFoundError(
            f"CRITICAL ERROR: Required skill file not found at {skill_path}. "
            "The agent cannot function without this skill."
        )
        
    with open(skill_path, "r") as skill_file:
        content = skill_file.read()
        # Escape curly braces for ADK template engine by replacing them with brackets
        content = content.replace("{", "[").replace("}", "]")
        return content


instruction = f"""You are the Task Planner Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{_load_conductor_new_track_skill()}
</SKILL_DOCUMENT>

Based on the generated architecture and UI/UX design documents, break down the project into a step-by-step implementation plan. Define the explicit tasks that need to be completed by the engineering team.

You must provide the full content for the generated task plan file (e.g., TaskPlan.md) in `files_to_write`.

CRITICAL INSTRUCTIONS:
1. Ensure the tasks follow a logical order, starting from project setup, backend foundation, to frontend implementation.
2. Ensure each task is atomic and has a clear definition of done.
"""

task_planner_agent = LlmAgent(
    name="task_planner_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
