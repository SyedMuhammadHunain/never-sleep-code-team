import os


def load_skill_file(skill_name: str, default_text: str = "") -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    paths_to_check = [
        os.path.join(base_dir, ".agents", "skills", skill_name, "SKILL.md"),
        os.path.expanduser(f"~/.agents/skills/{skill_name}/SKILL.md"),
        os.path.expanduser(f"~/.gemini/config/skills/{skill_name}/SKILL.md"),
    ]

    skill_path = None
    for p in paths_to_check:
        if os.path.exists(p):
            skill_path = p
            break

    if not skill_path:
        if default_text:
            return default_text
        raise FileNotFoundError(
            f"CRITICAL ERROR: Required skill '{skill_name}' not found. "
            "The agent cannot function without this skill."
        )

    with open(skill_path, "r") as skill_file:
        content = skill_file.read()
        return content.replace("{", "[").replace("}", "]")
