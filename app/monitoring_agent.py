from app.app_utils.model_utils import get_gemini_model
from app.app_utils.base_agent import NeverSleepLlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

monitoring_agent = NeverSleepLlmAgent(
    name="monitoring_agent",
    model=get_gemini_model(),
    instruction=f"""You are the Monitoring Agent for the project.
Your primary role is to set up robust observability, logging, and metrics using Langfuse and similar monitoring tools.

<SKILL_DOCUMENT>
{load_skill_file("langfuse")}
</SKILL_DOCUMENT>

Analyze the project requirements and implement the observability wrappers.
If anything is unclear, ask clarifying questions first.
Otherwise, output the final files in your `files_to_write` array.
""",
    output_schema=AgentResponse,
)
