# godot-mcp (MCPB Bundle)

Godot MCP server — Godot 4.0 engine control via WebSocket bridge, STL/GLB/OBJ import, GPU particles, animation, HTML5 export through MCP tools and REST API

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "godot-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "godot_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **godot-mcp**: Godot MCP server — Godot 4.0 engine control via WebSocket bridge, STL/GLB/OBJ import, GPU particles, animation, HTML5 export through MCP tools and REST API

## Requirements

- Python 3.12+
- uv
