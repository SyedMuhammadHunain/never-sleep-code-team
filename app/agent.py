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
_pending_questions: List[str] = []
_qa_pairs: Dict[str, str] = {}
_current_question: str = ""

def store_task_node(node_input):
    global _original_task, _is_first_pass, _pending_questions, _qa_pairs
    # Keep original task for later steps if needed
    _original_task = getattr(node_input, 'text', str(node_input))
    _is_first_pass = True
    _pending_questions.clear()
    _qa_pairs.clear()
    return node_input


def abort_if_planning_files_exist():
    for file_name in FILE_SEQUENCE:
        file_path = os.path.join(OUTPUT_DIR, file_name)
        if os.path.exists(file_path):
            raise FileExistsError(f"Abort: Planning file {file_name} already exists in {OUTPUT_DIR}/. Start with a clean workspace.")


def process_agent_response(node_input) -> Event:
    global _is_first_pass, _pending_questions
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
        _pending_questions = response.clarifying_questions
        status_messages.append("\nEntering Q&A Phase to collect your answers...")
        return Event(
            output="\n".join(status_messages),
            route="ask_questions"
        )
        
    # If no [Awaiting] or no questions, we are done
    return Event(
        output="\n".join(status_messages),
        route="done"
    )


def ask_questions_node(node_input):
    from google.adk.events import RequestInput
    global _pending_questions, _current_question
    
    if not _pending_questions:
        return Event(output=None, route="finished")
        
    _current_question = _pending_questions[0]
    return RequestInput(message=_current_question)

def save_answer_node(node_input):
    from google.adk.events import Event
    global _pending_questions, _qa_pairs, _current_question
    
    # The node_input is the user's answer from the UI
    answer = getattr(node_input, 'text', str(node_input))
    _qa_pairs[_current_question] = answer
    
    _pending_questions.pop(0)
    
    if _pending_questions:
        return Event(output=None, route="ask_more")
    else:
        return Event(output=_qa_pairs, route="finished")


def format_update_prompt(node_input):
    qa_pairs = node_input
    
    formatted_qa = ""
    for q, a in qa_pairs.items():
        formatted_qa += f"Q: {q}\nA: {a}\n\n"
        
    return f"""Original task: {_original_task}

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
