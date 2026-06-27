from google.adk.agents import LlmAgent
from app.schemas import AgentResponse


from app.app_utils.skill_loader import load_skill_file


instruction = f"""You are the Coder Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("conductor-implement")}
</SKILL_DOCUMENT>

Based on the generated project planning documents, specifications, and the mise.toml configuration, you must execute tasks from the track's implementation plan following the TDD workflow and best practices.

You must strictly follow the rules in the SKILL_DOCUMENT.
Output the resulting implementation code or updated documents via the `files_to_write` array in your AgentResponse.
"""

coder_agent = LlmAgent(
    name="coder_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
