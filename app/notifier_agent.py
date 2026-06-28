from google.adk.agents import LlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

notifier_agent = LlmAgent(
    name="notifier_agent",
    model="gemini-flash-lite-latest",
    instruction=f"""You are the Notifier Agent for the project.
Your primary role is to implement email and notification systems using Gmail automation and other integrations.

<SKILL_DOCUMENT>
{load_skill_file("gmail-automation")}
</SKILL_DOCUMENT>

You will receive input detailing the project requirements. Implement the correct notification hooks.
If anything is unclear, ask clarifying questions first.
Otherwise, output the final files in your `files_to_write` array.
""",
    output_schema=AgentResponse,
)
