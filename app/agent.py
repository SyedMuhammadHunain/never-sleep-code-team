import os
from typing import List

from app.app_utils.skill_loader import load_skill_file

from google.adk.workflow import Workflow, START
from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.events.request_input import RequestInput
from app.architecture_agent import architecture_agent
from app.ui_ux_designer_agent import ui_ux_designer_agent
from app.task_planner_agent import task_planner_agent
from app.env_setup_agent import env_setup_agent
from app.coder_agent import coder_agent
from app.test_writer_agent import test_writer_agent
from app.debugger_agent import debugger_agent
from app.security_agent import security_agent
from app.performance_agent import performance_agent
from app.schemas import FileToWrite, AgentResponse

REQ_OUTPUT_DIR = "Output/requirement_agent_output_files"
ARCH_OUTPUT_DIR = "Output/Architecture_output_files"
UI_UX_OUTPUT_DIR = "Output/ui_ux_designer_output_files"
TASK_PLAN_OUTPUT_DIR = "Output/task_planner_output_files"
ENV_SETUP_OUTPUT_DIR = "Output/env_setup_output_files"
CODER_OUTPUT_DIR = "Output/coder_output_files"
TEST_WRITER_OUTPUT_DIR = "Output/test_writer_output_files"
DEBUGGER_OUTPUT_DIR = "Output/debugger_output_files"
SECURITY_OUTPUT_DIR = "Output/security_output_files"
PERFORMANCE_OUTPUT_DIR = "Output/performance_output_files"

FILE_SEQUENCE = [
    "PRD.md",
    "TechSpec.md",
    "AppFlow.md",
    "Design.md",
    "Schema.md",
    "ImplementationPlan.md",
    "Tracker.md",
    "Rules.md",
]


instruction = f"""You are the Requirement Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("not-a-vibe-coder")}
</SKILL_DOCUMENT>

Based on the user's task, generate ALL 8 required planning files exactly matching these names. You must provide the full content for each file in `files_to_write`:
{", ".join(FILE_SEQUENCE)}
"""

requirement_agent = LlmAgent(
    name="requirement_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)


def store_task_node(ctx, node_input):
    ctx.state["original_task"] = getattr(node_input, "text", str(node_input))
    ctx.state["is_first_pass"] = True
    ctx.state["pending_questions"] = []
    ctx.state["qa_pairs"] = {}
    return node_input


def _parse_agent_response(node_input) -> AgentResponse:
    import json

    if isinstance(node_input, dict):
        return AgentResponse(**node_input)
    if hasattr(node_input, "output") and isinstance(node_input.output, dict):
        return AgentResponse(**node_input.output)
    if hasattr(node_input, "output") and isinstance(node_input.output, AgentResponse):
        return node_input.output
    if (
        hasattr(node_input, "content")
        and node_input.content
        and hasattr(node_input.content, "parts")
    ):
        for part in node_input.content.parts:
            if hasattr(part, "text") and part.text:
                try:
                    text = part.text
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0]
                    data = json.loads(text)
                    return AgentResponse(**data)
                except Exception:
                    pass
    return node_input


def _save_planning_files(
    files_to_write: List[FileToWrite], output_dir: str
) -> List[str]:
    """Saves generated files to disk in the specified output directory and returns success messages."""
    os.makedirs(output_dir, exist_ok=True)
    messages = []

    for file_obj in files_to_write:
        file_path = os.path.join(output_dir, file_obj.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            file.write(file_obj.content)
        messages.append(f"Successfully created/updated: `{file_path}`")

    return messages


def _build_status_messages(
    response: AgentResponse, file_messages: List[str]
) -> List[str]:
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
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}",
            route="done",
        )

    file_messages = (
        _save_planning_files(response.files_to_write, REQ_OUTPUT_DIR)
        if response.files_to_write
        else []
    )
    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and response.clarifying_questions:
        ctx.state["pending_questions"] = response.clarifying_questions.copy()
        status_messages.append("\nEntering Q&A Phase to collect your answers...")
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def _ask_questions_helper(ctx, prefix=""):
    pending_key = f"{prefix}pending_questions" if prefix else "pending_questions"
    current_key = f"{prefix}current_question" if prefix else "current_question"
    pending_questions = ctx.state.get(pending_key, [])

    if not pending_questions:
        return Event(output=None, route="finished")  # type: ignore

    current_question = pending_questions[0]
    ctx.state[current_key] = current_question
    return RequestInput(message=current_question)


