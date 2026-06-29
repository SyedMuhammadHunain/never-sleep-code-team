from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.agents import LlmAgent

# Monkey patch LlmAgent to inject generate_content_config with higher temperature globally
# to prevent RECITATION safety blocks on boilerplate code.
original_init = LlmAgent.__init__


def patched_init(self, *args, **kwargs):
    if (
        "generate_content_config" not in kwargs
        or kwargs["generate_content_config"] is None
    ):
        kwargs["generate_content_config"] = types.GenerateContentConfig(temperature=0.7)
    original_init(self, *args, **kwargs)


LlmAgent.__init__ = patched_init


def get_gemini_model():
    return Gemini(
        model="gemini-flash-lite-latest",
        retry_options=types.HttpRetryOptions(
            attempts=5,
            exp_base=5,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504],
        ),
    )
