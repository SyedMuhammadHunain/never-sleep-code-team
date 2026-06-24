from google.adk.workflow import Workflow, START
from google.adk.agents import LlmAgent
from pydantic import BaseModel


class CodeRequest(BaseModel):
    task: str


class CodeResponse(BaseModel):
    code: str
    explanation: str


coder = LlmAgent(
    name="coder",
    model="gemini-2.5-flash",
    instruction="You are an expert coder. Write code for the requested task.",
    output_schema=CodeResponse,
    output_key="code_response",
)


def format_output(node_input: dict) -> str:
    return f"Code:\n{node_input.get('code')}\n\nExplanation:\n{node_input.get('explanation')}"


root_agent = Workflow(
    name="never_sleep_code_team_workflow",
    edges=[(START, coder), (coder, format_output)],
    description="A graph workflow that takes a coding task and generates code.",
    input_schema=CodeRequest,
)
