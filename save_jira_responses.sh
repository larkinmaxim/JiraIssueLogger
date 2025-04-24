#!/bin/bash

echo "Jira Raw Response Saver"
echo "======================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Python is not installed or not in PATH."
        echo "Please install Python and try again."
        read -p "Press Enter to continue..."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Run the script
echo "Running save_jira_responses.py..."
echo
$PYTHON_CMD save_jira_responses.py "$@"

echo
read -p "Press Enter to continue..."
