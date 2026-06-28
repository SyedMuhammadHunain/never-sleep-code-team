from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor

from app.app_utils.skill_loader import load_skill_file
from app.schemas import AgentResponse

research_agent = LlmAgent(
    name="research_agent",
    model="gemini-flash-lite-latest",
    code_executor=BuiltInCodeExecutor(),
    instruction=f"""You are the Research Agent for the project.
Your primary role is to research advanced topics, APIs, or libraries required by the project and produce documented research notes.

<SKILL_DOCUMENT>
{load_skill_file("agent-reach")}
</SKILL_DOCUMENT>

Read the current state of the project, perform the necessary external research using your code execution capabilities to run agent-reach commands, and compile comprehensive notes.
If anything is unclear, ask clarifying questions first.

CRITICAL: You must execute the commands described in the agent-reach skill (e.g., agent-reach doctor --json) to fetch real internet content. Do not hallucinate research.

Once you have completed the research, you MUST output a final JSON block wrapped in ```json that strictly matches the following schema:
{{
  "files_to_write": [
    {{"filename": "string", "content": "string"}}
  ],
  "clarifying_questions": ["string"],
  "message_to_user": "string"
}}

To perfectly align with the agent-reach skill, ensure your `message_to_user` starts with: "using agent-reach, platform X via backend Y" and ends with any required version update announcements.
""",
    output_schema=AgentResponse,
)
