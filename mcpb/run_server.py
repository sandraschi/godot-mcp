"""Entry point for PyInstaller-bundled godot-mcp backend."""

import _strptime  # noqa: F401
import sys

sys.path.insert(0, "src")

from godot_mcp.server import main

if __name__ == "__main__":
    main()

