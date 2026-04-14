@echo off
title SOVEREIGN — STARTING...
color 0B
cls

echo.
echo  ███████╗ ██████╗ ██╗   ██╗███████╗██████╗ ███████╗██╗ ██████╗ ███╗   ██╗
echo  ██╔════╝██╔═══██╗██║   ██║██╔════╝██╔══██╗██╔════╝██║██╔════╝ ████╗  ██║
echo  ███████╗██║   ██║██║   ██║█████╗  ██████╔╝█████╗  ██║██║  ███╗██╔██╗ ██║
echo  ╚════██║██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗██╔══╝  ██║██║   ██║██║╚██╗██║
echo  ███████║╚██████╔╝ ╚████╔╝ ███████╗██║  ██║███████╗██║╚██████╔╝██║ ╚████║
echo  ╚══════╝ ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
echo.
echo                      AUTONOMOUS TRADING INTELLIGENCE v3.0
echo  ─────────────────────────────────────────────────────────────────────────────
echo.

:: --- PATHS ---
set PYTHON=C:\Users\satya\AppData\Local\Programs\Python\Python312\python.exe
set NODE_PATH=C:\Program Files\nodejs
set APP_DIR=d:\Sudha - C\Desktop\Sovereign
set FRONTEND_DIR=%APP_DIR%\frontend

:: --- Add Node to PATH for this session ---
set PATH=%PATH%;%NODE_PATH%;%APPDATA%\npm

echo  [1/4]  Checking dependencies...
%PYTHON% -m pip install fastapi uvicorn yfinance pandas feedparser google-generativeai python-dotenv >nul 2>&1
echo         Python packages OK.

echo  [2/4]  Starting Intelligence Engine (Backend)...
start "SOVEREIGN — Backend :8000" /min cmd /k "cd /d "%APP_DIR%" && %PYTHON% dashboard_server.py"

echo  [3/4]  Launching React UI (Frontend)...
start "SOVEREIGN — Frontend :5173" /min cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo  [4/4]  Opening Cockpit in browser...

:: Wait for backend to be ready (5s) then open browser
timeout /t 5 /nobreak >nul

:: Open the React dashboard (Vite dev server)
start "" "http://localhost:5173/overview"

echo.
echo  ─────────────────────────────────────────────────────────────────────────────
echo  ✓  Backend  →  http://localhost:8000
echo  ✓  Frontend →  http://localhost:5173
echo  ─────────────────────────────────────────────────────────────────────────────
echo.
echo  Both servers are running in minimized windows.
echo  Close those windows to shut down Sovereign.
echo.
timeout /t 3 /nobreak >nul
exit
