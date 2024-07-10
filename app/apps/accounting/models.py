import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.base.models import BaseEntity, BusinessOwnedEntity


class Wallet(BusinessOwnedEntity):
    currency: Mapped[str] = mapped_column(index=True)
    # balance = Column(Float, default=0.0)

    transactions = relationship("Transaction", back_populates="wallet")
    holds = relationship("WalletHold", back_populates="wallet")
    participants = relationship("Participant", back_populates="wallet")


class WalletHold(BaseEntity):
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallet.uid"), index=True)
    amount: Mapped[Decimal]
    expires_at: Mapped[datetime] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(index=True)

    wallet = relationship("Wallet", back_populates="holds")


class Transaction(BusinessOwnedEntity):
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallet.uid"), index=True)
    amount: Mapped[Decimal] = mapped_column(onupdate=None)
    balance: Mapped[Decimal]
    description: Mapped[str | None]
    note: Mapped[str | None]

    wallet = relationship("Wallet", back_populates="transactions")
    business = relationship("Business", back_populates="transactions")


class Participant(BaseModel):
    participant_id: uuid.UUID
    amount: Decimal
    wallet_id: uuid.UUID

    # participant_id: Mapped[uuid.UUID] = mapped_column(index=True)
    # amount: Mapped[Decimal]
    # wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallet.uid"), index=True)

    # wallet = relationship("Wallet", back_populates="participants")


class Proposal(BaseEntity):
    issuer_id: Mapped[uuid.UUID] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(onupdate=None)
    description: Mapped[str | None]
    note: Mapped[str | None]
    status: Mapped[str | None] = mapped_column(index=True)

    sources: Mapped[list[Participant]] = mapped_column(JSON)
    recipients: Mapped[list[Participant]] = mapped_column(JSON)

    application = relationship("Application", back_populates="proposals")
    business = relationship("Business", back_populates="proposals")
    # sources = relationship(
    #     "Participant", secondary="proposal_sources", backref=backref("source_proposals")
    # )
    # recipients = relationship(
    #     "Participant",
    #     secondary="proposal_recipients",
    #     backref=backref("recipient_proposals"),
    # )
