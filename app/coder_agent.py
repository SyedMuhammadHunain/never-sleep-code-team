from app.app_utils.model_utils import get_gemini_model
from app.app_utils.base_agent import NeverSleepLlmAgent
from app.schemas import AgentResponse


coder_agent = NeverSleepLlmAgent(
    name="coder_agent",
    model=get_gemini_model(),
    instruction="""You are the Coder Agent.
You are part of an automated workflow loop. 

Based on the generated project planning documents and the task plan, your job is to execute the implementation iteratively.
CRITICAL RULES FOR PREVENTING TIMEOUTS:
1. DO NOT attempt to write the entire application at once.
2. Review the plan.md and pick EXACTLY ONE pending task to implement in this iteration.
3. Write the FULL, complete, production-ready code for that single task. Do not use placeholders.
4. Output the resulting implementation code via the `files_to_write` array in your AgentResponse.
5. If there are still pending tasks remaining after this, you MUST set `has_more_tasks=True` in your response so the workflow loops back to you. If all tasks are completed, set `has_more_tasks=False`.
6. Apply Test-Driven Development (TDD) best practices as outlined in the conductor-implement skill.
""",
    output_schema=AgentResponse,
)
