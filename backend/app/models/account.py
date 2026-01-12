"""
Account model representing financial accounts.
All money flows through accounts (ADR-003: Account-centric design).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Account(Base):
    """
    Financial account belonging to a user.

    Examples: Savings account, checking account, cash wallet, credit card.
    Each account has a currency and tracks an opening balance.
    Current balance is derived from opening_balance + sum(transactions).
    """

    __tablename__ = "accounts"

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

    # Account details
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Currency (ISO 4217 codes: INR, USD, EUR, etc.)
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    # Opening balance in smallest currency unit (ADR-002: Integer-based money)
    # Examples:
    # - ₹1000.00 = 100000 paise
    # - $50.25 = 5025 cents
    opening_balance_minor: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    # Many accounts belong to one user
    user: Mapped["User"] = relationship("User", back_populates="accounts")

    # One account has many transactions
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="account",
        foreign_keys="Transaction.account_id",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # For transfers: transactions where this account is the destination
    incoming_transfers: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="related_account",
        foreign_keys="Transaction.related_account_id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name={self.name}, currency={self.currency})>"
