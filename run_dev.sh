#!/bin/bash
echo "Starting Jira Logger in development mode..."

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Set environment variables
export PYTHONPATH=$(pwd)

# Run the application
echo "Starting API server..."
python jira_logger/run_api.py &
API_PID=$!

echo "Starting scheduler..."
python jira_logger/main.py

# Clean up when done
kill $API_PID
deactivate
