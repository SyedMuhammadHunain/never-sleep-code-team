import asyncio
from app import app
from google.adk import Runner
from google.genai import types


from google.adk.sessions import InMemorySessionService


async def main():
    print("Running workflow test...")
    runner = Runner(
        app=app,
        app_name="test_app",
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )
    try:
        prompt = "Create a simple landing page"
        while True:
            new_message = types.Content(parts=[types.Part.from_text(text=prompt)])
            print(f"Sending message: {prompt}")
            is_finished = False
            for event in runner.run(
                user_id="test_user", session_id="test_session", new_message=new_message
            ):
                print("EVENT:", event.output)
                if (
                    isinstance(event.output, str)
                    and "Workflow finished!" in event.output
                ):
                    is_finished = True
            if is_finished:
                break
            prompt = "I don't have a preference, you can choose."
        print("Workflow finished successfully!")
    except Exception:
        print("Workflow failed!")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
