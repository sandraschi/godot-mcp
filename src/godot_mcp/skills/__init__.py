"""Skills provider — exposes SKILL.md resources for FastMCP clients.

When the MCP client lists resources, this provider returns skill URIs
that tell LLMs how to use this server's tools effectively.
"""

from pathlib import Path

SKILLS_DIR = Path(__file__).parent


def get_skill_markdown(skill_name: str) -> str | None:
    skill_file = SKILLS_DIR / f"{skill_name}.md"
    if skill_file.exists():
        return skill_file.read_text(encoding="utf-8")
    return None


def list_skills() -> list[dict]:
    skills = []
    for f in SKILLS_DIR.glob("*.md"):
        if f.name == "__init__.md":
            continue
        skills.append({"name": f.stem, "uri": f"skill://{f.stem}/SKILL.md"})
    return skills
