from app.app_utils.model_utils import get_gemini_model
from app.app_utils.base_agent import NeverSleepLlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

performance_agent = NeverSleepLlmAgent(
    name="performance_agent",
    model=get_gemini_model(),
    instruction=f"""You are the Performance Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("performance-engineer")}
</SKILL_DOCUMENT>

You must act as the Performance Agent, strictly follow the skill document to audit and optimize the codebase for performance.
Your output MUST include your findings and optimization proposals. Generate these findings in comprehensive markdown files (e.g., `PerformanceReport.md` or individual files for different areas) via the `files_to_write` array in your AgentResponse.
""",
    output_schema=AgentResponse,
)
