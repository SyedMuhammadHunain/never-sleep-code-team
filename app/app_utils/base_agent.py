from google.adk.agents import LlmAgent
from google.genai import types


class NeverSleepLlmAgent(LlmAgent):
    """
    A custom wrapper around LlmAgent that provides project-specific defaults.
    Specifically, it bumps the temperature to 0.7 to prevent the LLM from
    halting with RECITATION safety blocks when generating standard code templates.
    """

    def __init__(self, **kwargs):
        if (
            "generate_content_config" not in kwargs
            or kwargs["generate_content_config"] is None
        ):
            kwargs["generate_content_config"] = types.GenerateContentConfig(
                temperature=0.7
            )
        super().__init__(**kwargs)
