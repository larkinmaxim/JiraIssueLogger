"""
Run script for the Jira Logger FastAPI application.

This script provides a convenient way to start the FastAPI server.
"""

import uvicorn

if __name__ == "__main__":
    print("Starting Jira Logger API server...")
    print("API documentation will be available at http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
