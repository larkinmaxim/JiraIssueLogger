@echo off
echo Jira Raw Response Saver
echo =======================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Run the script
echo Running save_jira_responses.py...
echo.
python save_jira_responses.py %*

echo.
pause
