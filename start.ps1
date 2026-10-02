# APEX OSINT - PowerShell Startup Script

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    APEX OSINT - Intelligence, Connected." -ForegroundColor Cyan
Write-Host "    Local-First Defensive Investigation Platform" -ForegroundColor DarkCyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3 is not found in PATH. Please install Python 3.10+."
    exit 1
}

# Create venv if missing
if (-not (Test-Path "venv")) {
    Write-Host "[INFO] Creating virtual environment in .\venv..." -ForegroundColor Yellow
    python -m venv venv
}

# Install dependencies
Write-Host "[INFO] Checking backend requirements..." -ForegroundColor Yellow
& .\venv\Scripts\pip install -q -r backend\requirements.txt

# Copy .env if not exists
if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[INFO] Created .env configuration from template." -ForegroundColor Green
}

# Start Backend Process
Write-Host "[INFO] Starting Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='backend'; .\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000" -PassThru

# Start Frontend Process
Write-Host "[INFO] Starting Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location frontend; npm run dev" -PassThru

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    APEX OSINT is now active!" -ForegroundColor Green
Write-Host "    Web GUI:   http://127.0.0.1:5173" -ForegroundColor White
Write-Host "    API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan
