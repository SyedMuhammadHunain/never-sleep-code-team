import os
from google.adk.agents import LlmAgent
from app.schemas import AgentResponse


def _load_mise_configurator_skill() -> str:
    skill_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        ".agents",
        "skills",
        "mise-configurator",
        "SKILL.md",
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


instruction = f"""You are the Environment Setup Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{_load_mise_configurator_skill()}
</SKILL_DOCUMENT>

Based on the generated project planning documents and specifications, you must detect the project context and generate a valid `mise.toml` configuration for local development.

You must strictly follow the rules in the SKILL_DOCUMENT.
Do not use floating `latest` tags unless explicitly requested.
Output the resulting `mise.toml` content via the `files_to_write` array in your AgentResponse.
"""

env_setup_agent = LlmAgent(
    name="env_setup_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
