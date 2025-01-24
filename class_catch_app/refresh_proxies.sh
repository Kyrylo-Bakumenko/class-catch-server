#!/bin/bash

VENV_PYTHON="/Users/kyrylobakumenko/miniconda3/envs/class-catch-env/bin/python"
PROJECT_DIR="/Users/kyrylobakumenko/vscode/class-catch/backend/"
LOG_FILE="/Users/kyrylobakumenko/vscode/class-catch/backend/logs/refresh_proxies.log"

cd "$PROJECT_DIR"

"$VENV_PYTHON" manage.py refresh_proxies >> "$LOG_FILE" 2>&1