def _save_answer_helper(ctx, node_input, prefix=""):
    answer = getattr(node_input, "text", str(node_input))
    current_key = f"{prefix}current_question" if prefix else "current_question"
    qa_key = f"{prefix}qa_pairs" if prefix else "qa_pairs"
    pending_key = f"{prefix}pending_questions" if prefix else "pending_questions"

    current_question = ctx.state.get(current_key)
    qa_pairs = ctx.state.get(qa_key, {})
    qa_pairs[current_question] = answer
    ctx.state[qa_key] = qa_pairs

    pending_questions = ctx.state.get(pending_key, [])
    if pending_questions:
        pending_questions.pop(0)
    ctx.state[pending_key] = pending_questions

    if pending_questions:
        return Event(output=None, route="ask_more")  # type: ignore

    return Event(output=qa_pairs, route="finished")  # type: ignore


def ask_questions_node(ctx, node_input):
    return _ask_questions_helper(ctx, "")


def save_answer_node(ctx, node_input):
    return _save_answer_helper(ctx, node_input, "")


def format_update_prompt(ctx, node_input):
    qa_pairs = node_input
    original_task = ctx.state.get("original_task", "")

    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())

    return f"""Original task: {original_task}

Based on the original task, you previously generated the planning files.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update Design.md with these answers.
You must return the full updated Design.md file in your `files_to_write` array.
Ensure that the Design.md file is updated on the disk based on the new inputs from the user.
"""


def _read_planning_docs(dirs_to_read: List[str]) -> str:
    planning_docs = ""
    for filename in FILE_SEQUENCE:
        filepath = os.path.join(REQ_OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                planning_docs += f"--- {filename} ---\n{f.read()}\n\n"

    for d in dirs_to_read:
        if d == ARCH_OUTPUT_DIR:
            arch_filepath = os.path.join(ARCH_OUTPUT_DIR, "Architecture.md")
            if os.path.exists(arch_filepath):
                with open(arch_filepath, "r") as f:
                    planning_docs += f"--- Architecture.md ---\n{f.read()}\n\n"
        elif os.path.exists(d):
            for filename in os.listdir(d):
                filepath = os.path.join(d, filename)
                if os.path.isfile(filepath):
                    with open(filepath, "r") as f:
                        planning_docs += f"--- {filename} ---\n{f.read()}\n\n"
    return planning_docs


def prepare_architecture_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs([])
    prompt = f"Original User Task: {original_task}\n\nThe requirement phase is now complete. Below are the generated planning documents:\n\n{planning_docs}\n\nPlease generate the software architecture and save it via `files_to_write`."
    return prompt


def process_arch_response(ctx, node_input) -> Event:
    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, ARCH_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = list(file_messages)
    if getattr(response, "message_to_user", None):
        status_messages.append(
            f"\nArchitecture Agent Message: {response.message_to_user}"
        )

    status_messages.append(
        "\nArchitecture generation is complete. Proceeding to UI/UX Design..."
    )
    return Event(output="\n".join(status_messages), route="ui_ux_phase")  # type: ignore


def prepare_ui_ux_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs([ARCH_OUTPUT_DIR])
    prompt = f"Original User Task: {original_task}\n\nThe architecture phase is now complete. Below are the project documents:\n\n{planning_docs}\n\nPlease generate the UI/UX specifications and design documents via `files_to_write`."
    return prompt


def process_ui_ux_response(ctx, node_input) -> Event:
    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, UI_UX_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = list(file_messages)
    if getattr(response, "message_to_user", None):
        status_messages.append(f"\nUI/UX Agent Message: {response.message_to_user}")

    status_messages.append(
        "\nUI/UX Design generation is complete. Proceeding to Task Planning..."
    )
    return Event(output="\n".join(status_messages), route="task_planning_phase")  # type: ignore


def prepare_task_planner_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs([ARCH_OUTPUT_DIR, UI_UX_OUTPUT_DIR])
    prompt = f"Original User Task: {original_task}\n\nThe requirement, architecture, and UI/UX phases are complete. Below are the project documents:\n\n{planning_docs}\n\nPlease generate the TaskPlan.md via `files_to_write`."
    return prompt


def process_task_planner_response(ctx, node_input) -> Event:
    is_initial_run = ctx.state.get("is_task_planner_first_pass", True)

    if is_initial_run:
        ctx.state["is_task_planner_first_pass"] = False
        ctx.state["task_planner_qa_pairs"] = {}

    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, TASK_PLAN_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and getattr(response, "clarifying_questions", None):
        ctx.state["task_planner_pending_questions"] = (
            response.clarifying_questions.copy()
        )
        status_messages.append(
            "\nEntering Task Planner Q&A Phase to collect your answers..."
        )
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    status_messages.append(
        "\nTask planning generation is complete. Proceeding to Environment Setup..."
    )
    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def ask_task_planner_questions_node(ctx, node_input):
    return _ask_questions_helper(ctx, "task_planner_")


def save_task_planner_answer_node(ctx, node_input):
    return _save_answer_helper(ctx, node_input, "task_planner_")


def format_task_planner_update_prompt(ctx, node_input):
    qa_pairs = node_input

    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())

    return f"""Based on the original task and the previously generated documents, you asked some clarifying questions.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update TaskPlan.md with these answers.
You must return the full updated TaskPlan.md file in your `files_to_write` array.
Ensure that the TaskPlan.md file is updated based on the new inputs from the user.
"""


