from app.app_utils.model_utils import get_gemini_model
from app.app_utils.base_agent import NeverSleepLlmAgent
from app.schemas import AgentResponse
from app.app_utils.skill_loader import load_skill_file

security_agent = NeverSleepLlmAgent(
    name="security_agent",
    model=get_gemini_model(),
    instruction=f"""You are the Security Agent.
Your absolute source of truth lies in the file below:

<SKILL_DOCUMENT>
{load_skill_file("threat-modeling-expert")}
</SKILL_DOCUMENT>

You must act as the Security Agent, strictly follow the skill document to perform threat modeling and security analysis.
Your output MUST include files covering the following 8 steps from your instructions:
1. Define system scope and trust boundaries
2. Create data flow diagrams
3. Identify assets and entry points
4. Apply STRIDE to each component
5. Build attack trees for critical paths
6. Score and prioritize threats
7. Design mitigations
8. Document residual risks

Generate these findings in comprehensive markdown files (e.g., `ThreatModel.md` or individual files per step) via the `files_to_write` array in your AgentResponse.
""",
    output_schema=AgentResponse,
)
