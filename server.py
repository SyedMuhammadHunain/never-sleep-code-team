import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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


@app.websocket("/api/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    process = None
    try:
        # Initial prompt
        data = await websocket.receive_text()
        req = json.loads(data)
        prompt = req.get("prompt", "")

        process = await asyncio.create_subprocess_exec(
            "uv", "run", "agents-cli", "run", prompt,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        async def read_stream(stream, stream_type):
            while True:
                chunk = await stream.read(1024)
                if not chunk:
                    break
                await websocket.send_text(json.dumps({"type": stream_type, "data": chunk.decode(errors="replace")}))

        async def write_stdin():
            try:
                while True:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    if msg.get("type") == "input":
                        process.stdin.write((msg.get("data", "") + "\n").encode())
                        await process.stdin.drain()
            except WebSocketDisconnect:
                pass

        asyncio.create_task(read_stream(process.stdout, "stdout"))
        asyncio.create_task(read_stream(process.stderr, "stderr"))
        asyncio.create_task(write_stdin())

        await process.wait()
        await websocket.send_text(json.dumps({"type": "done", "code": process.returncode}))
    except WebSocketDisconnect:
        if process and process.returncode is None:
            process.terminate()

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
