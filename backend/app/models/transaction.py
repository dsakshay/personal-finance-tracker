"""
Transaction model representing all financial activity.
Immutable after creation (ADR-005: Transaction immutability).
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, BigInteger, ForeignKey, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TransactionType(str, Enum):
    """Transaction type classification."""

    INCOME = "income"  # Money coming in
    EXPENSE = "expense"  # Money going out
    TRANSFER = "transfer"  # Money moving between accounts


class Transaction(Base):
    """
    Financial transaction belonging to an account and user.

    Represents income, expenses, and transfers.
    Transactions are immutable (ADR-005): corrections use reversal entries.

    Transfer representation (ADR-006):
    - Two linked transactions (one per account)
    - Debit transaction has negative amount_minor
    - Credit transaction has positive amount_minor
    - Both reference each other via related_account_id
    """

    __tablename__ = "transactions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Ownership (multi-user isolation)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Account association
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Amount in smallest currency unit (ADR-002: Integer-based money)
    # Positive = income/credit
    # Negative = expense/debit
    # Examples:
    # - +₹500.00 income = +50000 paise
    # - -$25.50 expense = -2550 cents
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Currency (ISO 4217 codes: INR, USD, EUR, etc.)
    # Must match account currency in most cases
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Transaction classification
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, name="transaction_type_enum", create_type=True),
        nullable=False,
        index=True,
    )

    # Categorization and metadata
    tag: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # Examples: groceries, salary, rent, utilities

    payment_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )  # Examples: cash, card, upi, bank_transfer

    # For transfers: reference to the other account involved
    related_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Optional description
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # When the transaction actually occurred (can differ from created_at)
    transaction_date: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        default=None,
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    # Relationships
    # Many transactions belong to one user
    user: Mapped["User"] = relationship("User", back_populates="transactions")

    # Many transactions belong to one account
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="transactions",
        foreign_keys=[account_id],
    )

    # For transfers: the other account involved
    related_account: Mapped["Account | None"] = relationship(
        "Account",
        back_populates="incoming_transfers",
        foreign_keys=[related_account_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, type={self.transaction_type}, "
            f"amount={self.amount_minor}, currency={self.currency})>"
        )
