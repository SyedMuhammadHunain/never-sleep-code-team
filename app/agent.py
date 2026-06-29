from app.app_utils.model_utils import get_gemini_model
import json
import os
import subprocess
from typing import List

from app.app_utils.skill_loader import load_skill_file

from google.adk.workflow import Workflow, START
from app.app_utils.base_agent import NeverSleepLlmAgent
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
from app.code_review_agent import code_review_agent
from app.cicd_agent import cicd_agent
from app.notifier_agent import notifier_agent
from app.monitoring_agent import monitoring_agent
from app.research_agent import research_agent
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
CODE_REVIEW_OUTPUT_DIR = "Output/code_review_output_files"
CICD_OUTPUT_DIR = "Output/cicd_output_files"
NOTIFIER_OUTPUT_DIR = "Output/notifier_output_files"
MONITORING_OUTPUT_DIR = "Output/monitoring_output_files"
RESEARCH_OUTPUT_DIR = "Output/research_output_files"

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


requirement_agent = NeverSleepLlmAgent(
    name="requirement_agent",
    model=get_gemini_model(),
    instruction=f"""You are the Requirement Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("not-a-vibe-coder")}
</SKILL_DOCUMENT>

Based on the user's task, generate ALL 8 required planning files exactly matching these names. You must provide the full content for each file in `files_to_write`:
{", ".join(FILE_SEQUENCE)}
""",
    output_schema=AgentResponse,
)


def store_task_node(ctx, node_input):
    ctx.state["original_task"] = getattr(node_input, "text", str(node_input))
    ctx.state["is_first_pass"] = True
    ctx.state["pending_questions"] = []
    ctx.state["qa_pairs"] = {}
    return node_input


def parse_agent_response(node_input) -> AgentResponse:
    if isinstance(node_input, dict):
        return AgentResponse(**node_input)
    if hasattr(node_input, "output") and isinstance(node_input.output, dict):
        return AgentResponse(**node_input.output)
    if hasattr(node_input, "output") and isinstance(node_input.output, AgentResponse):
        return node_input.output
    text_to_parse = None
    if isinstance(node_input, str):
        text_to_parse = node_input
    elif hasattr(node_input, "output") and isinstance(node_input.output, str):
        text_to_parse = node_input.output

    if text_to_parse:
        try:
            if "```json" in text_to_parse:
                text_to_parse = text_to_parse.split("```json")[1].split("```")[0]
            data = json.loads(text_to_parse)
            return AgentResponse(**data)
        except Exception:
            pass
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


def save_generated_files(
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


def build_status_messages(
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

    response = parse_agent_response(node_input)
    if not isinstance(response, AgentResponse):
        ctx.state["pending_questions"] = [
            "The LLM failed to generate a valid response (possibly due to a RECITATION safety block). Please type 'retry' to proceed, or modify the prompt."
        ]
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}. Entering Q&A fallback for retry.",
            route="ask_questions",
        )

    file_messages = (
        save_generated_files(response.files_to_write, REQ_OUTPUT_DIR)
        if response.files_to_write
        else []
    )
    status_messages = build_status_messages(response, file_messages)

    if is_initial_run and response.clarifying_questions:
        ctx.state["pending_questions"] = response.clarifying_questions.copy()
        status_messages.append("\nEntering Q&A Phase to collect your answers...")
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def prompt_for_clarification(ctx, prefix=""):
    pending_key = f"{prefix}pending_questions" if prefix else "pending_questions"
    current_key = f"{prefix}current_question" if prefix else "current_question"
    pending_questions = ctx.state.get(pending_key, [])

    if not pending_questions:
        return Event(output=None, route="finished")  # type: ignore

    current_question = pending_questions[0]
    ctx.state[current_key] = current_question
    return RequestInput(message=current_question)


def store_user_answer(ctx, node_input, prefix=""):
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
    return prompt_for_clarification(ctx, "")


def save_answer_node(ctx, node_input):
    return store_user_answer(ctx, node_input, "")


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


