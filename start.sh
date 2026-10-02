#!/usr/bin/env bash
set -e

echo "==================================================="
echo "    APEX OSINT - Intelligence, Connected."
echo "    Local-First Defensive Investigation Platform"
echo "==================================================="

# Check python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is required. Please install Python 3.10+."
    exit 1
fi

# Virtual environment
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment in ./venv..."
    python3 -m venv venv
fi

# Activate venv & install requirements
source venv/bin/activate
pip install -q -r backend/requirements.txt

# .env check
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
fi

# Start Backend
echo "[INFO] Starting Backend on http://127.0.0.1:8000 ..."
export PYTHONPATH=backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "[INFO] Starting Frontend on http://127.0.0.1:5173 ..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "==================================================="
echo "    APEX OSINT is now active!"
echo "    Web GUI:   http://127.0.0.1:5173"
echo "    API Docs:  http://127.0.0.1:8000/docs"
echo "==================================================="

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
