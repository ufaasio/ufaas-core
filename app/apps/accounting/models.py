import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from apps.base.models import ImmutableBusinessOwnedEntity
from apps.base_mongo.models import BusinessOwnedEntity
from beanie import BackLink, Link
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from server.db import get_db_session
from sqlalchemy.orm import Mapped, mapped_column


class Wallet(BusinessOwnedEntity):
    holds: BackLink["WalletHold"] = Field(original_field="wallet")

    async def get_transactions(
        self,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
    ):
        base_query = [Transaction.wallet_id == self.uid]
        if to_date is None:
            to_date = datetime.now()
        if from_date and to_date:
            base_query.append(Transaction.created_at >= from_date)
            base_query.append(Transaction.created_at <= to_date)

        # session = await get_db_session()
        async with AsyncSession() as session:
            query = select(Transaction).where(*base_query).offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_balance(self):
        # session = await get_db_session()
        async with AsyncSession() as session:
            query = (
                select(Transaction.balance)
                .where(Transaction.wallet_id == self.uid)
                .order_by(Transaction.created_at.desc())
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_held_amount(
        self,
        currency: str | None = None,
        status: "StatusEnum" | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        pass

    @classmethod
    async def list_items(
        cls,
        user_id: uuid.UUID = None,
        business_name: str = None,
        offset: int = 0,
        limit: int = 10,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ):
        items = await cls.find(
            cls.user_id == user_id,
            cls.business_name == business_name,
            cls.is_deleted == False,
        ).offset(offset).limit(limit).to_list()

        return items

    # transactions = relationship("Transaction", back_populates="wallet")
    # holds = relationship("WalletHold", back_populates="wallet")

    # @property
    # def balance(self) -> Decimal:
    #     latest_transaction: Transaction = (
    #         self.transactions[-1] if self.transactions else None
    #     )
    #     return latest_transaction.balance if latest_transaction else Decimal(0)

    # @property
    # def held_amount(self) -> Decimal:
    #     return sum(
    #         hold.amount
    #         for hold in self.holds
    #         if hold.status == "active" and hold.expires_at > datetime.now()
    #     )


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class WalletHold(BusinessOwnedEntity):
    wallet_id: uuid.UUID
    amount: Decimal
    expires_at: datetime
    status: StatusEnum
    currency: str
    description: str | None
    wallet: Link[Wallet]

    @classmethod
    def get_holds_query(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        base_query = [
            cls.is_deleted == False,
            cls.user_id == user_id,
            cls.business_name == business_name,
            cls.wallet_id == wallet_id,
        ]
        if currency:
            base_query.append(cls.currency == currency)

        if status:
            base_query.append(cls.status == status)

        if to_date is None:
            to_date = datetime.now()
        if from_date and to_date:
            base_query.append(cls.created_at >= from_date)
            base_query.append(cls.created_at <= to_date)
        else:
            base_query.append(cls.expires_at > datetime.now())

        return base_query

    @classmethod
    async def get_holds(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        items = await cls.find(
            *cls.get_holds_query(
                user_id=user_id,
                business_name=business_name,
                wallet_id=wallet_id,
                currency=currency,
                status=status,
                from_date=from_date,
                to_date=to_date,
            )
        ).to_list()

        return items


class Transaction(ImmutableBusinessOwnedEntity):
    proposal_id: Mapped[uuid.UUID] = mapped_column(index=True)
    wallet_id: Mapped[uuid.UUID] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(onupdate=None)
    currency: Mapped[str] = mapped_column(index=True)
    balance: Mapped[Decimal]
    description: Mapped[str | None]

    async def note(self) -> str:
        query = TransactionNote.find(TransactionNote.transaction_id == self.uid).sort(
            "-created_at"
        )
        note = await query.to_list()
        return note[0].note if note else None


class TransactionNote(BusinessOwnedEntity):
    transaction_id: uuid.UUID
    note: str


class Participant(BaseModel):
    participant_id: uuid.UUID
    amount: Decimal
    wallet_id: uuid.UUID


class Proposal(BusinessOwnedEntity):
    issuer_id: uuid.UUID
    amount: Decimal
    description: str | None
    note: str | None
    status: str | None

    participants: list[Participant]

    async def get_transactions(self):
        # session = await get_db_session()
        async with AsyncSession() as session:
            query = select(Transaction).where(Transaction.proposal_id == self.uid)
            result = await session.execute(query)
            return result.scalars().all()