def read_generated_documents(extra_output_dirs: List[str]) -> str:
    planning_docs = ""
    for filename in FILE_SEQUENCE:
        filepath = os.path.join(REQ_OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                planning_docs += f"--- {filename} ---\n{f.read()}\n\n"

    for directory in extra_output_dirs:
        if directory == ARCH_OUTPUT_DIR:
            arch_filepath = os.path.join(ARCH_OUTPUT_DIR, "Architecture.md")
            if os.path.exists(arch_filepath):
                with open(arch_filepath, "r") as f:
                    planning_docs += f"--- Architecture.md ---\n{f.read()}\n\n"
        elif os.path.exists(directory):
            for root, _, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    if os.path.isfile(filepath):
                        with open(filepath, "r") as f:
                            rel_path = os.path.relpath(filepath, directory)
                            planning_docs += (
                                f"--- {directory}/{rel_path} ---\n{f.read()}\n\n"
                            )
    return planning_docs


def prepare_architecture_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents([])
    prompt = f"Original User Task: {original_task}\n\nThe requirement phase is now complete. Below are the generated planning documents:\n\n{planning_docs}\n\nPlease generate the software architecture and save it via `files_to_write`."
    return prompt


def process_arch_response(ctx, node_input) -> Event:
    response = parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        save_generated_files(response.files_to_write, ARCH_OUTPUT_DIR)
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
    planning_docs = read_generated_documents([ARCH_OUTPUT_DIR])
    prompt = f"Original User Task: {original_task}\n\nThe architecture phase is now complete. Below are the project documents:\n\n{planning_docs}\n\nPlease generate the UI/UX specifications and design documents via `files_to_write`."
    return prompt


def process_ui_ux_response(ctx, node_input) -> Event:
    response = parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}"
        )

    file_messages = (
        save_generated_files(response.files_to_write, UI_UX_OUTPUT_DIR)
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
    planning_docs = read_generated_documents([ARCH_OUTPUT_DIR, UI_UX_OUTPUT_DIR])
    prompt = f"Original User Task: {original_task}\n\nThe requirement, architecture, and UI/UX phases are complete. Below are the project documents:\n\n{planning_docs}\n\nPlease generate the TaskPlan.md via `files_to_write`."
    return prompt


def process_phase_response(
    ctx,
    node_input,
    prefix: str,
    output_dir: str,
    qa_phase_message: str,
    done_message: str,
) -> Event:
    is_initial_run = ctx.state.get(f"is_{prefix}first_pass", True)

    if is_initial_run:
        ctx.state[f"is_{prefix}first_pass"] = False
        ctx.state[f"{prefix}qa_pairs"] = {}

    response = parse_agent_response(node_input)

    if not isinstance(response, AgentResponse):
        ctx.state[f"{prefix}pending_questions"] = [
            "The LLM failed to generate a valid response (possibly due to a RECITATION safety block). Please type 'retry' to proceed, or modify the prompt."
        ]
        return Event(
            output=f"System Error: Expected AgentResponse, got {type(response)}. Entering Q&A fallback for retry.",
            route="ask_questions",
        )

    file_messages = (
        save_generated_files(response.files_to_write, output_dir)
        if getattr(response, "files_to_write", None)
        else []
    )

    status_messages = build_status_messages(response, file_messages)

    if is_initial_run and getattr(response, "clarifying_questions", None):
        ctx.state[f"{prefix}pending_questions"] = response.clarifying_questions.copy()
        status_messages.append(f"\n{qa_phase_message}")
        return Event(output="\n".join(status_messages), route="ask_questions")  # type: ignore

    if prefix == "coder_" and hasattr(response, "has_more_tasks"):
        ctx.state["is_project_complete"] = not response.has_more_tasks

    status_messages.append(f"\n{done_message}")
    return Event(output="\n".join(status_messages), route="done")  # type: ignore


def validate_build_node(ctx, node_input) -> Event:
    """
    Validates the generated code by attempting to build the project.
    If the build fails, the error is routed back to the coder for fixing.
    """
    build_dir = CODER_OUTPUT_DIR

    if not os.path.exists(os.path.join(build_dir, "package.json")):
        return Event(
            output="No package.json found. Skipping build validation.",
            route="validation_passed",
        )

    try:
        if not os.path.exists(os.path.join(build_dir, "node_modules")):
            subprocess.run(
                ["npm", "install"],
                cwd=build_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )

        subprocess.run(
            ["npm", "run", "build"],
            cwd=build_dir,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return Event(
            output="Build validation passed successfully.", route="validation_passed"
        )
    except subprocess.CalledProcessError as e:
        error_msg = f"Build failed with the following error:\\n{e.stderr}\\n\\nPlease fix the code to resolve these build errors."

        if "coder_pending_questions" not in ctx.state:
            ctx.state["coder_pending_questions"] = []
        ctx.state["coder_pending_questions"].append(error_msg)

        return Event(
            output="Build validation failed. Routing back to Coder Agent...",
            route="validation_failed",
        )
    except subprocess.TimeoutExpired:
        error_msg = "Build failed due to timeout. Please optimize the build process or fix infinite loops."
        if "coder_pending_questions" not in ctx.state:
            ctx.state["coder_pending_questions"] = []
        ctx.state["coder_pending_questions"].append(error_msg)
        return Event(
            output="Build validation timed out. Routing back to Coder Agent...",
            route="validation_failed",
        )


def run_playwright_tests_node(ctx, node_input) -> Event:
    """
    Runs Playwright tests generated by the Test Writer Agent.
    If they fail, routes back to Coder Agent.
    """
    build_dir = CODER_OUTPUT_DIR
    tests_dir = TEST_WRITER_OUTPUT_DIR

    if not os.path.exists(os.path.join(build_dir, "package.json")):
        return Event(
            output="No package.json found. Skipping tests.", route="tests_passed"
        )

    try:
        if not os.path.exists(os.path.join(build_dir, "node_modules", "@playwright")):
            subprocess.run(
                ["npm", "install", "-D", "@playwright/test"],
                cwd=build_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            subprocess.run(
                ["npx", "playwright", "install", "--with-deps"],
                cwd=build_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )

        test_path = os.path.abspath(tests_dir)
        subprocess.run(
            ["npx", "playwright", "test", test_path],
            cwd=build_dir,
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return Event(
            output="Playwright tests passed successfully.", route="tests_passed"
        )
    except subprocess.CalledProcessError as e:
        error_msg = f"Playwright tests failed with the following error:\\n{e.stdout}\\n{e.stderr}\\n\\nPlease fix the frontend logic or tests to resolve these failures."

        if "coder_pending_questions" not in ctx.state:
            ctx.state["coder_pending_questions"] = []
        ctx.state["coder_pending_questions"].append(error_msg)

        return Event(
            output="Tests failed. Routing back to Coder Agent...", route="tests_failed"
        )
    except subprocess.TimeoutExpired:
        error_msg = "Playwright tests timed out. Please optimize the tests or fix infinite loops."
        if "coder_pending_questions" not in ctx.state:
            ctx.state["coder_pending_questions"] = []
        ctx.state["coder_pending_questions"].append(error_msg)
        return Event(
            output="Tests timed out. Routing back to Coder Agent...",
            route="tests_failed",
        )


def make_phase_nodes(
    prefix: str, output_dir: str, display_name: str, qa_msg: str, done_msg: str
):
    def process_response(ctx, node_input) -> Event:
        return process_phase_response(
            ctx, node_input, prefix, output_dir, qa_msg, done_msg
        )

    process_response.__name__ = f"process_{prefix}response"

    def ask_questions(ctx, node_input):
        return prompt_for_clarification(ctx, prefix)

    ask_questions.__name__ = f"ask_{prefix}questions_node"

    def save_answer(ctx, node_input):
        return store_user_answer(ctx, node_input, prefix)

    save_answer.__name__ = f"save_{prefix}answer_node"

    def format_prompt(ctx, node_input):
        if prefix == "task_planner_":
            msg = "Instruction: Now update the task plan files with these answers.\nYou must return the full updated files in your `files_to_write` array."
        elif prefix == "test_writer_":
            msg = "Instruction: Now update the test files with these answers.\nYou must return the full updated files in your `files_to_write` array."
        elif prefix == "debugger_":
            msg = "Instruction: Now update the code with these answers.\nYou must return the full updated files in your `files_to_write` array."
        elif prefix == "code_review_":
            msg = "Instruction: Now update the code review feedback files with these answers.\nYou must return the full updated files in your `files_to_write` array."
        else:
            msg = f"Instruction: Now update the {display_name} files with these answers.\nYou must return the full updated files in your `files_to_write` array."
        return generate_update_prompt(node_input, msg)

    format_prompt.__name__ = f"format_{prefix}update_prompt"

    return process_response, ask_questions, save_answer, format_prompt


def check_implementation_loop_node(ctx, node_input):
    if ctx.state.get("is_project_complete", False):
        return Event(output=node_input, route="done")  # type: ignore
    else:
        return Event(
            output="Implementation loop continuing. Returning to Coder Agent for the next tasks...",
            route="loop_back",  # type: ignore
        )


def process_task_planner_response(ctx, node_input) -> Event:
    return process_phase_response(
        ctx,
        node_input,
        "task_planner_",
        TASK_PLAN_OUTPUT_DIR,
        "Entering Task Planner Q&A Phase to collect your answers...",
        "Task planning generation is complete. Proceeding to Environment Setup...",
    )


def ask_task_planner_questions_node(ctx, node_input):
    return prompt_for_clarification(ctx, "task_planner_")


def save_task_planner_answer_node(ctx, node_input):
    return store_user_answer(ctx, node_input, "task_planner_")


def generate_update_prompt(node_input, instruction_text: str) -> str:
    qa_pairs = node_input
    formatted_qa = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in qa_pairs.items())
    return f"""Based on the original task and the previously generated documents, you asked some clarifying questions.
Here are the user's answers to the clarifying questions:

{formatted_qa}

{instruction_text}"""


def format_task_planner_update_prompt(ctx, node_input):
    return generate_update_prompt(
        node_input,
        """Instruction: Now update TaskPlan.md with these answers.
You must return the full updated TaskPlan.md file in your `files_to_write` array.
Ensure that the TaskPlan.md file is updated based on the new inputs from the user.""",
    )


def prepare_env_setup_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
        [ARCH_OUTPUT_DIR, UI_UX_OUTPUT_DIR, TASK_PLAN_OUTPUT_DIR]
    )
    prompt = f"Original User Task: {original_task}\n\nThe planning phases are complete. Below are the project documents:\n\n{planning_docs}\n\nPlease generate the mise.toml configuration via `files_to_write`."
    return prompt


(
    process_env_setup_response,
    ask_env_setup_questions_node,
    save_env_setup_answer_node,
    format_env_setup_update_prompt,
) = make_phase_nodes(
    "env_setup_",
    ENV_SETUP_OUTPUT_DIR,
    "Env Setup",
    "Entering Environment Setup Q&A Phase to collect your answers...",
    "Environment setup generation is complete. Proceeding to Coding Phase...",
)


def prepare_coder_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
        ]
    )
    prompt = f"Original User Task: {original_task}\n\nThe planning and setup phases are complete. Below are the project documents AND the code you have already generated so far in previous iterations:\n\n{planning_docs}\n\nPlease implement the NEXT task following the Coder Agent instructions. Do not rewrite files you have already completed."
    return prompt


