"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from jose import JWTError

from app.core.config import settings
from app.core.exceptions import FinanceTrackerException
from app.core.error_handlers import (
    finance_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    database_error_handler,
    jwt_error_handler,
    generic_exception_handler,
)
from app.routers import auth, accounts, transactions, summary

app = FastAPI(
    title="Personal Finance Tracker API",
    description="Event-driven personal finance tracker with multi-user support",
    version="0.1.0",
    debug=settings.DEBUG,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(FinanceTrackerException, finance_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(OperationalError, database_error_handler)
app.add_exception_handler(JWTError, jwt_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Personal Finance Tracker API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check for monitoring."""
    return {"status": "healthy"}


# Register routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(summary.router, prefix="/api/v1/summary", tags=["Summaries"])