def prepare_env_setup_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs(
        [ARCH_OUTPUT_DIR, UI_UX_OUTPUT_DIR, TASK_PLAN_OUTPUT_DIR]
    )
    prompt = f"Original User Task: {original_task}\n\nThe planning phases are complete. Below are the project documents:\n\n{planning_docs}\n\nPlease generate the mise.toml configuration via `files_to_write`."
    return prompt


def process_env_setup_response(ctx, node_input) -> Event:
    is_initial_run = ctx.state.get("is_env_setup_first_pass", True)

    if is_initial_run:
        ctx.state["is_env_setup_first_pass"] = False
        ctx.state["env_setup_qa_pairs"] = {}

    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, ENV_SETUP_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and getattr(response, "clarifying_questions", None):
        ctx.state["env_setup_pending_questions"] = response.clarifying_questions.copy()
        status_messages.append(
            "\nEntering Environment Setup Q&A Phase to collect your answers..."
        )
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    status_messages.append(
        "\nEnvironment setup generation is complete. Proceeding to Coding Phase..."
    )
    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def ask_env_setup_questions_node(ctx, node_input):
    return _ask_questions_helper(ctx, "env_setup_")


def save_env_setup_answer_node(ctx, node_input):
    return _save_answer_helper(ctx, node_input, "env_setup_")


def format_env_setup_update_prompt(ctx, node_input):
    qa_pairs = node_input

    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())

    return f"""Based on the original task and the previously generated documents, you asked some clarifying questions.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update mise.toml with these answers.
You must return the full updated mise.toml file in your `files_to_write` array.
Ensure that the mise.toml file is updated based on the new inputs from the user.
"""


def prepare_coder_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs(
        [ARCH_OUTPUT_DIR, UI_UX_OUTPUT_DIR, TASK_PLAN_OUTPUT_DIR, ENV_SETUP_OUTPUT_DIR]
    )
    prompt = f"Original User Task: {original_task}\n\nThe planning and setup phases are complete. Below are the project documents:\n\n{planning_docs}\n\nPlease begin implementing the tasks following the Coder Agent instructions."
    return prompt


