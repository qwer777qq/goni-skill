@echo off
setlocal
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or later is required. Install Python and run this file again.
  pause
  exit /b 1
)
python -X utf8 "%~dp0scripts\install.py"
if errorlevel 1 (
  echo Installation failed. See the message above.
  pause
  exit /b 1
)
echo Installation complete. Double-click START.cmd to open the workspace.
pause
