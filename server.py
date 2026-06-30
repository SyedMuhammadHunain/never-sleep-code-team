import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/run")
def run_agent(request: PromptRequest):
    result = subprocess.run(
        ["uv", "run", "agents-cli", "run", request.prompt],
        capture_output=True,
        text=True
    )
    return {"output": result.stdout, "error": result.stderr}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
