import os
from typing import List, Dict
from pydantic import BaseModel
from google.adk.workflow import Workflow, START
from google.adk.agents import LlmAgent

FILE_SEQUENCE = [
    "Product_Requirements.md",
    "Architecture.md",
    "Design.md",
    "Data_Model.md",
    "API_Spec.md",
    "Task_List.md",
    "Test_Plan.md",
    "Security_Plan.md"
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


class RequirementRequest(BaseModel):
    task: str


class FileToWrite(BaseModel):
    filename: str
    content: str


class AgentResponse(BaseModel):
    files_to_write: List[FileToWrite]
    clarifying_questions: List[str]
    message_to_user: str


requirement_agent = LlmAgent(
    name="requirement_agent",
    model="gemini-flash-lite-latest",
    instruction=f"""You are the Requirement Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{_load_skill_rules()}
</SKILL_DOCUMENT>""",
    output_schema=AgentResponse,
    output_key="requirement_response",
)


def adk_request_input(prompt_text: str) -> str:
    return input(prompt_text)


def abort_if_planning_files_exist():
    for file_name in FILE_SEQUENCE:
        if os.path.exists(file_name):
            raise FileExistsError(f"Abort: Planning file {file_name} already exists. Start with a clean workspace.")


def collect_design_preferences(conversation_history: List[str]):
    style = adk_request_input("Provide style direction for Design.md: ")
    color = adk_request_input("Provide color palette for Design.md: ")
    conversation_history.append(f"Style direction: {style}")
    conversation_history.append(f"Color palette: {color}")


def build_agent_prompt(task: str, file_name: str, conversation_history: List[str]) -> str:
    history_text = "\n".join(conversation_history)
    return f"Task: {task}\nTarget File: {file_name}\nHistory:\n{history_text}\nPlease generate the file."


def ask_clarifying_questions(questions: List[str], conversation_history: List[str]):
    for question in questions:
        answer = adk_request_input(f"{question}\nAnswer: ")
        conversation_history.append(f"Q: {question}")
        conversation_history.append(f"A: {answer}")


def fetch_valid_agent_response(task: str, file_name: str, conversation_history: List[str]) -> AgentResponse:
    while True:
        prompt = build_agent_prompt(task, file_name, conversation_history)
        
        raw_response = requirement_agent({"task": prompt})
        response: AgentResponse = raw_response.get('requirement_response')
        
        if response.clarifying_questions:
            ask_clarifying_questions(response.clarifying_questions, conversation_history)
            continue
            
        if response.files_to_write:
            return response
            
        conversation_history.append("System: Please provide files_to_write or clarifying_questions.")


def _write_planning_files(files_to_write: List[FileToWrite]) -> str:
    if not files_to_write:
        return ""
        
    status_messages = []
    for file_obj in files_to_write:
        with open(file_obj.filename, "w") as file:
            file.write(file_obj.content)
        status_messages.append(f"Successfully created/updated: `{file_obj.filename}`")
        
    return "\n".join(status_messages) + "\n"


def process_single_file(task: str, file_name: str, conversation_history: List[str]):
    while True:
        agent_response = fetch_valid_agent_response(task, file_name, conversation_history)
        
        draft = agent_response.files_to_write[0]
        print(f"\n--- DRAFT: {draft.filename} ---\n{draft.content}\n-----------------------")
        
        feedback = adk_request_input(f"Approve {file_name}? (yes/no/changes): ")
        if feedback.strip().lower() in ['yes', 'y', 'approve']:
            _write_planning_files(agent_response.files_to_write)
            print(f"Confirmed and saved {file_name}.")
            break
        
        conversation_history.append(f"User feedback for {file_name}: {feedback}")


def process_agent_response(node_input: dict) -> str:
    abort_if_planning_files_exist()
    
    task = node_input.get("task", "Generate project planning files.")
    conversation_history = []
    
    for file_name in FILE_SEQUENCE:
        if file_name == "Design.md":
            collect_design_preferences(conversation_history)
            
        process_single_file(task, file_name, conversation_history)
        
    return "All planning files generated successfully."


root_agent = Workflow(
    name="never_sleep_code_team_workflow",
    edges=[(START, process_agent_response)],
    description="A workflow that takes a project idea and generates structured planning documents in sequence.",
    input_schema=RequirementRequest,
)
