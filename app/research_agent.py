from google.adk.agents import LlmAgent, AgentConfig
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

research_agent = LlmAgent(
    config=AgentConfig(
        name="Research Agent",
        system_instruction=f"""You are the Research Agent for the project.
Your primary role is to research advanced topics, APIs, or libraries required by the project and produce documented research notes.

{load_skill_file("agent-reach")}

Read the current state of the project, perform the necessary external research, and compile comprehensive notes.
If anything is unclear, ask clarifying questions first.
Otherwise, output the final notes in your `files_to_write` array.
""",
        output_schema=AgentResponse,
    )
)
