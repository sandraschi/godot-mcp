"""Entry point for godot-mcp (MCPB bundle / PyInstaller / direct uv run)."""

import _strptime  # noqa: F401
import sys
from pathlib import Path

# Resolve src/ relative to this file, not the CWD — MCPB and Claude Desktop
# may spawn the process with an arbitrary working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from godot_mcp.server import main

if __name__ == "__main__":
    main()