(
    process_coder_response,
    ask_coder_questions_node,
    save_coder_answer_node,
    format_coder_update_prompt,
) = make_phase_nodes(
    "coder_",
    CODER_OUTPUT_DIR,
    "Coder",
    "Entering Coding Q&A Phase to collect your answers...",
    "Coding Phase is complete. Proceeding to Test Writing...",
)


def prepare_test_writer_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
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


(
    process_test_writer_response,
    ask_test_writer_questions_node,
    save_test_writer_answer_node,
    format_test_writer_update_prompt,
) = make_phase_nodes(
    "test_writer_",
    TEST_WRITER_OUTPUT_DIR,
    "Test Writer",
    "Entering Test Writing Q&A Phase to collect your answers...",
    "Test Writing Phase is complete. Proceeding to Debugging...",
)


def prepare_debugger_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
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


(
    process_debugger_response,
    ask_debugger_questions_node,
    save_debugger_answer_node,
    format_debugger_update_prompt,
) = make_phase_nodes(
    "debugger_",
    DEBUGGER_OUTPUT_DIR,
    "Debugger",
    "Entering Debugging Q&A Phase to collect your answers...",
    "Debugging Phase is complete. Proceeding to Security Analysis...",
)


def prepare_security_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
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


(
    process_security_response,
    ask_security_questions_node,
    save_security_answer_node,
    format_security_update_prompt,
) = make_phase_nodes(
    "security_",
    SECURITY_OUTPUT_DIR,
    "Security",
    "Entering Security Q&A Phase to collect your answers...",
    "Security Phase is complete. Proceeding to Performance Analysis...",
)


