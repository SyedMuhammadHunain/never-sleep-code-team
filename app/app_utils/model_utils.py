from google.adk.models.google_llm import Gemini
from google.genai import types


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
