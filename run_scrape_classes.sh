#!/bin/bash

# # Define the paths
# VENV_PYTHON="/Users/kyrylobakumenko/miniconda3/envs/class-catch-env/bin/python"
# PROJECT_DIR="/Users/kyrylobakumenko/vscode/class-catch/backend/"
# LOG_FILE="/Users/kyrylobakumenko/vscode/class-catch/backend/logs/scrape_classes.log"

# # Navigate to the project directory
# cd "$PROJECT_DIR"

# # Run the scraping command
# "$VENV_PYTHON" manage.py scrape_classes >> "$LOG_FILE" 2>&1

### DEPLOYED VERSION ###
python manage.py scrape_classes >> logs/scrape_classes.log 2>&1