def prepare_performance_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
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


(
    process_performance_response,
    ask_performance_questions_node,
    save_performance_answer_node,
    format_performance_update_prompt,
) = make_phase_nodes(
    "performance_",
    PERFORMANCE_OUTPUT_DIR,
    "Performance",
    "Entering Performance Q&A Phase to collect your answers...",
    "Performance Phase is complete. Proceeding to Code Review...",
)


def prepare_code_review_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
            TEST_WRITER_OUTPUT_DIR,
            DEBUGGER_OUTPUT_DIR,
            SECURITY_OUTPUT_DIR,
            PERFORMANCE_OUTPUT_DIR,
        ]
    )
    prompt = f"Original User Task: {original_task}\n\nThe performance analysis phase is complete. Below are the project documents and implementation files:\n\n{planning_docs}\n\nPlease begin code review following the Code Review Agent instructions."
    return prompt


(
    process_code_review_response,
    ask_code_review_questions_node,
    save_code_review_answer_node,
    format_code_review_update_prompt,
) = make_phase_nodes(
    "code_review_",
    CODE_REVIEW_OUTPUT_DIR,
    "Code Review",
    "Entering Code Review Q&A Phase to collect your answers...",
    "Code Review Phase is complete. Workflow finished!",
)


def prepare_cicd_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
            TEST_WRITER_OUTPUT_DIR,
            DEBUGGER_OUTPUT_DIR,
            SECURITY_OUTPUT_DIR,
            PERFORMANCE_OUTPUT_DIR,
            CODE_REVIEW_OUTPUT_DIR,
        ]
    )
    file_contents = original_task + "\n" + planning_docs
    return f"Based on the project files:\n\n{file_contents}\n\nInstruction: Please perform CI/CD tasks based on your system instructions. Output the created/updated files."


