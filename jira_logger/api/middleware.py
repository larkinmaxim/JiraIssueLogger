"""
API Middleware for Jira Logger

This module defines middleware functions for the FastAPI application,
such as error handling and request/response logging.
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("api.log"), logging.StreamHandler()],
)

logger = logging.getLogger("jira_logger_api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and log information about it.

        Args:
            request (Request): The incoming request
            call_next (callable): The next middleware or route handler

        Returns:
            Response: The response from the next middleware or route handler
        """
        start_time = time.time()

        # Log request details
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Client: {request.client.host if request.client else 'Unknown'}"
        )

        try:
            # Process the request
            response = await call_next(request)

            # Log response details
            process_time = time.time() - start_time
            logger.info(
                f"Response: {response.status_code} "
                f"Process time: {process_time:.4f} seconds"
            )

            return response
        except Exception as e:
            # Log the error
            logger.error(f"Error processing request: {str(e)}")

            # Return a JSON error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "error": str(e)},
            )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling errors.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process the request and handle any errors.

        Args:
            request (Request): The incoming request
            call_next (callable): The next middleware or route handler

        Returns:
            Response: The response from the next middleware or route handler
        """
        try:
            # Process the request
            return await call_next(request)
        except Exception as e:
            # Log the error
            logger.error(f"Unhandled exception: {str(e)}")

            # Return a JSON error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "error": str(e)},
            )


def setup_middleware(app):
    """
    Set up middleware for the FastAPI application.

    Args:
        app: The FastAPI application
    """
    # Add middleware in reverse order (last added is executed first)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