def process_coder_response(ctx, node_input) -> Event:
    is_initial_run = ctx.state.get("is_coder_first_pass", True)

    if is_initial_run:
        ctx.state["is_coder_first_pass"] = False
        ctx.state["coder_qa_pairs"] = {}

    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, CODER_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and getattr(response, "clarifying_questions", None):
        ctx.state["coder_pending_questions"] = response.clarifying_questions.copy()
        status_messages.append("\nEntering Coding Q&A Phase to collect your answers...")
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    status_messages.append("\nCoding Phase is complete. Proceeding to Test Writing...")
    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def ask_coder_questions_node(ctx, node_input):
    return _ask_questions_helper(ctx, "coder_")


def save_coder_answer_node(ctx, node_input):
    return _save_answer_helper(ctx, node_input, "coder_")


def format_coder_update_prompt(ctx, node_input):
    qa_pairs = node_input

    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())

    return f"""Based on the original task and the previously generated documents, you asked some clarifying questions.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update the implementation files with these answers.
You must return the full updated files in your `files_to_write` array.
"""


def prepare_test_writer_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
        ]
    )
    prompt = f"Original User Task: {original_task}\n\nThe coding phase is complete. Below are the project documents and implementation files:\n\n{planning_docs}\n\nPlease begin writing tests following the Test Writer Agent instructions."
    return prompt


def process_test_writer_response(ctx, node_input) -> Event:
    is_initial_run = ctx.state.get("is_test_writer_first_pass", True)

    if is_initial_run:
        ctx.state["is_test_writer_first_pass"] = False
        ctx.state["test_writer_qa_pairs"] = {}

    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, TEST_WRITER_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and getattr(response, "clarifying_questions", None):
        ctx.state["test_writer_pending_questions"] = (
            response.clarifying_questions.copy()
        )
        status_messages.append(
            "\nEntering Test Writing Q&A Phase to collect your answers..."
        )
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    status_messages.append(
        "\nTest Writing Phase is complete. Proceeding to Debugging..."
    )
    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def ask_test_writer_questions_node(ctx, node_input):
    return _ask_questions_helper(ctx, "test_writer_")


def save_test_writer_answer_node(ctx, node_input):
    return _save_answer_helper(ctx, node_input, "test_writer_")


def format_test_writer_update_prompt(ctx, node_input):
    qa_pairs = node_input

    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())

    return f"""Based on the original task and the previously generated documents, you asked some clarifying questions.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update the test files with these answers.
You must return the full updated files in your `files_to_write` array.
"""


def prepare_debugger_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
            TEST_WRITER_OUTPUT_DIR,
        ]
    )
    prompt = f"Original User Task: {original_task}\n\nThe test writing phase is complete. Below are the project documents and implementation files:\n\n{planning_docs}\n\nPlease begin debugging following the Debugger Agent instructions."
    return prompt


def process_debugger_response(ctx, node_input) -> Event:
    is_initial_run = ctx.state.get("is_debugger_first_pass", True)

    if is_initial_run:
        ctx.state["is_debugger_first_pass"] = False
        ctx.state["debugger_qa_pairs"] = {}

    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, DEBUGGER_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and getattr(response, "clarifying_questions", None):
        ctx.state["debugger_pending_questions"] = response.clarifying_questions.copy()
        status_messages.append(
            "\nEntering Debugging Q&A Phase to collect your answers..."
        )
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    status_messages.append(
        "\nDebugging Phase is complete. Proceeding to Security Analysis..."
    )
    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def ask_debugger_questions_node(ctx, node_input):
    return _ask_questions_helper(ctx, "debugger_")


def save_debugger_answer_node(ctx, node_input):
    return _save_answer_helper(ctx, node_input, "debugger_")


def format_debugger_update_prompt(ctx, node_input):
    qa_pairs = node_input

    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())

    return f"""Based on the original task and the previously generated documents, you asked some clarifying questions.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update the code with these answers.
You must return the full updated files in your `files_to_write` array.
"""


