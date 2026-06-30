from app.app_utils.model_utils import get_gemini_model
from app.app_utils.base_agent import NeverSleepLlmAgent

from app.app_utils.skill_loader import load_skill_file


def execute_shell_command(command: str) -> str:
    """Execute a shell command such as agent-reach, curl, or gh to perform internet research."""
    import subprocess
    import shlex

    try:
        args = shlex.split(command)
        return subprocess.check_output(
            args, shell=False, text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        return f"Command failed with exit code {e.returncode}:\n{e.output}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


research_agent = NeverSleepLlmAgent(
    name="research_agent",
    model=get_gemini_model(),
    tools=[execute_shell_command],
    instruction=f"""You are the Research Agent for the project.
Your primary role is to research advanced topics, APIs, or libraries required by the project and produce documented research notes.

<SKILL_DOCUMENT>
{load_skill_file("agent-reach")}
</SKILL_DOCUMENT>

Read the current state of the project, perform the necessary external research using the `execute_shell_command` tool to run agent-reach commands, and compile comprehensive notes.
If anything is unclear, ask clarifying questions first.

CRITICAL: You must use the `execute_shell_command` tool to fetch real internet content. Do NOT write Python code. Just call the tool with commands like `agent-reach doctor --json` or `curl -s "https://r.jina.ai/URL"`.
Do not hallucinate research.

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
)
