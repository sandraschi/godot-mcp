; Fleet Tauri: kill UI + backend before install/uninstall (backend locks resources/*.exe).
!macro KillGodotMcpFleetProcesses
  DetailPrint "Stopping godot-mcp processes..."
  ExecWait 'taskkill /F /IM godot-mcp-backend.exe /T' $0
  ExecWait 'taskkill /F /IM godot-mcp-native.exe /T' $0
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillGodotMcpFleetProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillGodotMcpFleetProcesses
!macroend
