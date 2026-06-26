import os
from typing import List, Dict

from pydantic import BaseModel
from google.adk.workflow import Workflow, START
from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.events.request_input import RequestInput

OUTPUT_DIR = "planning_docs"

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
    """Loads the core instructions from the not-a-vibe-coder skill file."""
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


def store_task_node(ctx, node_input):
    ctx.state["original_task"] = getattr(node_input, 'text', str(node_input))
    ctx.state["is_first_pass"] = True
    ctx.state["pending_questions"] = []
    ctx.state["qa_pairs"] = {}
    return node_input


def _abort_if_planning_files_exist():
    """Ensures we do not overwrite existing files on the first run."""
    for file_name in FILE_SEQUENCE:
        file_path = os.path.join(OUTPUT_DIR, file_name)
        if os.path.exists(file_path):
            raise FileExistsError(
                f"Abort: Planning file {file_name} already exists in {OUTPUT_DIR}/. "
                "Start with a clean workspace."
            )


def _parse_agent_response(node_input) -> AgentResponse:
    if isinstance(node_input, dict):
        return AgentResponse(**node_input)
    return node_input


def _save_planning_files(files_to_write: List[FileToWrite]) -> List[str]:
    """Saves generated planning files to disk and returns success messages."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    messages = []
    
    for file_obj in files_to_write:
        file_path = os.path.join(OUTPUT_DIR, file_obj.filename)
        with open(file_path, "w") as file:
            file.write(file_obj.content)
        messages.append(f"Successfully created/updated: `{file_path}`")
        
    return messages


def _build_status_messages(response: AgentResponse, file_messages: List[str]) -> List[str]:
    """Compiles status messages including file creations, questions, and agent messages."""
    messages = list(file_messages)
    
    if response.clarifying_questions:
        messages.append("\nClarifying Questions:")
        messages.extend(f"- {q}" for q in response.clarifying_questions)
            
    if response.message_to_user:
        messages.append(f"\nMessage: {response.message_to_user}")
        
    return messages


def process_agent_response(ctx, node_input) -> Event:
    is_initial_run = ctx.state.get("is_first_pass", True)
    
    if is_initial_run:
        _abort_if_planning_files_exist()
        ctx.state["is_first_pass"] = False
    
    response = _parse_agent_response(node_input)
    if not isinstance(response, AgentResponse):
        return Event(output=f"System Error: Expected AgentResponse, got {type(response)}", route="done")
        
    file_messages = _save_planning_files(response.files_to_write) if response.files_to_write else []
    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and response.clarifying_questions:
        ctx.state["pending_questions"] = response.clarifying_questions.copy()
        status_messages.append("\nEntering Q&A Phase to collect your answers...")
        return Event(output="\n".join(status_messages), route="ask_questions")
        
    return Event(output="\n".join(status_messages), route="done")


def ask_questions_node(ctx, node_input):
    pending_questions = ctx.state.get("pending_questions", [])
    
    if not pending_questions:
        return Event(output=None, route="finished")
        
    current_question = pending_questions[0]
    ctx.state["current_question"] = current_question
    
    return RequestInput(message=current_question)


def save_answer_node(ctx, node_input):
    answer = getattr(node_input, 'text', str(node_input))
    current_question = ctx.state.get("current_question")
    
    qa_pairs = ctx.state.get("qa_pairs", {})
    qa_pairs[current_question] = answer
    ctx.state["qa_pairs"] = qa_pairs
    
    pending_questions = ctx.state.get("pending_questions", [])
    if pending_questions:
        pending_questions.pop(0)
    ctx.state["pending_questions"] = pending_questions
    
    if pending_questions:
        return Event(output=None, route="ask_more")
    
    return Event(output=qa_pairs, route="finished")


def format_update_prompt(ctx, node_input):
    qa_pairs = node_input
    original_task = ctx.state.get("original_task", "")
    
    formatted_qa = "".join(
        f"Q: {q}\nA: {a}\n\n" 
        for q, a in qa_pairs.items()
    )
        
    return f"""Original task: {original_task}

Based on the original task, you previously generated the planning files.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update Design.md with these answers.
You must return the full updated Design.md file in your `files_to_write` array.
Ensure that the Design.md file is updated on the disk based on the new inputs from the user.
"""


root_agent = Workflow(
    name="never_sleep_code_team_workflow",
    edges=[
        (START, store_task_node),
        (store_task_node, requirement_agent),
        (requirement_agent, process_agent_response),
        (process_agent_response, {"ask_questions": ask_questions_node}),
        (ask_questions_node, save_answer_node),
        (save_answer_node, {"ask_more": ask_questions_node, "finished": format_update_prompt}),
        (format_update_prompt, requirement_agent)
    ],
    description="A workflow that takes a project idea and generates structured planning documents in sequence.",
)
