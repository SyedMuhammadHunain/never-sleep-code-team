from app.app_utils.model_utils import get_gemini_model
from google.adk.agents import LlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

cicd_agent = LlmAgent(
    name="cicd_agent",
    model=get_gemini_model(),
    instruction=f"""You are the CI/CD Agent for the project.
Your primary role is to set up CI/CD workflows and GitHub Actions templates based on the current architecture and project state.

<SKILL_DOCUMENT>
{load_skill_file("github-actions-templates")}
</SKILL_DOCUMENT>

You will receive input containing the previous architectural and code planning. You must read it, understand the project stack, and output the required CI/CD workflow files.
If anything is unclear, ask clarifying questions first.
Otherwise, output the final files in your `files_to_write` array.
""",
    output_schema=AgentResponse,
)
