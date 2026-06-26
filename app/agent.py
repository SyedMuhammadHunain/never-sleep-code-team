import os
from typing import List, Dict
from pydantic import BaseModel
from google.adk.workflow import Workflow, START
from google.adk.agents import LlmAgent

FILE_SEQUENCE = [
    "PRD.md",
    "TechSpec.md",
    "AppFlow.md",
    "Design.md",
    "Schema.md",
    "ImplementationPlan.md",
    "Tracker.md",
    "Rules.md"
]

def _load_skill_rules() -> str:
    skill_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        ".agents", "skills", "not-a-vibe-coder", "SKILL.md"
    )
    
    if not os.path.exists(skill_path):
        raise FileNotFoundError(
            f"CRITICAL ERROR: Required skill file not found at {skill_path}. "
            "The agent cannot function without this skill."
        )
        
    with open(skill_path, "r") as skill_file:
        return skill_file.read()


class FileToWrite(BaseModel):
    filename: str
    content: str


class AgentResponse(BaseModel):
    files_to_write: List[FileToWrite]
    clarifying_questions: List[str]
    message_to_user: str


instruction = f"""You are the Requirement Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{_load_skill_rules()}
</SKILL_DOCUMENT>

Based on the user's task, generate ALL 8 required planning files exactly matching these names. You must provide the full content for each file in `files_to_write`:
{', '.join(FILE_SEQUENCE)}
"""

requirement_agent = LlmAgent(
    name="requirement_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)


OUTPUT_DIR = "planning_docs"

def abort_if_planning_files_exist():
    for file_name in FILE_SEQUENCE:
        file_path = os.path.join(OUTPUT_DIR, file_name)
        if os.path.exists(file_path):
            raise FileExistsError(f"Abort: Planning file {file_name} already exists in {OUTPUT_DIR}/. Start with a clean workspace.")


def process_agent_response(node_input) -> str:
    abort_if_planning_files_exist()
    
    # Handle the input being parsed as AgentResponse directly, or as a dictionary.
    response = node_input
    if isinstance(response, dict):
        response = AgentResponse(**response)
        
    if not isinstance(response, AgentResponse):
        return f"System Error: Expected AgentResponse, got {type(response)}"
        
    status_messages = []
    
    if response.files_to_write:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        for file_obj in response.files_to_write:
            file_path = os.path.join(OUTPUT_DIR, file_obj.filename)
            with open(file_path, "w") as file:
                file.write(file_obj.content)
            status_messages.append(f"Successfully created/updated: `{file_path}`")
            
    if response.clarifying_questions:
        status_messages.append("\nClarifying Questions:")
        for q in response.clarifying_questions:
            status_messages.append(f"- {q}")
            
    if response.message_to_user:
        status_messages.append(f"\nMessage: {response.message_to_user}")
        
    return "\n".join(status_messages)


root_agent = Workflow(
    name="never_sleep_code_team_workflow",
    edges=[
        (START, requirement_agent),
        (requirement_agent, process_agent_response)
    ],
    description="A workflow that takes a project idea and generates structured planning documents in sequence.",
)
