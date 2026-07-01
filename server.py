import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8000"],
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
        text=True,
    )

    return {
        "output": result.stdout,
        "error": result.stderr,
    }

@app.get("/api/workflow")
def get_workflow():
    from app.agent import root_agent
    from google.adk.workflow import START

    nodes_set = set()
    edges = []

    def get_node_name(node):
        if node == START:
            return "START"
        return getattr(node, "name", getattr(node, "__name__", str(node)))

    if hasattr(root_agent, "edges"):
        for idx, (source, target) in enumerate(root_agent.edges):
            source_name = get_node_name(source)
            nodes_set.add(source_name)

            if isinstance(target, dict):
                for route, dst in target.items():
                    dst_name = get_node_name(dst)
                    nodes_set.add(dst_name)
                    edges.append({"id": f"edge_{idx}_{route}", "source": source_name, "target": dst_name, "label": route})
            else:
                dst_name = get_node_name(target)
                nodes_set.add(dst_name)
                edges.append({"id": f"edge_{idx}", "source": source_name, "target": dst_name})

    return {
        "nodes": [{"id": n, "label": n} for n in nodes_set],
        "edges": edges
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
