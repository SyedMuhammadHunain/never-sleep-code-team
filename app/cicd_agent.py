from google.adk.agents import LlmAgent, AgentConfig
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

cicd_agent = LlmAgent(
    config=AgentConfig(
        name="CI/CD Agent",
        system_instruction=f"""You are the CI/CD Agent for the project.
Your primary role is to set up CI/CD workflows and GitHub Actions templates based on the current architecture and project state.

{load_skill_file("github-actions-templates")}

You will receive input containing the previous architectural and code planning. You must read it, understand the project stack, and output the required CI/CD workflow files.
If anything is unclear, ask clarifying questions first.
Otherwise, output the final files in your `files_to_write` array.
""",
        output_schema=AgentResponse,
    )
)
