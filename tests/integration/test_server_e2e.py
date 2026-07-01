import json
import logging
import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from typing import Any

import pytest  # type: ignore
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000"
RUN_URL = BASE_URL + "/api/run"

HEADERS = {"Content-Type": "application/json"}


def log_output(pipe: Any, log_func: Any) -> None:
    """Log the output from the given pipe."""
    for line in iter(pipe.readline, ""):
        log_func(line.strip())


def start_server() -> subprocess.Popen[str]:
    """Start the FastAPI server using subprocess and log its output."""
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    env = os.environ.copy()
    env["INTEGRATION_TEST"] = "TRUE"
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )

    # Start threads to log stdout and stderr in real-time
    threading.Thread(
        target=log_output, args=(process.stdout, logger.info), daemon=True
    ).start()
    threading.Thread(
        target=log_output, args=(process.stderr, logger.error), daemon=True
    ).start()

    return process


def wait_for_server(timeout: int = 90, interval: int = 1) -> bool:
    """Wait for the server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/docs", timeout=10)
            if response.status_code == 200:
                logger.info("Server is ready")
                return True
        except RequestException:
            pass
        time.sleep(interval)
    logger.error(f"Server did not become ready within {timeout} seconds")
    return False


@pytest.fixture(scope="session")
def server_fixture(request: Any) -> Iterator[subprocess.Popen[str]]:
    """Pytest fixture to start and stop the server for testing."""
    logger.info("Starting server process")
    server_process = start_server()
    if not wait_for_server():
        pytest.fail("Server failed to start")
    logger.info("Server process started")

    def stop_server() -> None:
        logger.info("Stopping server process")
        server_process.terminate()
        server_process.wait()
        logger.info("Server process stopped")

    request.addfinalizer(stop_server)
    yield server_process


def test_api_run(server_fixture: subprocess.Popen[str]) -> None:
    """Test the custom run API functionality."""
    logger.info("Starting run API test")

    data = {
        "prompt": "test prompt",
    }
    response = requests.post(
        RUN_URL, headers=HEADERS, json=data, timeout=60
    )
    assert response.status_code == 200

    resp_data = response.json()
    assert "output" in resp_data

def test_api_workflow(server_fixture: subprocess.Popen[str]) -> None:
    """Test the workflow graph API functionality."""
    logger.info("Starting workflow API test")

    response = requests.get(f"{BASE_URL}/api/workflow", timeout=10)
    assert response.status_code == 200

    resp_data = response.json()
    assert "nodes" in resp_data
    assert "edges" in resp_data
