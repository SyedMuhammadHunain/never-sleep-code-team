import os
from typing import List, Dict

from pydantic import BaseModel
from google.adk.workflow import Workflow, START
from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.events.request_input import RequestInput
from app.architecture_agent import architecture_agent
from app.ui_ux_designer_agent import ui_ux_designer_agent
from app.task_planner_agent import task_planner_agent
from app.schemas import FileToWrite, AgentResponse
REQ_OUTPUT_DIR = "Output/requirement_agent_output_files"
ARCH_OUTPUT_DIR = "Output/Architecture_output_files"
UI_UX_OUTPUT_DIR = "Output/ui_ux_designer_output_files"
TASK_PLAN_OUTPUT_DIR = "Output/task_planner_output_files"

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
        content = skill_file.read()
        return content.replace("{", "[").replace("}", "]")


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


def _parse_agent_response(node_input) -> AgentResponse:
    if isinstance(node_input, dict):
        return AgentResponse(**node_input)
    return node_input


def _save_planning_files(files_to_write: List[FileToWrite], output_dir: str) -> List[str]:
    """Saves generated files to disk in the specified output directory and returns success messages."""
    os.makedirs(output_dir, exist_ok=True)
    messages = []
    
    for file_obj in files_to_write:
        file_path = os.path.join(output_dir, file_obj.filename)
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
        ctx.state["is_first_pass"] = False
    
    response = _parse_agent_response(node_input)
    if not isinstance(response, AgentResponse):
        return Event(output=f"System Error: Expected AgentResponse, got {type(response)}", route="done")
        
    file_messages = _save_planning_files(response.files_to_write, REQ_OUTPUT_DIR) if response.files_to_write else []
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


def prepare_architecture_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = ""
    
    for filename in FILE_SEQUENCE:
        filepath = os.path.join(REQ_OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                planning_docs += f"--- {filename} ---\n{f.read()}\n\n"
    
    prompt = f"Original User Task: {original_task}\n\nThe requirement phase is now complete. Below are the generated planning documents:\n\n{planning_docs}\n\nPlease generate the software architecture and save it via `files_to_write`."
    return prompt


def process_arch_response(ctx, node_input) -> Event:
    if isinstance(node_input, dict):
        response = AgentResponse(**node_input)
    else:
        response = node_input
        
    if not hasattr(response, 'files_to_write'):
        return Event(output=f"System Error: Expected AgentResponse, got {type(response)}")
        
    file_messages = _save_planning_files(response.files_to_write, ARCH_OUTPUT_DIR) if getattr(response, 'files_to_write', None) else []
    
    status_messages = list(file_messages)
    if getattr(response, 'message_to_user', None):
        status_messages.append(f"\nArchitecture Agent Message: {response.message_to_user}")
        
    status_messages.append("\nArchitecture generation is complete. Proceeding to UI/UX Design...")
    return Event(output="\n".join(status_messages), route="ui_ux_phase")


def prepare_ui_ux_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = ""
    
    # Send all planning docs including Architecture.md to the UI UX agent
    for filename in FILE_SEQUENCE:
        filepath = os.path.join(REQ_OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                planning_docs += f"--- {filename} ---\n{f.read()}\n\n"
                
    arch_filepath = os.path.join(ARCH_OUTPUT_DIR, "Architecture.md")
    if os.path.exists(arch_filepath):
        with open(arch_filepath, "r") as f:
            planning_docs += f"--- Architecture.md ---\n{f.read()}\n\n"
    
    prompt = f"Original User Task: {original_task}\n\nThe architecture phase is now complete. Below are the project documents:\n\n{planning_docs}\n\nPlease generate the UI/UX specifications and design documents via `files_to_write`."
    return prompt


def process_ui_ux_response(ctx, node_input) -> Event:
    if isinstance(node_input, dict):
        response = AgentResponse(**node_input)
    else:
        response = node_input
        
    if not hasattr(response, 'files_to_write'):
        return Event(output=f"System Error: Expected AgentResponse, got {type(response)}")
        
    file_messages = _save_planning_files(response.files_to_write, UI_UX_OUTPUT_DIR) if getattr(response, 'files_to_write', None) else []
    
    status_messages = list(file_messages)
    if getattr(response, 'message_to_user', None):
        status_messages.append(f"\nUI/UX Agent Message: {response.message_to_user}")
        
    status_messages.append("\nUI/UX Design generation is complete. Proceeding to Task Planning...")
    return Event(output="\n".join(status_messages), route="task_planning_phase")


def prepare_task_planner_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = ""
    
    for filename in FILE_SEQUENCE:
        filepath = os.path.join(REQ_OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                planning_docs += f"--- {filename} ---\n{f.read()}\n\n"
                
    arch_filepath = os.path.join(ARCH_OUTPUT_DIR, "Architecture.md")
    if os.path.exists(arch_filepath):
        with open(arch_filepath, "r") as f:
            planning_docs += f"--- Architecture.md ---\n{f.read()}\n\n"
            
    # Include output from UI UX agent
    if os.path.exists(UI_UX_OUTPUT_DIR):
        for filename in os.listdir(UI_UX_OUTPUT_DIR):
            filepath = os.path.join(UI_UX_OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                with open(filepath, "r") as f:
                    planning_docs += f"--- {filename} ---\n{f.read()}\n\n"
    
    prompt = f"Original User Task: {original_task}\n\nThe requirement, architecture, and UI/UX phases are complete. Below are the project documents:\n\n{planning_docs}\n\nPlease generate the TaskPlan.md via `files_to_write`."
    return prompt


def process_task_planner_response(ctx, node_input) -> Event:
    if isinstance(node_input, dict):
        response = AgentResponse(**node_input)
    else:
        response = node_input
        
    if not hasattr(response, 'files_to_write'):
        return Event(output=f"System Error: Expected AgentResponse, got {type(response)}")
        
    file_messages = _save_planning_files(response.files_to_write, TASK_PLAN_OUTPUT_DIR) if getattr(response, 'files_to_write', None) else []
    
    status_messages = list(file_messages)
    if getattr(response, 'message_to_user', None):
        status_messages.append(f"\nTask Planner Agent Message: {response.message_to_user}")
        
    status_messages.append("\nTask planning generation is complete. Workflow finished!")
    return Event(output="\n".join(status_messages))



root_agent = Workflow(
    name="never_sleep_code_team_workflow",
    edges=[
        (START, store_task_node),
        (store_task_node, requirement_agent),
        (requirement_agent, process_agent_response),
        (process_agent_response, {"ask_questions": ask_questions_node, "done": prepare_architecture_prompt}),
        (ask_questions_node, save_answer_node),
        (save_answer_node, {"ask_more": ask_questions_node, "finished": format_update_prompt}),
        (format_update_prompt, requirement_agent),
        (prepare_architecture_prompt, architecture_agent),
        (architecture_agent, process_arch_response),
        (process_arch_response, {"ui_ux_phase": prepare_ui_ux_prompt}),
        (prepare_ui_ux_prompt, ui_ux_designer_agent),
        (ui_ux_designer_agent, process_ui_ux_response),
        (process_ui_ux_response, {"task_planning_phase": prepare_task_planner_prompt}),
        (prepare_task_planner_prompt, task_planner_agent),
        (task_planner_agent, process_task_planner_response)
    ],
    description="A workflow that takes a project idea, generates structured planning documents, designs the architecture, creates UI/UX specs, and creates a task plan.",
)