def prepare_security_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
            TEST_WRITER_OUTPUT_DIR,
            DEBUGGER_OUTPUT_DIR,
        ]
    )
    prompt = f"Original User Task: {original_task}\n\nThe debugging phase is complete. Below are the project documents and implementation files:\n\n{planning_docs}\n\nPlease begin security analysis following the Security Agent instructions."
    return prompt


def process_security_response(ctx, node_input) -> Event:
    is_initial_run = ctx.state.get("is_security_first_pass", True)

    if is_initial_run:
        ctx.state["is_security_first_pass"] = False
        ctx.state["security_qa_pairs"] = {}

    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, SECURITY_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and getattr(response, "clarifying_questions", None):
        ctx.state["security_pending_questions"] = response.clarifying_questions.copy()
        status_messages.append(
            "\nEntering Security Q&A Phase to collect your answers..."
        )
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    status_messages.append(
        "\nSecurity Phase is complete. Proceeding to Performance Analysis..."
    )
    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def ask_security_questions_node(ctx, node_input):
    return _ask_questions_helper(ctx, "security_")


def save_security_answer_node(ctx, node_input):
    return _save_answer_helper(ctx, node_input, "security_")


def format_security_update_prompt(ctx, node_input):
    qa_pairs = node_input

    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())

    return f"""Based on the original task and the previously generated documents, you asked some clarifying questions.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update the security documents with these answers.
You must return the full updated files in your `files_to_write` array.
"""


def prepare_performance_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = _read_planning_docs(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
            TEST_WRITER_OUTPUT_DIR,
            DEBUGGER_OUTPUT_DIR,
            SECURITY_OUTPUT_DIR,
        ]
    )
    prompt = f"Original User Task: {original_task}\n\nThe security analysis phase is complete. Below are the project documents and implementation files:\n\n{planning_docs}\n\nPlease begin performance analysis and optimization following the Performance Agent instructions."
    return prompt


def process_performance_response(ctx, node_input) -> Event:
    is_initial_run = ctx.state.get("is_performance_first_pass", True)

    if is_initial_run:
        ctx.state["is_performance_first_pass"] = False
        ctx.state["performance_qa_pairs"] = {}

    response = _parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        _save_planning_files(response.files_to_write, PERFORMANCE_OUTPUT_DIR)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = _build_status_messages(response, file_messages)

    if is_initial_run and getattr(response, "clarifying_questions", None):
        ctx.state["performance_pending_questions"] = (
            response.clarifying_questions.copy()
        )
        status_messages.append(
            "\nEntering Performance Q&A Phase to collect your answers..."
        )
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    status_messages.append("\nPerformance Phase is complete. Workflow finished!")
    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def ask_performance_questions_node(ctx, node_input):
    return _ask_questions_helper(ctx, "performance_")


def save_performance_answer_node(ctx, node_input):
    return _save_answer_helper(ctx, node_input, "performance_")


def format_performance_update_prompt(ctx, node_input):
    qa_pairs = node_input

    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())

    return f"""Based on the original task and the previously generated documents, you asked some clarifying questions.
Here are the user's answers to the clarifying questions:

{formatted_qa}

Instruction: Now update the performance documents with these answers.
You must return the full updated files in your `files_to_write` array.
"""


def end_workflow_node(ctx, node_input):
    return node_input


