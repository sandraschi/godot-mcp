"""MCP prompt templates for guided LLM interactions."""

from pydantic import BaseModel


class PromptTemplate(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    parameters: list[dict] = []


PROMPTS: dict[str, PromptTemplate] = {
    "scene_description": PromptTemplate(
        id="scene_description",
        name="Describe Scene",
        description="Generate a rich description of the current Godot scene.",
        system_prompt="You are a 3D scene analyst. Describe what you see in technical and artistic terms.",
        user_prompt_template="The Godot scene has {node_count} nodes. Scene tree:\n{scene_tree}\n\nDescribe this scene.",
        parameters=[{"name": "node_count", "type": "int"}, {"name": "scene_tree", "type": "string"}],
    ),
    "gdscript_generator": PromptTemplate(
        id="gdscript_generator",
        name="GDScript Generator",
        description="Generate GDScript code from a natural language description.",
        system_prompt="You are a Godot 4 GDScript expert. Write clean, idiomatic GDScript code.",
        user_prompt_template="Write a GDScript for: {specification}\n\nNode type: {node_type}",
        parameters=[
            {"name": "specification", "type": "string"},
            {"name": "node_type", "type": "string", "default": "Node3D"},
        ],
    ),
    "artifact_description": PromptTemplate(
        id="artifact_description",
        name="Artifact Description",
        description="Generate a marketplace description for a game asset.",
        system_prompt="You are a game asset cataloger. Write concise, appealing descriptions.",
        user_prompt_template="Write a description for a Godot {artifact_type} named '{name}'. Key features: {features}",
        parameters=[
            {"name": "artifact_type", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "features", "type": "string"},
        ],
    ),
    "material_advisor": PromptTemplate(
        id="material_advisor",
        name="Material Advisor",
        description="Suggest PBR material parameters for a given use case.",
        system_prompt="You are a materials scientist for game engines. Suggest PBR parameters.",
        user_prompt_template="Suggest PBR material settings for: {description}\nFormat as JSON: color hex, roughness, metallic",
        parameters=[{"name": "description", "type": "string"}],
    ),
}


def get_prompt(prompt_id: str) -> PromptTemplate | None:
    return PROMPTS.get(prompt_id)


def list_prompts() -> list[PromptTemplate]:
    return list(PROMPTS.values())
