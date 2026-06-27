import os
from google.adk.agents import LlmAgent
from app.schemas import AgentResponse


def _load_conductor_implement_skill() -> str:
    skill_path = os.path.expanduser("~/.agents/skills/conductor-implement/SKILL.md")

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


instruction = f"""You are the Coder Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{_load_conductor_implement_skill()}
</SKILL_DOCUMENT>

Based on the generated project planning documents, specifications, and the mise.toml configuration, you must execute tasks from the track's implementation plan following the TDD workflow and best practices.

You must strictly follow the rules in the SKILL_DOCUMENT.
Output the resulting implementation code or updated documents via the `files_to_write` array in your AgentResponse.
"""

coder_agent = LlmAgent(
    name="coder_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
