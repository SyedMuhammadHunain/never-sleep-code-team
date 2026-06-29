import re

with open("app/agent.py", "r") as f:
    content = f.read()

factory_code = """
def make_phase_nodes(prefix: str, output_dir: str, display_name: str, qa_msg: str, done_msg: str):
    def process_response(ctx, node_input) -> Event:
        return process_phase_response(ctx, node_input, prefix, output_dir, qa_msg, done_msg)
    process_response.__name__ = f"process_{prefix}response"

    def ask_questions(ctx, node_input):
        return prompt_for_clarification(ctx, prefix)
    ask_questions.__name__ = f"ask_{prefix}questions_node"

    def save_answer(ctx, node_input):
        return store_user_answer(ctx, node_input, prefix)
    save_answer.__name__ = f"save_{prefix}answer_node"

    def format_prompt(ctx, node_input):
        if prefix == "task_planner_":
            msg = "Instruction: Now update the task plan files with these answers.\\nYou must return the full updated files in your `files_to_write` array."
        elif prefix == "test_writer_":
            msg = "Instruction: Now update the test files with these answers.\\nYou must return the full updated files in your `files_to_write` array."
        elif prefix == "debugger_":
            msg = "Instruction: Now update the code with these answers.\\nYou must return the full updated files in your `files_to_write` array."
        elif prefix == "code_review_":
            msg = "Instruction: Now update the code review feedback files with these answers.\\nYou must return the full updated files in your `files_to_write` array."
        else:
            msg = f"Instruction: Now update the {display_name} files with these answers.\\nYou must return the full updated files in your `files_to_write` array."
        return generate_update_prompt(node_input, msg)
    format_prompt.__name__ = f"format_{prefix}update_prompt"

    return process_response, ask_questions, save_answer, format_prompt

"""

# Insert the factory code right before `def check_implementation_loop_node`
content = content.replace(
    "def check_implementation_loop_node(ctx, node_input):",
    factory_code + "def check_implementation_loop_node(ctx, node_input):",
)

# Now, we regex replace the individual blocks.
# We'll match blocks starting with `def process_XXXX_response` and ending with `return generate_update_prompt(...)`

pattern = re.compile(
    r"def process_([a-z_]+)_response\(ctx, node_input\) -> Event:\n"
    r"\s+return process_phase_response\(\n"
    r"\s+ctx,\n"
    r"\s+node_input,\n"
    r'\s+"([a-z_]+_)",\n'
    r"\s+([A-Z_]+_OUTPUT_DIR),\n"
    r'\s+"([^"]+)",\n'
    r'\s+"([^"]+)",\n'
    r"\s+\)\n+"
    r"def ask_\1_questions_node\(ctx, node_input\):\n"
    r'\s+return prompt_for_clarification\(ctx, "\2"\)\n+'
    r"def save_\1_answer_node\(ctx, node_input\):\n"
    r'\s+return store_user_answer\(ctx, node_input, "\2"\)\n+'
    r"def format_\1_update_prompt\(ctx, node_input\):\n"
    r"\s+return generate_update_prompt\(\n"
    r"\s+node_input,\n"
    r'(?:\s+"""Instruction:.*?""",|\s+"Instruction:.*?",)\n'
    r"\s+\)",
    re.DOTALL,
)


def replacer(match):
    name = match.group(1)
    prefix = match.group(2)
    output_dir = match.group(3)
    qa_msg = match.group(4)
    done_msg = match.group(5)
    display_name = name.replace("_", " ").title().strip()
    return f"""(
    process_{name}_response,
    ask_{name}_questions_node,
    save_{name}_answer_node,
    format_{name}_update_prompt,
) = make_phase_nodes(
    "{prefix}", {output_dir}, "{display_name}",
    "{qa_msg}",
    "{done_msg}"
)"""


new_content = pattern.sub(replacer, content)

with open("app/agent.py", "w") as f:
    f.write(new_content)

print(f"Replaced {len(pattern.findall(content))} blocks.")
