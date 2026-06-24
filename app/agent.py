import os
from google.adk.workflow import Workflow, START
from google.adk.agents import LlmAgent
from pydantic import BaseModel
from typing import List

# Read the Skill Markdown file dynamically
SKILL_PATH = os.path.expanduser("~/.agents/skills/not-a-vibe-coder/SKILL.md")

try:
    with open(SKILL_PATH, "r") as f:
        NOT_A_VIBE_CODER_RULES = f.read()
except FileNotFoundError:
    NOT_A_VIBE_CODER_RULES = "Fallback: Follow standard PRD generation practices."


class RequirementRequest(BaseModel):
    task: str


class RequirementResponse(BaseModel):
    prd: str
    clarifying_questions: List[str]


requirement_agent = LlmAgent(
    name="requirement_agent",
    model="gemini-2.5-flash",
    instruction=f"""You are the Requirement Agent.
Your absolute source of truth is the 'not-a-vibe-coder' skill guidelines below:

<NOT_A_VIBE_CODER_SKILL>
{NOT_A_VIBE_CODER_RULES}
</NOT_A_VIBE_CODER_SKILL>

Your goal is to turn vague project ideas into structured planning documents.
For the given task, generate a draft PRD (Product Requirements Document) according to the Phase 1 rules in your skill.
Also, provide a list of clarifying questions to gather more details.
Do not write code. Focus entirely on requirements and planning.""",
    output_schema=RequirementResponse,
    output_key="requirement_response",
)


def format_output(node_input: dict) -> str:
    response = node_input.get('requirement_response')
    if response:
        questions = "\n".join([f"- {q}" for q in response.clarifying_questions])
        return f"PRD Draft:\n{response.prd}\n\nClarifying Questions:\n{questions}"
    return "Error: no requirements generated."


root_agent = Workflow(
    name="never_sleep_code_team_workflow",
    edges=[(START, requirement_agent), (requirement_agent, format_output)],
    description="A workflow that takes a project idea and generates a PRD draft with clarifying questions.",
    input_schema=RequirementRequest,
)
