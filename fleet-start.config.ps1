# Per-repo fleet start config for godot-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'godot-mcp'
    BackendPort  = 10993
    FrontendPort = 10992
    HealthPath   = '/api/v1/status'
    WebRoot      = 'D:\Dev\repos\godot-mcp\webapp'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'godot_mcp.server:app'
        Env           = @{ WEB_PORT = '10993' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
