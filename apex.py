#!/usr/bin/env python
"""APEX OSINT CLI Entrypoint.

Automatically detects local virtual environment if current python lacks dependencies.
"""

import sys
import os
import subprocess

# Determine workspace root
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, "backend"))

# Ensure dependencies are available; if not, re-execute via venv python
try:
    import sqlalchemy
    import fastapi
except ImportError:
    # Look for virtual environment in ROOT_DIR/venv
    venv_py = os.path.join(ROOT_DIR, "venv", "Scripts", "python.exe")
    if not os.path.exists(venv_py):
        venv_py = os.path.join(ROOT_DIR, "venv", "bin", "python")
    
    if os.path.exists(venv_py) and os.path.abspath(sys.executable) != os.path.abspath(venv_py):
        # Delegate to venv python
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.join(ROOT_DIR, "backend")
        sys.exit(subprocess.call([venv_py] + sys.argv, env=env))
    else:
        print("[APEX ERROR] Missing dependencies. Please run: pip install -r backend/requirements.txt")
        sys.exit(1)

from app.cli.apex_cli import main

if __name__ == "__main__":
    main()
