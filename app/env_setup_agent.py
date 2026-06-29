from app.app_utils.model_utils import get_gemini_model
from app.app_utils.base_agent import NeverSleepLlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

env_setup_agent = NeverSleepLlmAgent(
    name="env_setup_agent",
    model=get_gemini_model(),
    instruction=f"""You are the Environment Setup Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("mise-configurator")}
</SKILL_DOCUMENT>

Based on the generated project planning documents and specifications, you must detect the project context and generate a valid `mise.toml` configuration for local development.

You must strictly follow the rules in the SKILL_DOCUMENT.
Do not use floating `latest` tags unless explicitly requested.
Output the resulting `mise.toml` content via the `files_to_write` array in your AgentResponse.
""",
    output_schema=AgentResponse,
)
