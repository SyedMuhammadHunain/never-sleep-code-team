<div align="center">
  
  # 🤖 Never Sleep Code Team
  *A multi-agent graph workflow for autonomous code generation and validation*
  
  [![Python](https://img.shields.io/badge/Python->=3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
  [![Google ADK](https://img.shields.io/badge/Google_ADK-2.0-blue?style=flat-square)](https://github.com/google/agent-development-kit)
  [![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-orange?style=flat-square)](https://ai.google.dev/)

  [Features](#features) • [Architecture](#architecture) • [Installation](#installation) • [Usage](#usage)

</div>

A powerful multi-agent system powered by **Google ADK 2.0**. It orchestrates specialized AI agents to autonomously plan, architect, test, code, review, and secure complete applications based solely on your natural language prompts.

## ✨ Features

- 🧠 **Autonomous Planning** - Requirement and Architecture agents scaffold specs, design docs, and implementation steps.
- 🧪 **Test-Driven Development (TDD)** - Test Writer agent generates automated tests before implementation.
- 💻 **Code Generation** - Coder agent implements application logic based on the test and architecture specs.
- 🛡️ **Built-in Quality & Security** - Dedicated Security and Code Review agents scan for vulnerabilities and enforce logic checks.
- 🔄 **Graph Workflow** - Fully orchestrated state machine via ADK nodes and events.

## 🏗️ Architecture

The workflow routes through the following 15 specialized AI agents:
1. **Requirement Agent**: Scaffolds requirements and plans.
2. **Architecture Agent**: Generates system design.
3. **UI/UX Designer Agent**: Creates UI/UX specifications and design documents.
4. **Task Planner Agent**: Breaks down tasks and creates implementation plans.
5. **Env Setup Agent**: Generates environment configuration (e.g. `mise.toml`).
6. **Coder Agent**: Implements the application logic incrementally.
7. **Test Writer Agent**: Creates automated tests (TDD).
8. **Debugger Agent**: Identifies and resolves errors or bugs.
9. **Security Agent**: Scans for vulnerabilities.
10. **Performance Agent**: Analyzes and optimizes code performance.
11. **Code Review Agent**: Enforces code quality and logic checks.
12. **CI/CD Agent**: Generates deployment and pipeline configurations.
13. **Notifier Agent**: Handles alerts and notification configurations.
14. **Monitoring Agent**: Configures observability and monitoring tools.
15. **Research Agent**: Conducts deep technical research for complex problems.

> [!NOTE]
> The agents are powered by **Gemini 2.5 Flash** using the `NeverSleepLlmAgent` wrapper to handle advanced output parsing, JSON schema compliance, and quota safety.

## 🚀 Installation

Ensure you have Python 3.11+ and the Google Agent Development Kit (ADK) installed.

```bash
# Clone the repository and install dependencies using uv
uv sync

# Copy environment variables and add your Google API key
cp .env.example .env
```

## 💻 Usage

You can run the agent locally through the `agents-cli` tool.

**Run an interactive playground:**
```bash
agents-cli playground
```

**Run a single, one-off task:**
```bash
agents-cli run "Create a fast and secure Todo app in React"
```