(
    process_cicd_response,
    ask_cicd_questions_node,
    save_cicd_answer_node,
    format_cicd_update_prompt,
) = make_phase_nodes(
    "cicd_",
    CICD_OUTPUT_DIR,
    "Cicd",
    "Entering CI/CD Q&A Phase to collect your answers...",
    "CI/CD Phase is complete. Proceeding to next phase...",
)


def prepare_notifier_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
            TEST_WRITER_OUTPUT_DIR,
            DEBUGGER_OUTPUT_DIR,
            SECURITY_OUTPUT_DIR,
            PERFORMANCE_OUTPUT_DIR,
            CODE_REVIEW_OUTPUT_DIR,
        ]
    )
    file_contents = original_task + "\n" + planning_docs
    return f"Based on the project files:\n\n{file_contents}\n\nInstruction: Please perform Notifier tasks based on your system instructions. Output the created/updated files."


(
    process_notifier_response,
    ask_notifier_questions_node,
    save_notifier_answer_node,
    format_notifier_update_prompt,
) = make_phase_nodes(
    "notifier_",
    NOTIFIER_OUTPUT_DIR,
    "Notifier",
    "Entering Notifier Q&A Phase to collect your answers...",
    "Notifier Phase is complete. Proceeding to next phase...",
)


def prepare_monitoring_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
            TEST_WRITER_OUTPUT_DIR,
            DEBUGGER_OUTPUT_DIR,
            SECURITY_OUTPUT_DIR,
            PERFORMANCE_OUTPUT_DIR,
            CODE_REVIEW_OUTPUT_DIR,
        ]
    )
    file_contents = original_task + "\n" + planning_docs
    return f"Based on the project files:\n\n{file_contents}\n\nInstruction: Please perform Monitoring tasks based on your system instructions. Output the created/updated files."


(
    process_monitoring_response,
    ask_monitoring_questions_node,
    save_monitoring_answer_node,
    format_monitoring_update_prompt,
) = make_phase_nodes(
    "monitoring_",
    MONITORING_OUTPUT_DIR,
    "Monitoring",
    "Entering Monitoring Q&A Phase to collect your answers...",
    "Monitoring Phase is complete. Proceeding to next phase...",
)


def prepare_research_prompt(ctx, node_input):
    original_task = ctx.state.get("original_task", "")
    planning_docs = read_generated_documents(
        [
            ARCH_OUTPUT_DIR,
            UI_UX_OUTPUT_DIR,
            TASK_PLAN_OUTPUT_DIR,
            ENV_SETUP_OUTPUT_DIR,
            CODER_OUTPUT_DIR,
            TEST_WRITER_OUTPUT_DIR,
            DEBUGGER_OUTPUT_DIR,
            SECURITY_OUTPUT_DIR,
            PERFORMANCE_OUTPUT_DIR,
            CODE_REVIEW_OUTPUT_DIR,
        ]
    )
    file_contents = original_task + "\n" + planning_docs
    return f"Based on the project files:\n\n{file_contents}\n\nInstruction: Please perform Research tasks based on your system instructions. Output the created/updated files."


