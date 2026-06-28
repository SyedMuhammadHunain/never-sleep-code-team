from google.adk.agents import LlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file


instruction = f"""You are the Debugger Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("debugger")}
</SKILL_DOCUMENT>

You must act as the Debugger Agent, strictly follow the skill document to diagnose and debug code, and output the fixed code via the `files_to_write` array in your AgentResponse.
"""

debugger_agent = LlmAgent(
    name="debugger_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
