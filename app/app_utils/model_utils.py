from google.adk.models.google_llm import Gemini
from google.genai import types


def get_gemini_model():
    return Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(
            attempts=3,
            exp_base=2,
            initial_delay=2,
            http_status_codes=[500, 503, 504],
        ),
    )
