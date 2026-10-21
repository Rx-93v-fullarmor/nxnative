@echo off
setlocal
cd /d "%~dp0.."
if exist "%NX_TOOLS_DIR%\runtime\python.exe" (
  "%NX_TOOLS_DIR%\runtime\python.exe" "scripts\start_webui.py" %*
) else (
  python "scripts\start_webui.py" %*
)
if errorlevel 1 pause
