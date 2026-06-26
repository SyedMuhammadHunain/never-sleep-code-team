import os
from typing import List, Dict
from pydantic import BaseModel
from google.adk.workflow import Workflow, START
from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.tools._request_input_tool import request_input as human_input

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
_is_first_pass = True
_original_task = None

def store_task_node(node_input):
    global _original_task
    # Keep original task for later steps if needed
    _original_task = getattr(node_input, 'text', str(node_input))
    return node_input


def abort_if_planning_files_exist():
    for file_name in FILE_SEQUENCE:
        file_path = os.path.join(OUTPUT_DIR, file_name)
        if os.path.exists(file_path):
            raise FileExistsError(f"Abort: Planning file {file_name} already exists in {OUTPUT_DIR}/. Start with a clean workspace.")


def process_agent_response(node_input) -> Event:
    global _is_first_pass
    is_initial_run = _is_first_pass
    
    if _is_first_pass:
        abort_if_planning_files_exist()
        _is_first_pass = False
    
    # Handle the input being parsed as AgentResponse directly, or as a dictionary.
    response = node_input
    if isinstance(response, dict):
        response = AgentResponse(**response)
        
    if not isinstance(response, AgentResponse):
        return Event(output=f"System Error: Expected AgentResponse, got {type(response)}", route="done")
        
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

    if is_initial_run and response.clarifying_questions:
        status_messages.append("\nEntering Q&A Phase to collect your answers...")
        questions_text = "Please answer the following clarifying questions:\n"
        questions_text += "\n".join([f"{i+1}. {q}" for i, q in enumerate(response.clarifying_questions)])
        
        # Route to the QA agent to ask these questions one by one
        return Event(
            output=questions_text,
            route="ask_questions"
        )
        
    # If no [Awaiting] or no questions, we are done
    return Event(
        output="\n".join(status_messages),
        route="done"
    )

qa_agent = LlmAgent(
    name="qa_agent",
    model="gemini-flash-lite-latest",
    instruction="""You are a QA Agent. You will receive a list of clarifying questions.
Your task is to ask the user EVERY question on the list ONE BY ONE using the `human_input` tool.

CRITICAL RULES:
1. NEVER ask a question that you have already asked. Always check your conversation history to see which questions have already been answered.
2. Ask exactly ONE question at a time using the `human_input` tool.
3. Wait for the `human_input` tool to return the user's answer before asking the next question.
4. Once ALL questions from the list have been answered by the user, DO NOT call the tool anymore. Instead, output a clear summary of all the Q&A pairs.""",
    tools=[human_input],
)

def format_update_prompt(node_input):
    qa_pairs = node_input
    return f"""Original task: {_original_task}

Based on the original task, you previously generated the planning files.
Here are the user's answers to the clarifying questions:
{qa_pairs}

Instruction: Now update Design.md with these answers.
You must return the full updated Design.md file in your `files_to_write` array.
Ensure all `[Awaiting]` placeholders are replaced with the concrete details provided by the user.
"""

root_agent = Workflow(
    name="never_sleep_code_team_workflow",
    edges=[
        (START, store_task_node),
        (store_task_node, requirement_agent),
        (requirement_agent, process_agent_response),
        (process_agent_response, {"ask_questions": qa_agent}),
        (qa_agent, format_update_prompt),
        (format_update_prompt, requirement_agent)
    ],
    description="A workflow that takes a project idea and generates structured planning documents in sequence.",
)
