import os
from google.adk.agents import LlmAgent
from app.schemas import AgentResponse


def _load_software_architecture_skill() -> str:
    skill_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        ".agents",
        "skills",
        "software-architecture",
        "SKILL.md",
    )

    if not os.path.exists(skill_path):
        raise FileNotFoundError(
            f"CRITICAL ERROR: Required skill file not found at {skill_path}. "
            "The agent cannot function without this skill."
        )

    with open(skill_path, "r") as skill_file:
        return skill_file.read()


instruction = f"""You are the Architecture Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{_load_software_architecture_skill()}
</SKILL_DOCUMENT>

Based on the user's task and the existing planning documents (e.g., PRD.md, TechSpec.md), design a robust architecture. You must provide the full content for the generated architecture file (e.g., Architecture.md) in `files_to_write`.

CRITICAL INSTRUCTIONS TO ENFORCE:
1. ANTI-NIH SYNDROME: You MUST NOT propose custom React Context for global state. You MUST mandate an established library like Zustand or Redux. Do not invent your own solutions.
2. NAMING BANS: You MUST explicitly ban generic folder/file names like `utils`, `helpers`, `common`, or `shared` in your directory structure diagram. Use domain-specific names.
3. SIZE LIMITS: You must explicitly state that functions should be kept under 80 lines and files under 200 lines.

You MUST include the following compliance checklist at the very bottom of the generated Architecture.md file:
## Compliance Checklist
- [ ] Did I use an external library (e.g., Zustand) instead of custom React Context?
- [ ] Are generic folder names (`utils`, `helpers`) completely banned?
- [ ] Are function/file size constraints explicitly mentioned?
"""

architecture_agent = LlmAgent(
    name="architecture_agent",
    model="gemini-flash-lite-latest",
    instruction=instruction,
    output_schema=AgentResponse,
)
