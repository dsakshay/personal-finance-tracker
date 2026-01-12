"""
Global exception handlers for FastAPI.
Converts exceptions to properly formatted JSON responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from jose import JWTError

from app.core.exceptions import FinanceTrackerException


async def finance_exception_handler(
    request: Request,
    exc: FinanceTrackerException,
) -> JSONResponse:
    """
    Handle custom finance tracker exceptions.

    Returns consistent JSON error format:
    {
        "error": "error_type",
        "message": "Human-readable message",
        "details": { ... }  // Optional additional context
    }
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Formats validation errors in a user-friendly way.
    HTTP 422 Unprocessable Entity
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Input validation failed",
            "details": {"errors": errors},
        },
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """
    Handle database integrity constraint violations.

    Examples:
    - Foreign key violation
    - Unique constraint violation
    - NOT NULL violation

    HTTP 409 Conflict (for duplicates) or 400 Bad Request
    """
    error_message = str(exc.orig) if hasattr(exc, "orig") else str(exc)

    # Check for common constraint violations
    if "unique constraint" in error_message.lower():
        status_code = status.HTTP_409_CONFLICT
        message = "Resource already exists"
    elif "foreign key constraint" in error_message.lower():
        status_code = status.HTTP_400_BAD_REQUEST
        message = "Referenced resource does not exist"
    elif "not null constraint" in error_message.lower():
        status_code = status.HTTP_400_BAD_REQUEST
        message = "Required field is missing"
    else:
        status_code = status.HTTP_400_BAD_REQUEST
        message = "Database constraint violation"

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "IntegrityError",
            "message": message,
            "details": {"db_error": error_message},
        },
    )


async def database_error_handler(
    request: Request,
    exc: OperationalError,
) -> JSONResponse:
    """
    Handle database operational errors.

    Examples:
    - Connection lost
    - Timeout
    - Database unavailable

    HTTP 503 Service Unavailable
    """
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "DatabaseError",
            "message": "Database service unavailable",
            "details": {},
        },
    )


async def jwt_error_handler(
    request: Request,
    exc: JWTError,
) -> JSONResponse:
    """
    Handle JWT token errors.

    Examples:
    - Invalid signature
    - Expired token
    - Malformed token

    HTTP 401 Unauthorized
    """
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "AuthenticationError",
            "message": "Invalid or expired authentication token",
            "details": {},
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.

    Logs the error and returns a generic 500 error.
    HTTP 500 Internal Server Error

    Note: In production, this should log to a monitoring service.
    """
    # TODO: Add proper logging here
    print(f"Unexpected error: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {},
        },
    )
