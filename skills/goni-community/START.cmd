@echo off
setlocal
where python >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or later is required. Run INSTALL.cmd after installing Python.
  pause
  exit /b 1
)
python -X utf8 "%~dp0scripts\start.py" %*
if errorlevel 1 pause
