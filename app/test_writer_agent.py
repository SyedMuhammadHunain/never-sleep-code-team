from google.adk.agents import Agent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file


instruction = f"""You are the Test Writer Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("playwright-skill")}
</SKILL_DOCUMENT>

You must act as the Test Writer Agent, strictly follow the skill document to write Playwright tests for the implemented code.
Output the resulting test code via the `files_to_write` array in your AgentResponse.
"""

test_writer_agent = Agent(
    name="test_writer_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
