from google.adk.agents import LlmAgent, AgentConfig
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

monitoring_agent = LlmAgent(
    config=AgentConfig(
        name="Monitoring Agent",
        system_instruction=f"""You are the Monitoring Agent for the project.
Your primary role is to set up robust observability, logging, and metrics using Langfuse and similar monitoring tools.

{load_skill_file("langfuse")}

Analyze the project requirements and implement the observability wrappers.
If anything is unclear, ask clarifying questions first.
Otherwise, output the final files in your `files_to_write` array.
""",
        output_schema=AgentResponse,
    )
)
