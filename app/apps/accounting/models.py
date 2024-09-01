import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from apps.base.models import ImmutableBusinessOwnedEntity
from apps.base_mongo.models import BusinessOwnedEntity
from apps.base_mongo.tasks import TaskMixin
from beanie import BackLink, Link
from pydantic import BaseModel, Field
from server.db import async_session
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column


class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


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

        async with async_session() as session:
            query = select(Transaction).where(*base_query).offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    async def get_balance(self):
        async with async_session() as session:
            query = (
                select(Transaction.balance)
                .where(Transaction.wallet_id == self.uid)
                .order_by(Transaction.created_at.desc())
                .limit(1)
            )
            result = await session.execute(query)
            return result.scalars().one_or_none() or Decimal(0)

    async def get_held_amount(
        self,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ):
        pass

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
        is_deleted: bool = False,
    ):
        base_query = [
            cls.is_deleted == is_deleted,
            cls.user_id == user_id,
            cls.business_name == business_name,
        ]
        if wallet_id:
            base_query.append(cls.wallet_id == wallet_id)
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

        return cls.find(*base_query)

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
        items = await cls.get_holds_query(
            user_id=user_id,
            business_name=business_name,
            wallet_id=wallet_id,
            currency=currency,
            status=status,
            from_date=from_date,
            to_date=to_date,
        ).to_list()

        return items

    @classmethod
    async def list_items(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        is_deleted: bool = False,
        offset: int = 0,
        limit: int = 10,
        *args,
        **kwargs,
    ):
        offset, limit = cls.adjust_pagination(offset, limit)
        query = cls.get_holds_query(
            user_id=user_id,
            business_name=business_name,
            wallet_id=wallet_id,
            currency=currency,
            status=status,
            from_date=from_date,
            to_date=to_date,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )

        items_query = query.sort("-created_at").skip(offset).limit(limit)
        items = await items_query.to_list()
        return items

    @classmethod
    async def total_count(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        is_deleted: bool = False,
        *args,
        **kwargs,
    ):
        query = cls.get_holds_query(
            user_id=user_id,
            business_name=business_name,
            wallet_id=wallet_id,
            currency=currency,
            status=status,
            from_date=from_date,
            to_date=to_date,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )

        return await query.count()

    @classmethod
    async def list_total_combined(
        cls,
        user_id: uuid.UUID,
        business_name: str,
        wallet_id: uuid.UUID,
        currency: str | None = None,
        status: StatusEnum | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        is_deleted: bool = False,
        offset: int = 0,
        limit: int = 10,
        *args,
        **kwargs,
    ) -> tuple[list["WalletHold"], int]:
        offset, limit = cls.adjust_pagination(offset, limit)
        query = cls.get_holds_query(
            user_id=user_id,
            business_name=business_name,
            wallet_id=wallet_id,
            currency=currency,
            status=status,
            from_date=from_date,
            to_date=to_date,
            is_deleted=is_deleted,
            *args,
            **kwargs,
        )
        items_query = query.sort("-created_at").skip(offset).limit(limit)
        items = await items_query.to_list()
        total = await query.count()

        return items, total


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


class Proposal(BusinessOwnedEntity, TaskMixin):
    issuer: Literal["user", "business", "app"] = "business"
    issuer_id: uuid.UUID
    amount: Decimal
    description: str | None
    note: str | None
    status: str | None

    participants: list[Participant]

    async def get_transactions(self):
        async with async_session() as session:
            query = select(Transaction).where(Transaction.proposal_id == self.uid)
            result = await session.execute(query)
            return result.scalars().all()
