# Per-repo fleet start config for godot-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'godot-mcp'
    BackendPort  = 10993
    FrontendPort = 10992
    HealthPath   = '/api/v1/status'
    WebRoot      = 'webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'godot_mcp.server:app'
        # Slow starter: heavy import (fastmcp + 95 tools) + bridge probe.
        # Central default is 20s; godot needs 40s cold.
        HealthTimeoutSec = 40
        Env           = @{ WEB_PORT = '10993' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
