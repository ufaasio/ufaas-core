import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from apps.base.models import BusinessOwnedEntity, ImmutableBusinessOwnedEntity
from pydantic import BaseModel
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Wallet(BusinessOwnedEntity):
    # currency: Mapped[str] = mapped_column(index=True)
    # balance = Column(Float, default=0.0)

    transactions = relationship("Transaction", back_populates="wallet")
    holds = relationship("WalletHold", back_populates="wallet")
    # participants = relationship("Participant", back_populates="wallet")

    @property
    def balance(self) -> Decimal:
        latest_transaction: Transaction = (
            self.transactions[-1] if self.transactions else None
        )
        return latest_transaction.balance if latest_transaction else Decimal(0)

    @property
    def held_amount(self) -> Decimal:
        return sum(
            hold.amount
            for hold in self.holds
            if hold.status == "active" and hold.expires_at > datetime.now()
        )


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class WalletHold(BusinessOwnedEntity):
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallet.uid"), index=True)
    amount: Mapped[Decimal]
    expires_at: Mapped[datetime] = mapped_column(index=True)
    status: Mapped[StatusEnum] = mapped_column(index=True)
    # status: Mapped[StatusEnum] = mapped_column(SqlEnum(StatusEnum), index=True)

    wallet = relationship("Wallet", back_populates="holds")


class Transaction(ImmutableBusinessOwnedEntity):
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("proposal.uid"), index=True
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallet.uid"), index=True)
    amount: Mapped[Decimal] = mapped_column(onupdate=None)
    currency: Mapped[str] = mapped_column(index=True)
    balance: Mapped[Decimal]
    description: Mapped[str | None]

    wallet = relationship("Wallet", back_populates="transactions")
    # business = relationship("Business", back_populates="transactions")
    proposal = relationship("Proposal", back_populates="transactions")
    notes = relationship("TransactionNote", back_populates="transaction")

    @property
    def note(self) -> Decimal:
        return self.notes[-1].note if self.notes else None


class TransactionNote(BusinessOwnedEntity):
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transaction.uid"), index=True
    )
    note: Mapped[str]
    transaction = relationship("Transaction", back_populates="notes")


class Participant(BaseModel):
    participant_id: uuid.UUID
    amount: Decimal
    wallet_id: uuid.UUID

    # participant_id: Mapped[uuid.UUID] = mapped_column(index=True)
    # amount: Mapped[Decimal]
    # wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallet.uid"), index=True)

    # wallet = relationship("Wallet", back_populates="participants")


class Proposal(BusinessOwnedEntity):
    issuer_id: Mapped[uuid.UUID] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(onupdate=None)
    description: Mapped[str | None]
    note: Mapped[str | None]
    status: Mapped[str | None] = mapped_column(index=True)

    # sources: Mapped[list[Participant]] = mapped_column(JSON)
    # recipients: Mapped[list[Participant]] = mapped_column(JSON)
    participants: Mapped[list[Participant]] = mapped_column(JSON)

    # business = relationship("Business", back_populates="proposals")
    transactions = relationship("Transaction", back_populates="proposal")

    # sources = relationship(
    #     "Participant", secondary="proposal_sources", backref=backref("source_proposals")
    # )
    # recipients = relationship(
    #     "Participant",
    #     secondary="proposal_recipients",
    #     backref=backref("recipient_proposals"),
    # )
