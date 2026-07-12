# Release Tier: T3 — Desktop

**NSIS installer** + MCPB + webapp.

This repo ships a Tauri 2.0 NSIS installer with embedded PyInstaller backend.
The full build pipeline (`just build-native`) requires Rust, MSVC, Node.js,
and ~10 min. Build only for major releases.

See `mcp-central-docs/standards/RELEASE_TIERS.md` for the fleet standard.
