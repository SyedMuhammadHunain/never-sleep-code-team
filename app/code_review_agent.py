from app.app_utils.model_utils import get_gemini_model
from app.app_utils.base_agent import NeverSleepLlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

code_review_agent = NeverSleepLlmAgent(
    name="code_review_agent",
    model=get_gemini_model(),
    instruction=f"""You are the Code Review Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("code-reviewer")}
</SKILL_DOCUMENT>

You must act as the Code Review Agent, strictly follow the skill document to review the codebase.
Your output MUST include your review findings and suggestions. Generate these findings in comprehensive markdown files (e.g., `CodeReviewReport.md` or individual files for different areas) via the `files_to_write` array in your AgentResponse.
""",
    output_schema=AgentResponse,
)
