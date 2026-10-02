@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo     APEX OSINT - Intelligence, Connected.
echo     Local-First Defensive Investigation Platform
echo ===================================================
echo.

:: 1. Check Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3 is not found in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

:: 2. Create virtual environment if missing
if not exist "venv" (
    echo [INFO] Creating Python virtual environment in .\venv...
    python -m venv venv
)

:: 3. Install backend dependencies
echo [INFO] Verifying backend dependencies...
call .\venv\Scripts\pip install -q -r backend\requirements.txt

:: 4. Check for .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating default .env from .env.example...
        copy .env.example .env >nul
    )
)

:: 5. Launch Backend in background
echo.
echo [INFO] Starting APEX OSINT Backend on http://127.0.0.1:8000 ...
start "APEX OSINT Backend" /min cmd /c "set PYTHONPATH=backend&& .\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: 6. Launch Frontend
echo [INFO] Starting Frontend Dev Server on http://127.0.0.1:5173 ...
if exist "frontend\node_modules" (
    cd frontend
    start "APEX OSINT Frontend" cmd /c "npm run dev"
    cd ..
) else (
    echo [INFO] Installing frontend dependencies...
    cd frontend
    npm install
    start "APEX OSINT Frontend" cmd /c "npm run dev"
    cd ..
)

echo.
echo ===================================================
echo     APEX OSINT is now active!
echo     Web GUI:    http://127.0.0.1:5173
echo     API Docs:   http://127.0.0.1:8000/docs
echo ===================================================
echo.
pause
