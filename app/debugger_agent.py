from app.app_utils.model_utils import get_gemini_model
from app.app_utils.base_agent import NeverSleepLlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

debugger_agent = NeverSleepLlmAgent(
    name="debugger_agent",
    model=get_gemini_model(),
    instruction=f"""You are the Debugger Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("debugger")}
</SKILL_DOCUMENT>

You must act as the Debugger Agent, strictly follow the skill document to diagnose and debug code, and output the fixed code via the `files_to_write` array in your AgentResponse.
""",
    output_schema=AgentResponse,
)
