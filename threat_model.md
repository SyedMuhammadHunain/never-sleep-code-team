# STRIDE Threat Model: `never-sleep-code-team` Agent Workflow

## 1. Analyze System Boundaries
- **Entry Points:** The workflow is triggered by an initial `original_task` (user prompt). Various agents take this input and output structured plans and code.
- **Data Storage Layers:** Files are written to local directories under `Output/` (e.g. `Output/requirement_agent_output_files`, `Output/coder_output_files`).
- **Execution Boundaries:** `app/agent.py` executes shell commands in `validate_build_node` and `run_playwright_tests_node` using `subprocess.run` (e.g. `npm install`, `npm run build`, `npx playwright test`).

## 2. STRIDE Evaluation

### Spoofing
- **Threat:** Caller identity boundaries are not verified when accepting the `original_task` or answering clarifying questions. Additionally, the new FastAPI server exposes `/api/run` without any authentication or API keys.
- **Impact:** Any user or process interacting with the workflow (or network) can impersonate legitimate users and trigger expensive agent operations.
- **Mitigation:** Implement authentication/authorization (e.g., API keys, OAuth) before kicking off workflows or accepting requests on the FastAPI server.

### Tampering
- **Threat:** The workflow uses `subprocess.run(["npm", "install"])` inside `CODER_OUTPUT_DIR`. An attacker or compromised agent could generate malicious `package.json` with dangerous post-install scripts. Furthermore, user input from the Angular frontend is passed directly to `agents-cli run` (Prompt Injection).
- **Impact:** Remote Code Execution (RCE) on the host machine running the workflow, or agents being manipulated into executing harmful tool calls.
- **Mitigation:** Sandbox the build validation step (e.g., using Docker containers) and disable lifecycle scripts (`--ignore-scripts`). Rely on the `.agents/scripts/validate_tool_call.py` hook to block destructive commands from prompt injection.

### Repudiation
- **Threat:** There is limited secure logging of critical transactions (e.g. which agent generated which exact shell command or file). The FastAPI server also lacks request logging with client IPs.
- **Impact:** Difficult to audit if an agent goes rogue or if a malicious prompt injection causes the system to run harmful commands.
- **Mitigation:** Implement structured, append-only audit logging for all `subprocess.run` executions, file writes, and incoming API requests.

### Information Disclosure
- **Threat:** Error messages from failed builds and tests are directly appended to `coder_pending_questions`. Additionally, the FastAPI `/api/run` endpoint returns raw `stderr` and `stdout` from the CLI.
- **Impact:** Raw stack traces, environment variables, or local file paths from the host system may leak into the LLM context or to unauthenticated API clients.
- **Mitigation:** Sanitize and redact sensitive information from `stderr`/`stdout` before passing it back into the agent context or the HTTP response.

### Denial of Service
- **Threat:** Overarching `check_implementation_loop_node` can cause infinite loops. The FastAPI server lacks rate limiting on the `/api/run` endpoint.
- **Impact:** A misbehaving `coder_agent` or a malicious API client can exhaust API quotas (Gemini credits) and local compute resources.
- **Mitigation:** Implement a hard cap on the total number of workflow iterations and add rate limiting/throttling to the FastAPI server.

### Elevation of Privilege
- **Threat:** The workflow agents have the implicit privilege to write to the local filesystem and execute arbitrary code via the validation steps.
- **Impact:** If an agent is manipulated via prompt injection, it could write files outside of `Output/` (e.g., using path traversal `../`) in `save_generated_files` and execute arbitrary scripts.
- **Mitigation:** Restrict `os.path.join` in `save_generated_files` by verifying that the resulting path is strictly within the intended `output_dir` (preventing path traversal). Sandbox all executions.