root_agent = Workflow(
    name="never_sleep_code_team_workflow",
    edges=[
        (START, store_task_node),
        (store_task_node, requirement_agent),
        (requirement_agent, process_agent_response),
        (
            process_agent_response,
            {"ask_questions": ask_questions_node, "done": prepare_architecture_prompt},
        ),
        (ask_questions_node, save_answer_node),
        (
            save_answer_node,
            {"ask_more": ask_questions_node, "finished": format_update_prompt},
        ),
        (format_update_prompt, requirement_agent),
        (prepare_architecture_prompt, architecture_agent),
        (architecture_agent, process_arch_response),
        (process_arch_response, {"ui_ux_phase": prepare_ui_ux_prompt}),
        (prepare_ui_ux_prompt, ui_ux_designer_agent),
        (ui_ux_designer_agent, process_ui_ux_response),
        (process_ui_ux_response, {"task_planning_phase": prepare_task_planner_prompt}),
        (prepare_task_planner_prompt, task_planner_agent),
        (task_planner_agent, process_task_planner_response),
        (
            process_task_planner_response,
            {
                "ask_questions": ask_task_planner_questions_node,
                "done": prepare_env_setup_prompt,
            },
        ),
        (ask_task_planner_questions_node, save_task_planner_answer_node),
        (
            save_task_planner_answer_node,
            {
                "ask_more": ask_task_planner_questions_node,
                "finished": format_task_planner_update_prompt,
            },
        ),
        (format_task_planner_update_prompt, task_planner_agent),
        (prepare_env_setup_prompt, env_setup_agent),
        (env_setup_agent, process_env_setup_response),
        (
            process_env_setup_response,
            {
                "ask_questions": ask_env_setup_questions_node,
                "done": prepare_coder_prompt,
            },
        ),
        (ask_env_setup_questions_node, save_env_setup_answer_node),
        (
            save_env_setup_answer_node,
            {
                "ask_more": ask_env_setup_questions_node,
                "finished": format_env_setup_update_prompt,
            },
        ),
        (format_env_setup_update_prompt, env_setup_agent),
        (prepare_coder_prompt, coder_agent),
        (coder_agent, process_coder_response),
        (
            process_coder_response,
            {
                "ask_questions": ask_coder_questions_node,
                "done": prepare_test_writer_prompt,
            },
        ),
        (ask_coder_questions_node, save_coder_answer_node),
        (
            save_coder_answer_node,
            {
                "ask_more": ask_coder_questions_node,
                "finished": format_coder_update_prompt,
            },
        ),
        (format_coder_update_prompt, coder_agent),
        (prepare_test_writer_prompt, test_writer_agent),
        (test_writer_agent, process_test_writer_response),
        (
            process_test_writer_response,
            {
                "ask_questions": ask_test_writer_questions_node,
                "done": prepare_debugger_prompt,
            },
        ),
        (ask_test_writer_questions_node, save_test_writer_answer_node),
        (
            save_test_writer_answer_node,
            {
                "ask_more": ask_test_writer_questions_node,
                "finished": format_test_writer_update_prompt,
            },
        ),
        (format_test_writer_update_prompt, test_writer_agent),
        (prepare_debugger_prompt, debugger_agent),
        (debugger_agent, process_debugger_response),
        (
            process_debugger_response,
            {
                "ask_questions": ask_debugger_questions_node,
                "done": prepare_security_prompt,
            },
        ),
        (ask_debugger_questions_node, save_debugger_answer_node),
        (
            save_debugger_answer_node,
            {
                "ask_more": ask_debugger_questions_node,
                "finished": format_debugger_update_prompt,
            },
        ),
        (format_debugger_update_prompt, debugger_agent),
        (prepare_security_prompt, security_agent),
        (security_agent, process_security_response),
        (
            process_security_response,
            {
                "ask_questions": ask_security_questions_node,
                "done": prepare_performance_prompt,
            },
        ),
        (ask_security_questions_node, save_security_answer_node),
        (
            save_security_answer_node,
            {
                "ask_more": ask_security_questions_node,
                "finished": format_security_update_prompt,
            },
        ),
        (format_security_update_prompt, security_agent),
        (prepare_performance_prompt, performance_agent),
        (performance_agent, process_performance_response),
        (
            process_performance_response,
            {
                "ask_questions": ask_performance_questions_node,
                "done": end_workflow_node,
            },
        ),
        (ask_performance_questions_node, save_performance_answer_node),
        (
            save_performance_answer_node,
            {
                "ask_more": ask_performance_questions_node,
                "finished": format_performance_update_prompt,
            },
        ),
        (format_performance_update_prompt, performance_agent),
    ],
    description="A workflow that takes a project idea, generates structured planning documents, designs the architecture, creates UI/UX specs, and creates a task plan.",
)
