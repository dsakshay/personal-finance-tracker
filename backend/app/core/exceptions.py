"""
Custom exception classes for the finance tracker.
Provides clear error messages and proper HTTP status codes.
"""

from typing import Any, Dict, Optional


class FinanceTrackerException(Exception):
    """
    Base exception for all finance tracker errors.

    All custom exceptions inherit from this class.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# ============================================================================
# Authentication & Authorization Errors (401, 403, 404)
# ============================================================================


class UnauthorizedException(FinanceTrackerException):
    """
    User is not authenticated or token is invalid.
    HTTP 401 Unauthorized
    """

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(FinanceTrackerException):
    """
    User is authenticated but doesn't have permission.
    HTTP 403 Forbidden

    Example: Trying to access another user's account.
    """

    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, status_code=403)


class NotFoundException(FinanceTrackerException):
    """
    Resource not found or user doesn't have access to it.
    HTTP 404 Not Found

    Note: We use 404 for "not found OR no access" to prevent user enumeration.
    """

    def __init__(self, resource: str = "Resource"):
        super().__init__(message=f"{resource} not found", status_code=404)


# ============================================================================
# Validation Errors (400, 422)
# ============================================================================


class ValidationException(FinanceTrackerException):
    """
    Input validation failed.
    HTTP 400 Bad Request

    Examples: Invalid email format, negative amount, etc.
    """

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message=message, status_code=400, details=details)


class CurrencyMismatchException(FinanceTrackerException):
    """
    Currency codes don't match where they should.
    HTTP 400 Bad Request

    Example: Transferring INR to USD account.
    """

    def __init__(
        self,
        expected: str,
        received: str,
        context: str = "operation",
    ):
        message = (
            f"Currency mismatch in {context}. "
            f"Expected {expected}, but received {received}"
        )
        super().__init__(
            message=message,
            status_code=400,
            details={
                "expected_currency": expected,
                "received_currency": received,
                "context": context,
            },
        )


class InvalidAmountException(FinanceTrackerException):
    """
    Amount validation failed.
    HTTP 400 Bad Request

    Examples: Zero amount, negative amount when positive required, etc.
    """

    def __init__(self, message: str, amount: Optional[float] = None):
        details = {"amount": amount} if amount is not None else {}
        super().__init__(message=message, status_code=400, details=details)


class InvalidDateException(FinanceTrackerException):
    """
    Date validation failed.
    HTTP 400 Bad Request

    Example: Transaction date in the future.
    """

    def __init__(self, message: str, date_value: Optional[str] = None):
        details = {"date": date_value} if date_value else {}
        super().__init__(message=message, status_code=400, details=details)


# ============================================================================
# Business Logic Errors (400, 409)
# ============================================================================


class DuplicateResourceException(FinanceTrackerException):
    """
    Resource already exists (e.g., email already registered).
    HTTP 409 Conflict
    """

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} already exists: {identifier}"
        super().__init__(
            message=message,
            status_code=409,
            details={"resource": resource, "identifier": identifier},
        )


class InvalidTransferException(FinanceTrackerException):
    """
    Transfer operation is invalid.
    HTTP 400 Bad Request

    Examples:
    - Same source and destination account
    - Accounts belong to different users
    - Currency mismatch
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=400, details=details or {})


class AccountOwnershipException(FinanceTrackerException):
    """
    Accounts involved in operation don't all belong to the same user.
    HTTP 403 Forbidden

    Example: Trying to transfer between your account and someone else's.
    """

    def __init__(self, message: str = "All accounts must belong to the same user"):
        super().__init__(message=message, status_code=403)


class InsufficientBalanceException(FinanceTrackerException):
    """
    Account doesn't have enough balance for the operation.
    HTTP 400 Bad Request

    Note: This is for future use (not enforced in MVP).
    """

    def __init__(
        self,
        account_name: str,
        required: float,
        available: float,
    ):
        message = (
            f"Insufficient balance in {account_name}. "
            f"Required: ₹{required:.2f}, Available: ₹{available:.2f}"
        )
        super().__init__(
            message=message,
            status_code=400,
            details={
                "account": account_name,
                "required": required,
                "available": available,
            },
        )


# ============================================================================
# System Errors (500, 503)
# ============================================================================


class DatabaseException(FinanceTrackerException):
    """
    Database operation failed.
    HTTP 500 Internal Server Error
    """

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message=message, status_code=500)


class ExternalServiceException(FinanceTrackerException):
    """
    External service (e.g., payment gateway) unavailable.
    HTTP 503 Service Unavailable

    Note: For future use when integrating external services.
    """

    def __init__(self, service: str, message: str = "Service unavailable"):
        super().__init__(
            message=f"{service}: {message}",
            status_code=503,
            details={"service": service},
        )
