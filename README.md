# Never Sleep Code Team

A Google ADK-powered graph workflow project for automated multi-agent coding. 
This project orchestrates specialized AI agents (Requirement, Architecture, Testing, Coding, Security, and Code Review) to autonomously generate and validate complete applications based on user prompts.

## Architecture

- **ADK 2.0 Graph Workflow**: Nodes are defined in `app/agent.py`.
- **LLM**: Gemini 2.5 Flash via `NeverSleepLlmAgent`.
- **Agents**:
  - `Requirement Agent`: Scaffolds specs and plans.
  - `Architecture Agent`: Generates system design.
  - `Test Writer`: Creates automated tests (TDD).
  - `Coder Agent`: Implements the application logic.
  - `Security Agent`: Scans for vulnerabilities.
  - `Code Reviewer`: Enforces quality and logic checks.

## Development

- **Prerequisites**: Python >= 3.11, Google ADK.
- **Install dependencies**: `uv sync`
- **Run playground**: `agents-cli playground`
- **Run one-off task**: `agents-cli run "Create a Todo app"`

## Environment
Copy `.env.example` to `.env` and set your `GOOGLE_API_KEY`.
