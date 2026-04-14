@echo off
title SOVEREIGN AI TERMINAL
color 0B
cls

echo.
echo  ======================================================
echo  SOVEREIGN NATIVE APP LAUNCHER
echo  ======================================================
echo  Booting Local Intelligence Network...
echo.

:: Ensure we are in the Sovereign main folder
cd /d "%~dp0"

:: Start Ollama (local AI engine) in background
echo  [1/3] Starting Ollama Local AI Engine...
start /B ollama serve >nul 2>&1
timeout /t 3 /nobreak >nul

:: Start the Python Dashboard Server in background
echo  [2/3] Starting Dashboard Server...
start /B python dashboard_server.py >nul 2>&1
timeout /t 3 /nobreak >nul

:: Start the Electron Wrapper
echo  [3/3] Launching Sovereign Dashboard...
cd desktop_app
call npx electron .

exit