(
    process_research_response,
    ask_research_questions_node,
    save_research_answer_node,
    format_research_update_prompt,
) = make_phase_nodes(
    "research_",
    RESEARCH_OUTPUT_DIR,
    "Research",
    "Entering Research Q&A Phase to collect your answers...",
    "Research Phase is complete. Proceeding to next phase...",
)


def end_workflow_node(ctx, node_input):
    return node_input


_root_agent_workflow = Workflow(
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
                "done": validate_build_node,
            },
        ),
        (
            validate_build_node,
            {
                "validation_passed": prepare_test_writer_prompt,
                "validation_failed": prepare_coder_prompt,
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
                "done": prepare_code_review_prompt,
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
        (prepare_code_review_prompt, code_review_agent),
        (code_review_agent, process_code_review_response),
        (
            process_code_review_response,
            {
                "ask_questions": ask_code_review_questions_node,
                "done": check_implementation_loop_node,
            },
        ),
        (
            check_implementation_loop_node,
            {
                "done": prepare_cicd_prompt,
                "loop_back": prepare_coder_prompt,
            },
        ),
        (ask_code_review_questions_node, save_code_review_answer_node),
        (
            save_code_review_answer_node,
            {
                "ask_more": ask_code_review_questions_node,
                "finished": format_code_review_update_prompt,
            },
        ),
        (format_code_review_update_prompt, code_review_agent),
        (prepare_cicd_prompt, cicd_agent),
        (cicd_agent, process_cicd_response),
        (
            process_cicd_response,
            {
                "ask_questions": ask_cicd_questions_node,
                "done": run_playwright_tests_node,
            },
        ),
        (
            run_playwright_tests_node,
            {
                "tests_passed": prepare_notifier_prompt,
                "tests_failed": prepare_coder_prompt,
            },
        ),
        (ask_cicd_questions_node, save_cicd_answer_node),
        (
            save_cicd_answer_node,
            {
                "ask_more": ask_cicd_questions_node,
                "finished": format_cicd_update_prompt,
            },
        ),
        (format_cicd_update_prompt, cicd_agent),
        (prepare_notifier_prompt, notifier_agent),
        (notifier_agent, process_notifier_response),
        (
            process_notifier_response,
            {
                "ask_questions": ask_notifier_questions_node,
                "done": prepare_monitoring_prompt,
            },
        ),
        (ask_notifier_questions_node, save_notifier_answer_node),
        (
            save_notifier_answer_node,
            {
                "ask_more": ask_notifier_questions_node,
                "finished": format_notifier_update_prompt,
            },
        ),
        (format_notifier_update_prompt, notifier_agent),
        (prepare_monitoring_prompt, monitoring_agent),
        (monitoring_agent, process_monitoring_response),
        (
            process_monitoring_response,
            {
                "ask_questions": ask_monitoring_questions_node,
                "done": prepare_research_prompt,
            },
        ),
        (ask_monitoring_questions_node, save_monitoring_answer_node),
        (
            save_monitoring_answer_node,
            {
                "ask_more": ask_monitoring_questions_node,
                "finished": format_monitoring_update_prompt,
            },
        ),
        (format_monitoring_update_prompt, monitoring_agent),
        (prepare_research_prompt, research_agent),
        (research_agent, process_research_response),
        (
            process_research_response,
            {
                "ask_questions": ask_research_questions_node,
                "done": end_workflow_node,
            },
        ),
        (ask_research_questions_node, save_research_answer_node),
        (
            save_research_answer_node,
            {
                "ask_more": ask_research_questions_node,
                "finished": format_research_update_prompt,
            },
        ),
        (format_research_update_prompt, research_agent),
    ],
    description="A workflow that takes a project idea, generates structured planning documents, designs the architecture, creates UI/UX specs, and creates a task plan, sets up the environment, codes, writes tests, debugs, and performs security and performance analysis, and finally code review.",
)

root_agent = _root_agent_workflow
