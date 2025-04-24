@echo off
echo Starting Jira Logger in development mode...

REM Check if virtual environment exists, create if not
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

REM Set environment variables
set PYTHONPATH=%CD%

REM Run the application
echo Starting API server...
start cmd /k "python jira_logger\run_api.py"

echo Starting scheduler...
python jira_logger\main.py

REM Deactivate virtual environment when done
call venv\Scripts\deactivate
