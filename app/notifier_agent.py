from google.adk.agents import LlmAgent, AgentConfig
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

notifier_agent = LlmAgent(
    config=AgentConfig(
        name="Notifier Agent",
        system_instruction=f"""You are the Notifier Agent for the project.
Your primary role is to implement email and notification systems using Gmail automation and other integrations.

{load_skill_file("gmail-automation")}

You will receive input detailing the project requirements. Implement the correct notification hooks.
If anything is unclear, ask clarifying questions first.
Otherwise, output the final files in your `files_to_write` array.
""",
        output_schema=AgentResponse,
    )
)
