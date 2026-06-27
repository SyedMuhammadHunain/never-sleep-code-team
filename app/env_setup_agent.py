from google.adk.agents import LlmAgent
from app.schemas import AgentResponse


from app.app_utils.skill_loader import load_skill_file


instruction = f"""You are the Environment Setup Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("mise-configurator")}
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
