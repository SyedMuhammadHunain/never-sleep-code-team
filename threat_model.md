# STRIDE Threat Model: `never-sleep-code-team` Agent Workflow

## 1. Analyze System Boundaries
- **Entry Points:** The workflow is triggered by an initial `original_task` (user prompt). Various agents take this input and output structured plans and code.
- **Data Storage Layers:** Files are written to local directories under `Output/` (e.g. `Output/requirement_agent_output_files`, `Output/coder_output_files`).
- **Execution Boundaries:** `app/agent.py` executes shell commands in `validate_build_node` and `run_playwright_tests_node` using `subprocess.run` (e.g. `npm install`, `npm run build`, `npx playwright test`).

## 2. STRIDE Evaluation

### Spoofing
- **Threat:** Caller identity boundaries are not verified when accepting the `original_task` or answering clarifying questions.
- **Impact:** Any user or process interacting with the workflow can impersonate legitimate users and trigger expensive agent operations.
- **Mitigation:** Implement authentication/authorization before kicking off the `_root_agent_workflow` or when continuing via `RequestInput`.

### Tampering
- **Threat:** The workflow uses `subprocess.run(["npm", "install"])` inside `CODER_OUTPUT_DIR`. An attacker or compromised agent could generate malicious `package.json` with dangerous post-install scripts.
- **Impact:** Remote Code Execution (RCE) on the host machine running the workflow.
- **Mitigation:** Sandbox the build validation step (e.g., using Docker containers) and disable lifecycle scripts during `npm install` (`--ignore-scripts`).

### Repudiation
- **Threat:** There is limited secure logging of critical transactions (e.g. which agent generated which exact shell command or file).
- **Impact:** Difficult to audit if an agent goes rogue or if a malicious prompt injection causes the system to run harmful commands.
- **Mitigation:** Implement structured, append-only audit logging for all `subprocess.run` executions and all file writes in `save_generated_files`.

### Information Disclosure
- **Threat:** Error messages (`e.stderr` and `e.stdout`) from failed builds and tests are directly appended to `coder_pending_questions` and passed back to the LLM.
- **Impact:** Raw stack traces, environment variables, or local file paths from the host system may leak into the LLM context, which might be logged or sent to an external provider (Gemini).
- **Mitigation:** Sanitize and redact sensitive information from `stderr`/`stdout` before passing it back into the agent context.

### Denial of Service
- **Threat:** While `build_retries` limits the build loop to 3 attempts, there is an overarching `check_implementation_loop_node` that loops back to `coder_agent` if `has_more_tasks` is true.
- **Impact:** A misbehaving `coder_agent` could return `has_more_tasks = true` indefinitely, leading to an infinite loop that exhausts API quotas and local compute resources.
- **Mitigation:** Implement a hard cap on the total number of workflow iterations or task loops across the entire execution graph.

### Elevation of Privilege
- **Threat:** The workflow agents have the implicit privilege to write to the local filesystem and execute arbitrary code via the validation steps.
- **Impact:** If an agent is manipulated via prompt injection, it could write files outside of `Output/` (e.g., using path traversal `../`) in `save_generated_files` and execute arbitrary scripts.
- **Mitigation:** Restrict `os.path.join` in `save_generated_files` by verifying that the resulting path is strictly within the intended `output_dir` (preventing path traversal). Sandbox all executions.
